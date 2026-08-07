"""Interfaz de decisión de la PC.

Vive en el core (y no en `makai/ai`) para que `Partida` no dependa del paquete
de estrategias: el core define el contrato y el default, y `makai.ai` construye
encima. Los niveles de dificultad están en `makai/ai/estrategias.py`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .cartas import Carta
from .reglas import MAX_CARTAS_POR_MANO, calcular_puntaje

#: Umbral por defecto: la PC pide mientras su puntaje esté por debajo.
UMBRAL_POR_DEFECTO = 6


@dataclass(frozen=True)
class Contexto:
    """Lo que la PC sabe al decidir si pide otra carta.

    `mano_rival` son las cartas del jugador, que en este juego están boca
    arriba: una estrategia difícil puede legítimamente mirarlas. Las de la PC
    son las que están ocultas.
    """

    mano: tuple[Carta, ...]
    mano_rival: tuple[Carta, ...]
    es_banca: bool

    @property
    def puntaje(self) -> float:
        return calcular_puntaje(self.mano)

    @property
    def puntaje_rival(self) -> float:
        return calcular_puntaje(self.mano_rival)

    @property
    def puede_pedir(self) -> bool:
        return len(self.mano) < MAX_CARTAS_POR_MANO


#: Una estrategia decide si la PC pide otra carta.
Estrategia = Callable[[Contexto], bool]


def estrategia_umbral(contexto: Contexto, umbral: float = UMBRAL_POR_DEFECTO) -> bool:
    """Pedir hasta alcanzar un umbral fijo, ignorando al rival.

    Es la estrategia histórica del juego y el default de `Partida`.
    """
    return contexto.puede_pedir and contexto.puntaje < umbral


def contexto_de(
    mano_pc: Sequence[Carta],
    mano_jugador: Sequence[Carta],
    es_banca: bool,
) -> Contexto:
    return Contexto(
        mano=tuple(mano_pc),
        mano_rival=tuple(mano_jugador),
        es_banca=es_banca,
    )
