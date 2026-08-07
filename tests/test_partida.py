import random

import pytest

from makai.core.cartas import Carta, Palo
from makai.core.estrategia import Contexto, estrategia_umbral
from makai.core.partida import (
    APUESTA_MINIMA,
    CARTAS_INICIALES,
    ApuestaInvalida,
    Estado,
    EstadoInvalido,
    Partida,
)
from makai.core.reglas import MAX_CARTAS_POR_MANO, Resultado, Rol


def nueva_partida(semilla=0, **kwargs):
    return Partida(rng=random.Random(semilla), **kwargs)


def jugar_ronda(partida, pedir=0):
    """Juega una ronda completa: reparte, pide N veces, se planta y resuelve."""
    partida.repartir()
    for _ in range(pedir):
        partida.pedir()
    partida.plantarse()
    while partida.pc_debe_pedir():
        partida.pc_pide()
    return partida.resolver_ronda()


def jugar_partida(partida, limite=5000):
    """Juega hasta que alguien se quede sin fichas."""
    rondas = 0
    while partida.estado is not Estado.PARTIDA_TERMINADA:
        resultado = jugar_ronda(partida)
        rondas += 1
        assert rondas < limite, "la partida no converge"
        if not resultado.partida_terminada:
            partida.nueva_ronda()
    return rondas


# --- Reparto ------------------------------------------------------------------


def test_al_repartir_cada_mano_recibe_dos_cartas():
    p = nueva_partida()
    p.repartir()
    assert len(p.mano_jugador) == len(p.mano_pc) == CARTAS_INICIALES
    assert p.estado is Estado.TURNO_JUGADOR


def test_el_reparto_no_repite_cartas():
    p = nueva_partida()
    p.repartir()
    repartidas = p.mano_jugador + p.mano_pc
    assert len(set(repartidas)) == len(repartidas)


def test_no_se_puede_repartir_dos_veces_seguidas():
    p = nueva_partida()
    p.repartir()
    with pytest.raises(EstadoInvalido):
        p.repartir()


# --- Turno del jugador --------------------------------------------------------


def test_el_jugador_puede_pedir_una_tercera_carta():
    p = nueva_partida()
    p.repartir()
    p.pedir()
    assert len(p.mano_jugador) == MAX_CARTAS_POR_MANO


def test_el_jugador_no_puede_pasar_de_tres_cartas():
    p = nueva_partida()
    p.repartir()
    p.pedir()
    assert not p.jugador_puede_pedir
    with pytest.raises(EstadoInvalido):
        p.pedir()


def test_no_se_puede_pedir_antes_de_repartir():
    p = nueva_partida()
    with pytest.raises(EstadoInvalido):
        p.pedir()


def test_no_se_puede_pedir_despues_de_plantarse():
    p = nueva_partida()
    p.repartir()
    p.plantarse()
    with pytest.raises(EstadoInvalido):
        p.pedir()


# --- Turno de la PC -----------------------------------------------------------


def test_la_pc_no_juega_durante_el_turno_del_jugador():
    p = nueva_partida()
    p.repartir()
    assert not p.pc_debe_pedir()


def test_la_pc_nunca_supera_tres_cartas():
    for semilla in range(30):
        p = nueva_partida(semilla)
        jugar_ronda(p)
        assert len(p.mano_pc) <= MAX_CARTAS_POR_MANO


def test_pc_pide_falla_si_ya_se_planto():
    p = nueva_partida()
    p.repartir()
    p.plantarse()
    while p.pc_debe_pedir():
        p.pc_pide()
    with pytest.raises(EstadoInvalido):
        p.pc_pide()


def test_se_puede_inyectar_otra_estrategia():
    p = nueva_partida(estrategia_pc=lambda contexto: False)
    p.repartir()
    p.plantarse()
    assert not p.pc_debe_pedir()
    assert len(p.mano_pc) == CARTAS_INICIALES


