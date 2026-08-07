"""Tests de las medidas responsive. No requieren Flet."""

import pytest

from makai.core.reglas import MAX_CARTAS_POR_MANO
from makai.ui.layout import (
    ANCHO_MAXIMO_CARTA,
    ANCHO_MINIMO_CARTA,
    MARGEN_LATERAL,
    PROPORCION_CARTA,
    alto_de_carta,
    ancho_de_carta,
    ancho_ocupado,
    es_pantalla_angosta,
    tamano_texto,
)

# Anchos reales de dispositivos comunes.
IPHONE_SE = 375
IPHONE_PRO_MAX = 430
TABLET = 768
ESCRITORIO = 1280


@pytest.mark.parametrize("ancho", [280, 320, IPHONE_SE, IPHONE_PRO_MAX, TABLET, ESCRITORIO])
def test_una_mano_completa_siempre_entra_en_pantalla(ancho):
    """Es la razon de ser de este modulo: 3 cartas tienen que entrar."""
    carta = ancho_de_carta(ancho)
    ocupado = ancho_ocupado(carta)
    assert ocupado <= ancho - 2 * MARGEN_LATERAL + 0.01, (
        f"con ancho {ancho} la mano ocupa {ocupado}px y desborda"
    )


@pytest.mark.parametrize("ancho", [IPHONE_SE, IPHONE_PRO_MAX, TABLET, ESCRITORIO])
def test_la_carta_nunca_baja_del_minimo_legible(ancho):
    assert ancho_de_carta(ancho) >= ANCHO_MINIMO_CARTA


def test_en_escritorio_se_usa_el_tamano_original():
    assert ancho_de_carta(ESCRITORIO) == ANCHO_MAXIMO_CARTA


#: Por debajo de este ancho las 3 cartas ya no entran a tamaño completo:
#: 3*100 + 2*15 de separación + 2*16 de margen = 362.
UMBRAL_ACHICADO = 362

ANDROID_CHICO = 320


def test_en_pantallas_chicas_la_carta_se_achica():
    assert ancho_de_carta(ANDROID_CHICO) < ANCHO_MAXIMO_CARTA


def test_justo_en_el_umbral_todavia_entra_a_tamano_completo():
    assert ancho_de_carta(UMBRAL_ACHICADO) == ANCHO_MAXIMO_CARTA
    assert ancho_de_carta(UMBRAL_ACHICADO - 1) < ANCHO_MAXIMO_CARTA


def test_pantallas_mas_anchas_no_dan_cartas_mas_grandes_que_el_maximo():
    for ancho in (ESCRITORIO, 1920, 3840):
        assert ancho_de_carta(ancho) == ANCHO_MAXIMO_CARTA


def test_el_ancho_crece_con_la_pantalla():
    anchos = [ancho_de_carta(a) for a in (320, 375, 430, 600)]
    assert anchos == sorted(anchos)


@pytest.mark.parametrize("ancho", [None, 0, -100])
def test_sin_medida_de_pantalla_se_asume_escritorio(ancho):
    """Flet no reporta page.width hasta el primer render."""
    assert ancho_de_carta(ancho) == ANCHO_MAXIMO_CARTA


def test_una_pantalla_absurdamente_angosta_no_rompe():
    assert ancho_de_carta(120) == ANCHO_MINIMO_CARTA


def test_el_alto_conserva_la_proporcion_de_las_imagenes():
    assert alto_de_carta(100) == 150
    assert alto_de_carta(ANCHO_MINIMO_CARTA) == ANCHO_MINIMO_CARTA * PROPORCION_CARTA


def test_se_puede_pedir_una_mano_mas_chica():
    """Con 2 cartas hay mas espacio por carta que con 3."""
    assert ancho_de_carta(IPHONE_SE, cartas_por_mano=2) >= ancho_de_carta(
        IPHONE_SE, cartas_por_mano=MAX_CARTAS_POR_MANO
    )


# --- Pantalla angosta y tipografia -------------------------------------------


@pytest.mark.parametrize(
    ("ancho", "esperado"),
    [(IPHONE_SE, True), (IPHONE_PRO_MAX, True), (TABLET, False), (ESCRITORIO, False)],
)
def test_deteccion_de_pantalla_angosta(ancho, esperado):
    assert es_pantalla_angosta(ancho) is esperado


def test_sin_medida_no_se_considera_angosta():
    assert es_pantalla_angosta(None) is False


def test_el_titulo_se_achica_en_telefono():
    assert tamano_texto(60, IPHONE_SE) < 60


def test_el_titulo_no_cambia_en_escritorio():
    assert tamano_texto(60, ESCRITORIO) == 60
    assert tamano_texto(30, None) == 30
