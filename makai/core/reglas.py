"""Puntuación y resolución de rondas.

Las reglas implementadas están documentadas en docs/REGLAS.md, incluyendo qué
partes están confirmadas y cuáles se infirieron del código original.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum

from .cartas import Carta

#: Toda figura (sota, caballo, rey) suma 10 puntos.
VALOR_FIGURA = 10

#: Máximo de cartas que puede tener una mano.
MAX_CARTAS_POR_MANO = 3

#: Mano especial: tres figuras. Vale más que cualquier 8 pero menos que un 9.
PUNTAJE_TRES_FIGURAS = 8.5

#: Mejor puntaje numérico alcanzable.
PUNTAJE_MAXIMO = 9

#: Rondas ganadas necesarias para llevarse la partida.
RONDAS_PARA_GANAR = 10


class Resultado(Enum):
    """Desenlace de una ronda."""

    GANA_JUGADOR = "gana_jugador"
    GANA_BANCA = "gana_banca"
    EMPATE = "empate"


def es_tres_figuras(mano: Sequence[Carta]) -> bool:
    """True si la mano son exactamente tres figuras."""
    return len(mano) == MAX_CARTAS_POR_MANO and all(c.es_figura for c in mano)


def calcular_puntaje(mano: Sequence[Carta]) -> float:
    """Puntaje de una mano.

    Tres figuras es una mano especial que vale 8.5. En cualquier otro caso se
    suman las cartas (las figuras valen 10) y **solo cuenta el último dígito**:
    15 vale 5, y 10 vale 0.
    """
    if es_tres_figuras(mano):
        return PUNTAJE_TRES_FIGURAS
    total = sum(VALOR_FIGURA if carta.es_figura else carta.valor for carta in mano)
    return total % 10


def resolver(mano_jugador: Sequence[Carta], mano_banca: Sequence[Carta]) -> Resultado:
    """Compara dos manos y devuelve quién gana la ronda."""
    puntaje_jugador = calcular_puntaje(mano_jugador)
    puntaje_banca = calcular_puntaje(mano_banca)
    if puntaje_jugador > puntaje_banca:
        return Resultado.GANA_JUGADOR
    if puntaje_banca > puntaje_jugador:
        return Resultado.GANA_BANCA
    return Resultado.EMPATE


def suma_punto_el_jugador(resultado: Resultado) -> bool:
    """El empate favorece a la banca: solo una victoria limpia suma al jugador."""
    return resultado is Resultado.GANA_JUGADOR
