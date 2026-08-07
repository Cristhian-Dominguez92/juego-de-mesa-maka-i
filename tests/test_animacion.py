"""Tests de las animaciones del tablero.

No verifican que se vean bien —eso no se puede automatizar— sino que **terminen
donde deben**: una carta que se queda a medio aparecer o de canto es invisible
en pantalla, y es el modo de fallo que importa.
"""

import asyncio

import pytest

pytest.importorskip("flet")

import flet as ft  # noqa: E402

from makai.ui import animacion  # noqa: E402


@pytest.fixture
def sin_esperas(monkeypatch):
    async def no_esperar(_segundos):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_esperar)


def carta(src="dorso.jpeg"):
    return ft.Container(content=ft.Image(src=src))


def nada():
    return None


# --- Ocultar ------------------------------------------------------------------


def test_ocultar_deja_la_carta_invisible():
    c = animacion.ocultar(carta())
    assert c.opacity == 0
    assert c.scale.scale < 1


def test_ocultar_devuelve_el_mismo_control():
    c = carta()
    assert animacion.ocultar(c) is c


# --- Aparecer -----------------------------------------------------------------


def test_aparecer_deja_las_cartas_visibles(sin_esperas):
    cartas = [animacion.ocultar(carta()) for _ in range(3)]
    asyncio.run(animacion.aparecer(cartas, nada))

    for c in cartas:
        assert c.opacity == 1, "una carta quedo invisible"
        assert c.scale.scale == 1, "una carta quedo encogida"


def test_aparecer_refresca_una_vez_por_carta(sin_esperas):
    refrescos = []
    cartas = [animacion.ocultar(carta()) for _ in range(4)]
    asyncio.run(animacion.aparecer(cartas, lambda: refrescos.append(1)))
    assert len(refrescos) == 4


def test_aparecer_sin_cartas_no_falla(sin_esperas):
    asyncio.run(animacion.aparecer([], nada))


# --- Voltear ------------------------------------------------------------------


def test_voltear_termina_con_la_carta_de_frente(sin_esperas):
    c = carta("dorso.jpeg")

    def mostrar():
        c.content.src = "1_oro.jpeg"

    asyncio.run(animacion.voltear(c, mostrar, nada))

    assert c.content.src == "1_oro.jpeg"
    assert c.scale.scale_x == 1, "la carta quedo de canto"


def test_la_cara_se_cambia_mientras_la_carta_esta_de_canto(sin_esperas):
    """Si la imagen cambiara antes, se veria el cambio de golpe."""
    c = carta("dorso.jpeg")
    escala_al_cambiar = []

    def mostrar():
        escala_al_cambiar.append(c.scale.scale_x)
        c.content.src = "1_oro.jpeg"

    asyncio.run(animacion.voltear(c, mostrar, nada))
    assert escala_al_cambiar == [animacion.ESCALA_DE_CANTO]


def test_voltear_refresca_las_dos_medias_vueltas(sin_esperas):
    refrescos = []
    asyncio.run(animacion.voltear(carta(), nada, lambda: refrescos.append(1)))
    assert len(refrescos) == 2


# --- Orden de reparto ---------------------------------------------------------


def test_el_reparto_alterna_entre_las_dos_manos():
    a = [carta("a1"), carta("a2")]
    b = [carta("b1"), carta("b2")]
    orden = animacion.repartir_alternando(a, b)
    assert [c.content.src for c in orden] == ["a1", "b1", "a2", "b2"]


def test_las_cartas_no_se_pierden_si_una_mano_tiene_mas():
    a = [carta("a1"), carta("a2"), carta("a3")]
    b = [carta("b1")]
    orden = animacion.repartir_alternando(a, b)
    assert [c.content.src for c in orden] == ["a1", "b1", "a2", "a3"]


def test_las_cartas_no_se_pierden_si_la_otra_mano_tiene_mas():
    a = [carta("a1")]
    b = [carta("b1"), carta("b2")]
    orden = animacion.repartir_alternando(a, b)
    assert [c.content.src for c in orden] == ["a1", "b1", "b2"]


def test_alternar_manos_vacias_no_falla():
    assert animacion.repartir_alternando([], []) == []
