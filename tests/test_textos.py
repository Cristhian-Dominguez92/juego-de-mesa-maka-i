"""Evita que la pantalla de reglas se desincronice del juego real.

El texto de `makai/ui/textos.py` está escrito a mano y no se deriva del código,
así que puede quedar mintiéndole al jugador. Estos tests atan los números que
aparecen en pantalla a las constantes que de verdad gobiernan la partida.
"""

from makai.ai.estrategias import UMBRAL_NORMAL
from makai.core.cartas import VALORES
from makai.core.partida import FICHAS_INICIALES
from makai.core.reglas import MAX_CARTAS_POR_MANO, PUNTAJE_MAXIMO, PUNTAJE_TRES_FIGURAS
from makai.ui import textos

TODO = "\n".join(f"{titulo}\n{cuerpo}" for titulo, cuerpo in textos.REGLAS)


def test_hay_secciones_y_todas_tienen_contenido():
    assert textos.REGLAS
    for titulo, cuerpo in textos.REGLAS:
        assert titulo.strip()
        assert cuerpo.strip()


def test_los_titulos_no_se_repiten():
    titulos = [t for t, _ in textos.REGLAS]
    assert len(titulos) == len(set(titulos))


def test_menciona_el_tamano_de_la_baraja():
    assert str(len(VALORES) * 4) in TODO


def test_menciona_el_maximo_de_cartas_por_mano():
    assert str(MAX_CARTAS_POR_MANO) in TODO


def test_menciona_el_puntaje_de_tres_figuras():
    assert str(PUNTAJE_TRES_FIGURAS) in TODO


def test_menciona_el_puntaje_maximo():
    assert str(PUNTAJE_MAXIMO) in TODO


def test_menciona_el_umbral_de_la_pc_en_normal():
    assert str(UMBRAL_NORMAL) in TODO


def test_no_menciona_las_fichas_iniciales_si_cambiaron():
    """Si el texto cita una cantidad de fichas, tiene que ser la real."""
    import re

    citadas = {int(n) for n in re.findall(r"\b(\d{2,4}) fichas\b", TODO)}
    assert citadas <= {FICHAS_INICIALES}, f"el texto cita fichas que no existen: {citadas}"


def test_explica_que_el_empate_lo_gana_la_banca():
    assert "empate" in TODO.lower()
    assert "banca" in TODO.lower()


def test_explica_los_tres_niveles_de_dificultad():
    for etiqueta in ("Fácil", "Normal", "Difícil"):
        assert etiqueta in TODO
