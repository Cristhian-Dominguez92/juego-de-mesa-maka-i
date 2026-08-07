"""Modelo de la baraja española de 40 cartas."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Palo(Enum):
    """Los cuatro palos.

    El valor de cada miembro es el sufijo que usan los archivos de imagen
    (`1_oro.jpeg`, `12_basto.jpeg`, ...), para que el nombre del archivo se
    derive del modelo y no de un diccionario suelto en la capa de UI.
    """

    OROS = "oro"
    COPAS = "copa"
    ESPADAS = "espada"
    BASTOS = "basto"


#: La baraja española no tiene 8 ni 9: salta del 7 a la sota (10).
VALORES: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)

#: Sota (10), caballo (11) y rey (12). Todas valen 10 puntos.
FIGURAS: frozenset[int] = frozenset({10, 11, 12})

TAMANO_MAZO: int = len(Palo) * len(VALORES)


@dataclass(frozen=True)
class Carta:
    """Una carta concreta. Inmutable, para poder usarla en sets y comparaciones."""

    palo: Palo
    valor: int

    def __post_init__(self) -> None:
        if self.valor not in VALORES:
            raise ValueError(f"Valor {self.valor!r} inválido: la baraja española admite {VALORES}")

    @property
    def es_figura(self) -> bool:
        return self.valor in FIGURAS

    @property
    def nombre_archivo(self) -> str:
        """Nombre del archivo de imagen, sin directorio."""
        return f"{self.valor}_{self.palo.value}.webp"

    def __str__(self) -> str:
        return f"{self.valor} de {self.palo.name.capitalize()}"


def crear_mazo() -> list[Carta]:
    """Devuelve las 40 cartas en orden."""
    return [Carta(palo, valor) for palo in Palo for valor in VALORES]


def crear_mazo_barajado(rng: random.Random | None = None) -> list[Carta]:
    """Devuelve las 40 cartas mezcladas.

    `rng` permite inyectar un generador con semilla fija para que los tests
    sean deterministas.
    """
    mazo = crear_mazo()
    (rng or random).shuffle(mazo)
    return mazo