def test_la_estrategia_recibe_las_dos_manos_y_el_rol():
    vistos = []

    def espia(contexto: Contexto) -> bool:
        vistos.append(contexto)
        return False

    p = nueva_partida(banca_inicial=Rol.PC, estrategia_pc=espia)
    p.repartir()
    p.plantarse()
    p.pc_debe_pedir()

    assert vistos, "no se consulto la estrategia"
    contexto = vistos[0]
    assert contexto.mano == tuple(p.mano_pc)
    assert contexto.mano_rival == tuple(p.mano_jugador)
    assert contexto.es_banca is True


def test_la_estrategia_sabe_cuando_la_pc_no_es_banca():
    vistos = []

    def espia(contexto: Contexto) -> bool:
        vistos.append(contexto)
        return False

    p = nueva_partida(banca_inicial=Rol.JUGADOR, estrategia_pc=espia)
    p.repartir()
    p.plantarse()
    p.pc_debe_pedir()

    assert vistos[0].es_banca is False


@pytest.mark.parametrize(
    ("valores", "deberia_pedir"),
    [
        ((1, 2), True),  # 3 < 6
        ((1, 4), True),  # 5 < 6
        ((1, 5), False),  # 6, alcanza el umbral
        ((4, 5), False),  # 9
        ((7, 3), True),  # 10 -> 0
        ((1, 2, 3), False),  # ya tiene tres cartas
    ],
)
def test_estrategia_umbral(valores, deberia_pedir):
    contexto = Contexto(
        mano=tuple(Carta(Palo.OROS, v) for v in valores),
        mano_rival=(),
        es_banca=False,
    )
    assert estrategia_umbral(contexto) is deberia_pedir


# --- Apuestas -----------------------------------------------------------------


def test_ambos_arrancan_con_las_mismas_fichas():
    p = nueva_partida(fichas_iniciales=50)
    assert p.fichas_jugador == p.fichas_pc == 50


def test_se_puede_cambiar_la_apuesta_antes_de_repartir():
    p = nueva_partida()
    p.apostar(20)
    assert p.apuesta == 20


def test_no_se_puede_apostar_despues_de_repartir():
    p = nueva_partida()
    p.repartir()
    with pytest.raises(EstadoInvalido):
        p.apostar(10)


def test_no_se_puede_apostar_menos_del_minimo():
    p = nueva_partida()
    with pytest.raises(ApuestaInvalida):
        p.apostar(APUESTA_MINIMA - 1)


def test_no_se_puede_apostar_mas_de_lo_que_el_rival_puede_pagar():
    p = nueva_partida(fichas_iniciales=30)
    assert p.apuesta_maxima == 30
    with pytest.raises(ApuestaInvalida):
        p.apostar(31)


def test_el_ganador_se_lleva_la_apuesta():
    p = nueva_partida(fichas_iniciales=100)
    p.apostar(25)
    r = jugar_ronda(p)

    if r.ganador is Rol.JUGADOR:
        assert (r.fichas_jugador, r.fichas_pc) == (125, 75)
    else:
        assert (r.fichas_jugador, r.fichas_pc) == (75, 125)


def test_el_total_de_fichas_se_conserva():
    p = nueva_partida(fichas_iniciales=100)
    for _ in range(15):
        r = jugar_ronda(p)
        assert r.fichas_jugador + r.fichas_pc == 200
        if r.partida_terminada:
            break
        p.nueva_ronda()


def test_la_apuesta_se_recorta_si_ya_no_alcanza():
    """Tras perder fichas, la apuesta anterior puede quedar fuera de rango."""
    # Apostando 6 de 10, el perdedor queda con 4: la apuesta ya no entra.
    p = nueva_partida(fichas_iniciales=10)
    p.apostar(6)
    r = jugar_ronda(p)
    assert not r.partida_terminada

    p.nueva_ronda()
    assert p.apuesta_maxima == 4
    assert p.apuesta == 4, "la apuesta deberia haberse recortado al maximo jugable"


def test_el_maximo_apostable_es_el_del_lado_mas_pobre():
    p = nueva_partida(fichas_iniciales=100)
    p.fichas[Rol.PC] = 7
    assert p.apuesta_maxima == 7


def test_no_se_puede_crear_una_partida_sin_fichas():
    with pytest.raises(ValueError):
        Partida(fichas_iniciales=0)


# --- Rotación de la banca -----------------------------------------------------


