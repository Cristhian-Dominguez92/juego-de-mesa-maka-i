"""Los personajes que el jugador puede elegir.

Son puramente cosméticos: no cambian ninguna regla ni la dificultad. Sirven
para que la mesa tenga caras, como en cualquier juego de cartas de barrio.

Este módulo es la única fuente de verdad de la lista. `tools/generar_avatares.py`
la importa para dibujar un retrato por cada uno, y un test verifica que no
quede ninguno sin imagen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

CLAVE_PERSONAJE = "makai.personaje"


@dataclass(frozen=True)
class Personaje:
    id: str
    nombre: str

    @property
    def archivo(self) -> str:
        """Nombre del retrato, sin directorio."""
        return f"{self.id}.webp"


#: El orden es el que se ve en la pantalla de selección.
PERSONAJES: tuple[Personaje, ...] = (
    Personaje("sultano", "Sultano"),
    Personaje("mengano", "Mengano"),
    Personaje("gordo", "El Gordo"),
    Personaje("flaco", "Flaco"),
    Personaje("vaicho", "Vaicho"),
    Personaje("leporato", "Leporato"),
)

#: Con quién juega el jugador si todavía no eligió.
POR_DEFECTO = PERSONAJES[0]


def por_id(identificador: object, por_defecto: Personaje | None = None) -> Personaje:
    """Busca un personaje por su id, tolerando lo que venga guardado en disco."""
    for personaje in PERSONAJES:
        if personaje.id == identificador:
            return personaje
    return por_defecto or POR_DEFECTO


def rival_de(personaje: Personaje) -> Personaje:
    """Con qué personaje juega la PC.

    Cualquiera menos el del jugador: verse la cara repetida del otro lado de
    la mesa rompe la ilusión.
    """
    for candidato in PERSONAJES:
        if candidato != personaje:
            return candidato
    return personaje


class Almacenamiento(Protocol):
    def get(self, clave: str) -> Any: ...

    def set(self, clave: str, valor: Any) -> Any: ...


def cargar(almacenamiento: Almacenamiento) -> Personaje:
    try:
        return por_id(almacenamiento.get(CLAVE_PERSONAJE))
    except Exception:
        return POR_DEFECTO


def guardar(almacenamiento: Almacenamiento, personaje: Personaje) -> None:
    try:
        almacenamiento.set(CLAVE_PERSONAJE, personaje.id)
    except Exception:
        pass
