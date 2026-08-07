"""Puntuación y resolución de rondas.

Las reglas implementadas están documentadas en docs/REGLAS.md.
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


class Rol(Enum):
    """Quién es quién en la mesa.

    Importa porque la banca rota y porque el empate la favorece.
    """

    JUGADOR = "jugador"
    PC = "pc"

    @property
    def rival(self) -> Rol:
        return Rol.PC if self is Rol.JUGADOR else Rol.JUGADOR


class Resultado(Enum):
    """Quién sacó más puntaje en una ronda, sin considerar quién es banca."""

    GANA_JUGADOR = "gana_jugador"
    GANA_PC = "gana_pc"
    EMPATE = "empate"


def es_tres_figuras(mano: Sequence[Carta]) -> bool:
    """True si la mano son exactamente tres figuras."""
    return len(mano) == MAX_CARTAS_POR_MANO and all(c.es_figura for c in mano)


def calcular_puntaje(mano: Sequence[Carta]) -> float:
    """Puntaje de una mano.

    Tres figuras es una mano especial que vale 8.5, lo que la deja por encima
    de cualquier 8 pero por debajo de un 9. En cualquier otro caso se suman las
    cartas (las figuras valen 10) y **solo cuenta el último dígito**: 15 vale 5,
    y 10 vale 0.
    """
    if es_tres_figuras(mano):
        return PUNTAJE_TRES_FIGURAS
    total = sum(VALOR_FIGURA if carta.es_figura else carta.valor for carta in mano)
    return total % 10


def resolver(mano_jugador: Sequence[Carta], mano_pc: Sequence[Carta]) -> Resultado:
    """Compara dos manos por puntaje. No decide el empate: eso depende de la banca."""
    puntaje_jugador = calcular_puntaje(mano_jugador)
    puntaje_pc = calcular_puntaje(mano_pc)
    if puntaje_jugador > puntaje_pc:
        return Resultado.GANA_JUGADOR
    if puntaje_pc > puntaje_jugador:
        return Resultado.GANA_PC
    return Resultado.EMPATE


def ganador_de_ronda(resultado: Resultado, banca: Rol) -> Rol:
    """Quién se lleva la ronda. **El empate favorece a la banca.**"""
    if resultado is Resultado.EMPATE:
        return banca
    return Rol.JUGADOR if resultado is Resultado.GANA_JUGADOR else Rol.PC


def siguiente_banca(ganador: Rol) -> Rol:
    """Quién es banca en la ronda siguiente.

    La banca se conserva mientras gane; cuando pierde, pasa al rival. Los dos
    casos se reducen a lo mismo: la banca de la ronda siguiente es quien acaba
    de ganar.
    """
    return ganador