def test_la_banca_inicial_es_configurable():
    assert nueva_partida(banca_inicial=Rol.JUGADOR).banca is Rol.JUGADOR
    assert nueva_partida(banca_inicial=Rol.PC).banca is Rol.PC


def test_la_banca_pasa_al_ganador_de_la_ronda():
    p = nueva_partida()
    r = jugar_ronda(p)
    assert p.banca is r.ganador
    assert r.banca_siguiente is r.ganador


def test_el_resultado_informa_quien_era_banca_antes():
    p = nueva_partida(banca_inicial=Rol.PC)
    r = jugar_ronda(p)
    assert r.banca is Rol.PC


def test_el_empate_lo_gana_la_banca_y_la_conserva():
    p = nueva_partida(banca_inicial=Rol.JUGADOR)
    p.repartir()
    p.mano_jugador = [Carta(Palo.OROS, 4), Carta(Palo.COPAS, 5)]
    p.mano_pc = [Carta(Palo.ESPADAS, 7), Carta(Palo.BASTOS, 2)]
    p.plantarse()
    r = p.resolver_ronda()

    assert r.resultado is Resultado.EMPATE
    assert r.ganador is Rol.JUGADOR
    assert p.banca is Rol.JUGADOR


def test_la_banca_rota_a_lo_largo_de_una_partida():
    """Con la banca rotando, el rol no puede quedarse fijo indefinidamente."""
    p = nueva_partida(7, fichas_iniciales=200)
    bancas = set()
    for _ in range(40):
        r = jugar_ronda(p)
        bancas.add(p.banca)
        if r.partida_terminada:
            break
        p.nueva_ronda()
    assert bancas == {Rol.JUGADOR, Rol.PC}, "la banca nunca cambio de lado"


# --- Fin de partida -----------------------------------------------------------


def test_la_partida_termina_cuando_alguien_se_queda_sin_fichas():
    p = nueva_partida(fichas_iniciales=10)
    p.apostar(10)
    r = jugar_ronda(p)
    assert r.partida_terminada
    assert p.estado is Estado.PARTIDA_TERMINADA
    assert min(r.fichas_jugador, r.fichas_pc) == 0


def test_gano_el_jugador_solo_si_le_quedan_fichas():
    p = nueva_partida(fichas_iniciales=10)
    p.apostar(10)
    r = jugar_ronda(p)
    assert r.gano_el_jugador is (r.fichas_jugador > 0)


def test_la_partida_sigue_mientras_ambos_tengan_fichas():
    p = nueva_partida(fichas_iniciales=100)
    p.apostar(1)
    r = jugar_ronda(p)
    assert not r.partida_terminada
    assert p.estado is Estado.RONDA_TERMINADA


def test_no_se_puede_seguir_jugando_una_partida_terminada():
    p = nueva_partida(fichas_iniciales=10)
    p.apostar(10)
    jugar_ronda(p)
    with pytest.raises(EstadoInvalido):
        p.nueva_ronda()


def test_reiniciar_devuelve_las_fichas_y_la_banca_inicial():
    p = nueva_partida(fichas_iniciales=10, banca_inicial=Rol.PC)
    p.apostar(10)
    jugar_ronda(p)
    p.reiniciar()
    assert p.fichas_jugador == p.fichas_pc == 10
    assert p.banca is Rol.PC
    assert p.estado is Estado.ESPERANDO_REPARTO
    assert p.mano_jugador == p.mano_pc == []


def test_toda_partida_termina_con_un_solo_ganador():
    for semilla in range(15):
        p = nueva_partida(semilla, fichas_iniciales=40)
        jugar_partida(p)
        assert min(p.fichas_jugador, p.fichas_pc) == 0
        assert max(p.fichas_jugador, p.fichas_pc) == 80


# --- Determinismo -------------------------------------------------------------


def test_la_misma_semilla_reproduce_la_misma_partida():
    a, b = nueva_partida(99), nueva_partida(99)
    ra, rb = jugar_ronda(a), jugar_ronda(b)
    assert a.mano_jugador == b.mano_jugador
    assert a.mano_pc == b.mano_pc
    assert ra == rb
