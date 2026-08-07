"""Tests de las estadísticas persistentes. No requieren Flet."""

import pytest

from makai.ui.estadisticas import CLAVE, Estadisticas, cargar, guardar


class AlmacenamientoStub:
    def __init__(self, datos=None):
        self.datos = dict(datos or {})

    def get(self, clave):
        return self.datos.get(clave)

    def set(self, clave, valor):
        self.datos[clave] = valor
        return True


class AlmacenamientoRoto:
    def get(self, clave):
        raise RuntimeError("sin almacenamiento")

    def set(self, clave, valor):
        raise RuntimeError("sin almacenamiento")


# --- Contadores ---------------------------------------------------------------


def test_arranca_todo_en_cero():
    e = Estadisticas()
    assert e.partidas_jugadas == e.rondas_ganadas == e.mejor_racha == 0
    assert e.porcentaje_rondas == 0.0


def test_registrar_rondas_cuenta_jugadas_y_ganadas():
    e = Estadisticas()
    e.registrar_ronda(gano=True, fichas_jugador=105)
    e.registrar_ronda(gano=False, fichas_jugador=95)
    e.registrar_ronda(gano=True, fichas_jugador=110)

    assert e.rondas_jugadas == 3
    assert e.rondas_ganadas == 2


def test_el_porcentaje_de_rondas():
    e = Estadisticas(rondas_jugadas=8, rondas_ganadas=2)
    assert e.porcentaje_rondas == 25.0


def test_la_racha_crece_con_victorias_seguidas():
    e = Estadisticas()
    for _ in range(4):
        e.registrar_ronda(gano=True, fichas_jugador=100)
    assert e.racha_actual == 4
    assert e.mejor_racha == 4


def test_perder_corta_la_racha_pero_no_el_record():
    e = Estadisticas()
    for _ in range(3):
        e.registrar_ronda(gano=True, fichas_jugador=100)
    e.registrar_ronda(gano=False, fichas_jugador=90)

    assert e.racha_actual == 0
    assert e.mejor_racha == 3


def test_una_racha_menor_no_pisa_el_record():
    e = Estadisticas()
    for _ in range(5):
        e.registrar_ronda(gano=True, fichas_jugador=100)
    e.registrar_ronda(gano=False, fichas_jugador=90)
    e.registrar_ronda(gano=True, fichas_jugador=95)

    assert e.racha_actual == 1
    assert e.mejor_racha == 5


def test_las_fichas_maximas_son_el_pico_historico():
    e = Estadisticas()
    for fichas in (120, 180, 90, 140):
        e.registrar_ronda(gano=True, fichas_jugador=fichas)
    assert e.fichas_maximas == 180


def test_registrar_partidas():
    e = Estadisticas()
    e.registrar_partida(gano=True)
    e.registrar_partida(gano=False)
    e.registrar_partida(gano=False)

    assert e.partidas_jugadas == 3
    assert e.partidas_ganadas == 1
    assert e.partidas_perdidas == 2


# --- Persistencia -------------------------------------------------------------


def test_guardar_y_cargar_conserva_todo():
    almacen = AlmacenamientoStub()
    original = Estadisticas(
        partidas_jugadas=7,
        partidas_ganadas=3,
        rondas_jugadas=91,
        rondas_ganadas=44,
        racha_actual=2,
        mejor_racha=9,
        fichas_maximas=260,
    )
    guardar(almacen, original)
    assert cargar(almacen) == original


def test_sin_nada_guardado_devuelve_ceros():
    assert cargar(AlmacenamientoStub()) == Estadisticas()


def test_un_almacenamiento_roto_no_tumba_el_juego():
    assert cargar(AlmacenamientoRoto()) == Estadisticas()
    guardar(AlmacenamientoRoto(), Estadisticas())  # no debe lanzar


@pytest.mark.parametrize("basura", ["texto", 42, [], None])
def test_datos_corruptos_devuelven_ceros(basura):
    assert cargar(AlmacenamientoStub({CLAVE: basura})) == Estadisticas()


def test_se_ignoran_campos_de_versiones_viejas():
    """Que un campo eliminado no rompa la carga."""
    almacen = AlmacenamientoStub({CLAVE: {"rondas_ganadas": 5, "puntos_totales": 999}})
    e = cargar(almacen)
    assert e.rondas_ganadas == 5
    assert not hasattr(e, "puntos_totales")


def test_se_ignoran_valores_del_tipo_equivocado():
    almacen = AlmacenamientoStub({CLAVE: {"rondas_ganadas": "muchas", "mejor_racha": 4}})
    e = cargar(almacen)
    assert e.rondas_ganadas == 0
    assert e.mejor_racha == 4


def test_los_campos_faltantes_quedan_en_cero():
    almacen = AlmacenamientoStub({CLAVE: {"partidas_jugadas": 2}})
    e = cargar(almacen)
    assert e.partidas_jugadas == 2
    assert e.rondas_jugadas == 0
