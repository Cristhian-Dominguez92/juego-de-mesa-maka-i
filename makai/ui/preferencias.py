"""Preferencias del jugador que sobreviven entre sesiones.

El silencio del audio vive en `makai.ui.audio`, junto a lo que controla.
"""

from __future__ import annotations

from typing import Any, Protocol

from makai.ai import Dificultad

CLAVE_DIFICULTAD = "makai.dificultad"


class Almacenamiento(Protocol):
    def get(self, clave: str) -> Any: ...

    def set(self, clave: str, valor: Any) -> Any: ...


def cargar_dificultad(almacenamiento: Almacenamiento) -> Dificultad:
    """Lee la dificultad elegida. Ante cualquier problema, devuelve Normal."""
    try:
        crudo = almacenamiento.get(CLAVE_DIFICULTAD)
    except Exception:
        return Dificultad.NORMAL
    return Dificultad.desde_texto(crudo)


def guardar_dificultad(almacenamiento: Almacenamiento, dificultad: Dificultad) -> None:
    try:
        almacenamiento.set(CLAVE_DIFICULTAD, dificultad.value)
    except Exception:
        pass
