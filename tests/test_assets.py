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
    assert (ASSETS / "dorso.webp").is_file()


def test_no_hay_imagenes_huerfanas():
    """Toda imagen de carta en assets/ debe corresponder a una carta real."""
    esperadas = {c.nombre_archivo for c in crear_mazo()} | {"dorso.webp"}
    encontradas = {p.name for p in ASSETS.glob("*.webp")}
    assert encontradas - esperadas == set()


def test_no_quedaron_las_imagenes_viejas():
    """Los .jpeg de origen desconocido salieron del proyecto (ver CREDITS.md)."""
    assert list(ASSETS.glob("*.jpeg")) == []


def test_las_cartas_estan_optimizadas():
    """Los PNG sin convertir hinchan el APK: 11.9 MB contra 1.1 MB en WebP."""
    assert list(ASSETS.glob("*.png")) == [], "quedaron PNG sin convertir a WebP"
