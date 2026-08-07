"""Animaciones del tablero.

Usa `asyncio.sleep` directamente para que los tests puedan anularlo y correr
las animaciones de forma instantánea, verificando el estado final sin esperar.

Flet no tiene un volteo 3D, así que la carta se voltea encogiéndola en el eje
horizontal hasta casi cero, cambiando la imagen, y volviendo a expandirla. A
simple vista se lee como una carta que gira.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable, Sequence

import flet as ft

#: Duración de la aparición de una carta, en milisegundos.
DURACION_APARICION = 260

#: Pausa entre carta y carta al repartir, en segundos.
RETARDO_ENTRE_CARTAS = 0.12

#: Duración de cada media vuelta, en milisegundos.
DURACION_VOLTEO = 170

#: Escala horizontal en el punto medio del volteo, cuando la carta está de canto.
ESCALA_DE_CANTO = 0.02


def escala(scale_x: float = 1.0) -> ft.Scale:
    return ft.Scale(scale_x=scale_x)


def ocultar(control: ft.Container) -> ft.Container:
    """Deja el control listo para aparecer: invisible y algo encogido."""
    control.opacity = 0
    control.scale = ft.Scale(scale=0.86)
    return control


async def aparecer(
    controles: Iterable[ft.Container],
    actualizar: Callable[[], None],
    retardo: float = RETARDO_ENTRE_CARTAS,
) -> None:
    """Muestra las cartas una por una, como un reparto real."""
    for control in controles:
        control.opacity = 1
        control.scale = ft.Scale(scale=1)
        actualizar()
        await asyncio.sleep(retardo)


async def voltear(
    control: ft.Container,
    mostrar_frente: Callable[[], None],
    actualizar: Callable[[], None],
) -> None:
    """Da vuelta una carta: la pone de canto, cambia la cara y la expande."""
    medio_giro = DURACION_VOLTEO / 1000

    control.scale = escala(ESCALA_DE_CANTO)
    actualizar()
    await asyncio.sleep(medio_giro)

    mostrar_frente()
    control.scale = escala(1.0)
    actualizar()
    await asyncio.sleep(medio_giro)


def repartir_alternando(
    de_un_lado: Sequence[ft.Container],
    del_otro: Sequence[ft.Container],
) -> list[ft.Container]:
    """Intercala las dos manos, que es el orden en que se reparte en la mesa."""
    alternadas: list[ft.Container] = []
    for a, b in zip(de_un_lado, del_otro, strict=False):
        alternadas.append(a)
        alternadas.append(b)
    # Si una mano tiene mas cartas que la otra, el resto va al final.
    sobrante = de_un_lado[len(del_otro) :] or del_otro[len(de_un_lado) :]
    alternadas.extend(sobrante)
    return alternadas
