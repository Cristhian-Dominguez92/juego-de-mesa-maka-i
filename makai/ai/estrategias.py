"""Niveles de dificultad de la PC.

Todas las estrategias reciben un `Contexto` y devuelven si la PC pide otra
carta. La PC decide siempre después de que el jugador se plantó, así que el
puntaje del rival que ve en el contexto ya es definitivo.
"""

from __future__ import annotations

from enum import Enum

from makai.core.estrategia import (
    UMBRAL_POR_DEFECTO,
    Contexto,
    Estrategia,
    estrategia_umbral,
)

# El umbral NO es monótono: como los puntajes son módulo 10, pedir de más
# empeora la mano tanto como pedir de menos. Midiendo la tasa de rondas que gana
# un jugador pasivo contra cada umbral, la curva resulta en U con el óptimo de
# la PC en 5:
#
#   umbral   0      1      2      4      5      6      8      9
#   jugador  45.0%  39.0%  36.2%  31.5%  30.7%  31.0%  35.4%  37.6%
#
# Por eso un umbral 4 NO es un nivel fácil: está pegado al óptimo y juega casi
# igual de bien que el 6. Para que la PC juegue mal hay que alejarla del centro.
#: La PC solo pide con 0 o 1 punto: se planta con manos malas.
UMBRAL_FACIL = 2

#: El umbral histórico del juego, y casi el óptimo de esta familia.
UMBRAL_NORMAL = UMBRAL_POR_DEFECTO


class Dificultad(Enum):
    FACIL = "facil"
    NORMAL = "normal"
    DIFICIL = "dificil"

    @property
    def etiqueta(self) -> str:
        return {"facil": "Fácil", "normal": "Normal", "dificil": "Difícil"}[self.value]

    @classmethod
    def desde_texto(cls, valor: object, por_defecto: Dificultad | None = None) -> Dificultad:
        """Convierte un valor guardado en disco, tolerando basura."""
        try:
            return cls(valor)
        except ValueError:
            return por_defecto or cls.NORMAL


def estrategia_facil(contexto: Contexto) -> bool:
    """Umbral bajo: se conforma con muy poco."""
    return estrategia_umbral(contexto, UMBRAL_FACIL)


def estrategia_normal(contexto: Contexto) -> bool:
    """El comportamiento clásico: pedir hasta 6, sin mirar al rival."""
    return estrategia_umbral(contexto, UMBRAL_NORMAL)


def estrategia_dificil(contexto: Contexto) -> bool:
    """Juega contra la mano concreta del jugador, que está boca arriba.

    El razonamiento es simple y fuerte: si ya va ganando, se planta; si va
    perdiendo, pide, porque quedarse como está es perder seguro. Pedir puede
    empeorar la mano (los puntajes son módulo 10), pero una chance es mejor que
    ninguna.

    Ser banca cambia la cuenta: como el empate favorece a la banca, de banca le
    alcanza con igualar, y sin la banca necesita superar al rival.
    """
    if not contexto.puede_pedir:
        return False
    if contexto.es_banca:
        return contexto.puntaje < contexto.puntaje_rival
    return contexto.puntaje <= contexto.puntaje_rival


DIFICULTADES: dict[Dificultad, Estrategia] = {
    Dificultad.FACIL: estrategia_facil,
    Dificultad.NORMAL: estrategia_normal,
    Dificultad.DIFICIL: estrategia_dificil,
}


def estrategia_para(dificultad: Dificultad) -> Estrategia:
    return DIFICULTADES[dificultad]
