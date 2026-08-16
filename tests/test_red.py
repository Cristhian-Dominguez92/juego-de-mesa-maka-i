"""Tests de las salas de partida en red. No requieren Flet."""

import asyncio

import pytest

from makai.core import Rol
from makai.ui import red


async def _noop() -> None:
    pass


@pytest.fixture(autouse=True)
def limpiar_registro():
    """Cada sala creada en un test no debe filtrarse al siguiente."""
    yield
    red._SALAS.clear()
    red._intentos_fallidos.clear()


# --- Crear y unirse -------------------------------------------------------


def test_crear_sala_la_deja_disponible_por_su_codigo():
    sala = red.crear_sala()
    assert red.unirse(sala.codigo) is sala


def test_dos_salas_no_repiten_codigo():
    a = red.crear_sala()
    b = red.crear_sala()
    assert a.codigo != b.codigo


def test_unirse_no_distingue_mayusculas_ni_espacios():
    sala = red.crear_sala()
    assert red.unirse(f"  {sala.codigo.lower()}  ") is sala


def test_unirse_con_codigo_inexistente_falla():
    with pytest.raises(red.SalaInexistente):
        red.unirse("ZZZZ")


def test_unirse_con_el_asiento_del_invitado_ocupado_falla():
    sala = red.crear_sala()
    sala.marcar_conectado(Rol.PC, notificar=_noop)
    with pytest.raises(red.SalaLlena):
        red.unirse(sala.codigo)


def test_cerrar_sala_la_saca_del_registro():
    sala = red.crear_sala()
    red.cerrar_sala(sala.codigo)
    with pytest.raises(red.SalaInexistente):
        red.unirse(sala.codigo)


def test_cerrar_sala_inexistente_no_falla():
    red.cerrar_sala("ZZZZ")


# --- Conexión y aviso entre asientos ---------------------------------------


def test_sala_no_esta_completa_con_un_solo_asiento():
    sala = red.crear_sala()
    sala.marcar_conectado(Rol.JUGADOR, notificar=_noop)
    assert not sala.completa


def test_sala_completa_cuando_se_conectan_los_dos_asientos():
    sala = red.crear_sala()
    sala.marcar_conectado(Rol.JUGADOR, notificar=_noop)
    sala.marcar_conectado(Rol.PC, notificar=_noop)
    assert sala.completa


def test_avisar_al_otro_dispara_el_callback_del_asiento_contrario():
    avisos = []

    async def anotar_jugador():
        avisos.append("jugador")

    async def anotar_pc():
        avisos.append("pc")

    sala = red.crear_sala()
    sala.marcar_conectado(Rol.JUGADOR, notificar=anotar_jugador)
    sala.marcar_conectado(Rol.PC, notificar=anotar_pc)

    asyncio.run(sala.avisar_al_otro(Rol.JUGADOR))
    assert avisos == ["pc"]

    asyncio.run(sala.avisar_al_otro(Rol.PC))
    assert avisos == ["pc", "jugador"]


def test_avisar_al_otro_sin_nadie_conectado_no_falla():
    sala = red.crear_sala()
    asyncio.run(sala.avisar_al_otro(Rol.JUGADOR))


def test_desconectar_libera_el_asiento():
    sala = red.crear_sala()
    sala.marcar_conectado(Rol.PC, notificar=_noop)
    sala.desconectar(Rol.PC)
    assert not sala.conectado(Rol.PC)
    assert red.unirse(sala.codigo) is sala


def test_desconectar_un_asiento_libre_no_falla():
    sala = red.crear_sala()
    sala.desconectar(Rol.PC)


# --- Límite de intentos fallidos ---------------------------------------------


def test_unirse_sin_identificador_no_tiene_limite():
    for _ in range(red.INTENTOS_MAXIMOS + 5):
        with pytest.raises(red.SalaInexistente):
            red.unirse("ZZZZZZ")


def test_unirse_bloquea_tras_demasiados_intentos_fallidos():
    for _ in range(red.INTENTOS_MAXIMOS):
        with pytest.raises(red.SalaInexistente):
            red.unirse("ZZZZZZ", identificador="1.2.3.4")
    with pytest.raises(red.DemasiadosIntentos):
        red.unirse("ZZZZZZ", identificador="1.2.3.4")


def test_una_sala_llena_no_cuenta_como_intento_fallido():
    sala = red.crear_sala()
    sala.marcar_conectado(Rol.PC, notificar=_noop)
    for _ in range(red.INTENTOS_MAXIMOS + 3):
        with pytest.raises(red.SalaLlena):
            red.unirse(sala.codigo, identificador="1.2.3.4")


def test_el_limite_es_por_identificador():
    for _ in range(red.INTENTOS_MAXIMOS):
        with pytest.raises(red.SalaInexistente):
            red.unirse("ZZZZZZ", identificador="1.1.1.1")
    # A otro identificador todavia le quedan intentos.
    with pytest.raises(red.SalaInexistente):
        red.unirse("ZZZZZZ", identificador="2.2.2.2")


def test_el_bloqueo_se_libera_pasada_la_ventana(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(red.time, "monotonic", lambda: reloj[0])

    for _ in range(red.INTENTOS_MAXIMOS):
        with pytest.raises(red.SalaInexistente):
            red.unirse("ZZZZZZ", identificador="1.2.3.4")
    with pytest.raises(red.DemasiadosIntentos):
        red.unirse("ZZZZZZ", identificador="1.2.3.4")

    reloj[0] += red.VENTANA_INTENTOS_SEGUNDOS + 1
    with pytest.raises(red.SalaInexistente):
        red.unirse("ZZZZZZ", identificador="1.2.3.4")


# --- Expiración de salas abandonadas -----------------------------------------


def test_una_sala_reciente_no_esta_vencida():
    sala = red.crear_sala()
    assert not sala.vencida


def test_una_sala_sin_actividad_mucho_tiempo_esta_vencida(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(red.time, "monotonic", lambda: reloj[0])

    sala = red.crear_sala()
    reloj[0] += red.TIEMPO_EXPIRACION_SEGUNDOS + 1
    assert sala.vencida


def test_avisar_al_otro_renueva_la_actividad(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(red.time, "monotonic", lambda: reloj[0])

    sala = red.crear_sala()
    sala.marcar_conectado(Rol.JUGADOR, notificar=_noop)
    sala.marcar_conectado(Rol.PC, notificar=_noop)

    reloj[0] += red.TIEMPO_EXPIRACION_SEGUNDOS - 1
    asyncio.run(sala.avisar_al_otro(Rol.JUGADOR))

    reloj[0] += red.TIEMPO_EXPIRACION_SEGUNDOS - 1
    assert not sala.vencida, "la actividad reciente deberia haber renovado el plazo"


def test_crear_sala_purga_las_vencidas(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(red.time, "monotonic", lambda: reloj[0])

    vieja = red.crear_sala()
    reloj[0] += red.TIEMPO_EXPIRACION_SEGUNDOS + 1

    red.crear_sala()  # dispara la purga

    with pytest.raises(red.SalaInexistente):
        red.unirse(vieja.codigo)


def test_crear_sala_no_purga_una_sala_activa(monkeypatch):
    reloj = [0.0]
    monkeypatch.setattr(red.time, "monotonic", lambda: reloj[0])

    activa = red.crear_sala()
    reloj[0] += red.TIEMPO_EXPIRACION_SEGUNDOS - 1

    red.crear_sala()

    assert red.unirse(activa.codigo) is activa
