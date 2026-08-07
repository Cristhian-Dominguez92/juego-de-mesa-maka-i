import itertools

import pytest

from makai.core.cartas import VALORES, Carta, Palo, crear_mazo
from makai.core.reglas import (
    PUNTAJE_TRES_FIGURAS,
    Resultado,
    calcular_puntaje,
    es_tres_figuras,
    resolver,
    suma_punto_el_jugador,
)


def mano(*valores):
    """Construye una mano. El palo es irrelevante para el puntaje."""
    palos = itertools.cycle(Palo)
    return [Carta(next(palos), v) for v in valores]


# --- Puntaje ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("valores", "esperado"),
    [
        ((1, 2), 3),
        ((4, 5), 9),
        ((1, 1), 2),
        ((7, 3), 0),  # 10 -> solo cuenta el ultimo digito
        ((7, 7), 4),  # 14 -> 4
        ((10, 5), 5),  # figura vale 10 -> 15 -> 5
        ((12, 11), 0),  # 20 -> 0
        ((7, 7, 7), 1),  # 21 -> 1
        ((10, 11, 1), 1),  # 21 -> 1, no son tres figuras
        ((1, 2, 3), 6),
    ],
)
def test_puntaje_de_manos_normales(valores, esperado):
    assert calcular_puntaje(mano(*valores)) == esperado


@pytest.mark.parametrize(
    "valores",
    [(10, 11, 12), (10, 10, 10), (12, 12, 12), (11, 12, 10)],
)
def test_tres_figuras_valen_8_5(valores):
    assert es_tres_figuras(mano(*valores))
    assert calcular_puntaje(mano(*valores)) == PUNTAJE_TRES_FIGURAS


def test_dos_figuras_no_son_mano_especial():
    assert not es_tres_figuras(mano(10, 11))
    assert calcular_puntaje(mano(10, 11)) == 0  # 20 -> 0


def test_tres_figuras_gana_a_cualquier_8_pero_pierde_con_9():
    tres_figuras = calcular_puntaje(mano(10, 11, 12))
    assert tres_figuras > calcular_puntaje(mano(4, 4))  # 8
    assert tres_figuras < calcular_puntaje(mano(4, 5))  # 9


def test_el_puntaje_nunca_pasa_de_9():
    for n in (2, 3):
        for combo in itertools.combinations_with_replacement(VALORES, n):
            assert 0 <= calcular_puntaje(mano(*combo)) <= 9


def test_equivalencia_con_la_formula_original():
    """Regresión: el refactor no debe cambiar ningún puntaje.

    Reproduce la fórmula del main.py original y la compara contra la actual
    para todas las manos posibles de 2 y 3 cartas.
    """

    def original(cartas):
        figs = ['10', '11', '12']
        valores = [str(c.valor) for c in cartas]
        if len(cartas) == 3 and sum(1 for v in valores if v in figs) == 3:
            return 8.5
        total = sum(10 if v in figs else int(v) for v in valores)
        return total % 10 if total >= 10 else total

    for n in (2, 3):
        for combo in itertools.combinations_with_replacement(VALORES, n):
            cartas = mano(*combo)
            assert calcular_puntaje(cartas) == original(cartas), combo


def test_el_palo_no_afecta_el_puntaje():
    a = [Carta(Palo.OROS, 5), Carta(Palo.COPAS, 3)]
    b = [Carta(Palo.ESPADAS, 5), Carta(Palo.BASTOS, 3)]
    assert calcular_puntaje(a) == calcular_puntaje(b)


# --- Resolución ---------------------------------------------------------------


def test_gana_el_puntaje_mas_alto():
    assert resolver(mano(4, 5), mano(1, 2)) is Resultado.GANA_JUGADOR
    assert resolver(mano(1, 2), mano(4, 5)) is Resultado.GANA_BANCA


def test_mismo_puntaje_es_empate():
    assert resolver(mano(4, 5), mano(7, 2)) is Resultado.EMPATE


def test_el_empate_favorece_a_la_banca():
    assert not suma_punto_el_jugador(Resultado.EMPATE)
    assert not suma_punto_el_jugador(Resultado.GANA_BANCA)
    assert suma_punto_el_jugador(Resultado.GANA_JUGADOR)


def test_tres_figuras_le_gana_a_ocho():
    assert resolver(mano(10, 11, 12), mano(4, 4)) is Resultado.GANA_JUGADOR


def test_nueve_le_gana_a_tres_figuras():
    assert resolver(mano(10, 11, 12), mano(4, 5)) is Resultado.GANA_BANCA


def test_todas_las_cartas_del_mazo_producen_puntaje_valido():
    for carta in crear_mazo():
        assert 0 <= calcular_puntaje([carta]) <= 9
