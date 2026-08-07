"""Verifica que el código y los assets del disco no se desincronicen.

Si alguien renombra una imagen o cambia `Carta.nombre_archivo`, esto falla acá
en vez de mostrar una carta rota en pantalla.
"""

import pathlib

import pytest

from makai.core.cartas import crear_mazo

ASSETS = pathlib.Path(__file__).parent.parent / "assets" / "Recursos"


@pytest.mark.parametrize("carta", crear_mazo(), ids=str)
def test_cada_carta_tiene_su_imagen(carta):
    assert (ASSETS / carta.nombre_archivo).is_file(), (
        f"Falta la imagen {carta.nombre_archivo} para {carta}"
    )


def test_existe_el_dorso():
    assert (ASSETS / "dorso.jpeg").is_file()


def test_no_hay_imagenes_huerfanas():
    """Toda imagen de carta en assets/ debe corresponder a una carta real."""
    esperadas = {c.nombre_archivo for c in crear_mazo()} | {"dorso.jpeg"}
    encontradas = {p.name for p in ASSETS.glob("*.jpeg")}
    assert encontradas - esperadas == set()
