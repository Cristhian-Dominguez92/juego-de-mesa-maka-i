"""Tests de los personajes. No requieren Flet."""

import pathlib

import pytest

from makai.ui.personajes import (
    CLAVE_PERSONAJE,
    PERSONAJES,
    POR_DEFECTO,
    cargar,
    guardar,
    por_id,
    rival_de,
)

AVATARES = pathlib.Path(__file__).parent.parent / "assets" / "Personajes"


class AlmacenamientoStub:
    def __init__(self, datos=None):
        self.datos = dict(datos or {})

    def get(self, clave):
        return self.datos.get(clave)

    def set(self, clave, valor):
        self.datos[clave] = valor
        return True


class AlmacenamientoRoto:
    def get(self, clave):
        raise RuntimeError("sin almacenamiento")

    def set(self, clave, valor):
        raise RuntimeError("sin almacenamiento")


# --- La lista ------------------------------------------------------------------


def test_estan_los_seis_personajes():
    assert len(PERSONAJES) == 6


def test_los_nombres_pedidos_estan_todos():
    nombres = {p.nombre for p in PERSONAJES}
    assert nombres == {"Sultano", "Mengano", "El Gordo", "Flaco", "Vaicho", "Leporato"}


def test_los_identificadores_no_se_repiten():
    ids = [p.id for p in PERSONAJES]
    assert len(ids) == len(set(ids))


def test_el_personaje_por_defecto_esta_en_la_lista():
    assert POR_DEFECTO in PERSONAJES


# --- Retratos ------------------------------------------------------------------


@pytest.mark.parametrize("personaje", PERSONAJES, ids=lambda p: p.id)
def test_cada_personaje_tiene_su_retrato(personaje):
    """Sin esto, un personaje nuevo saldria con la imagen rota."""
    assert (AVATARES / personaje.archivo).is_file(), (
        f"Falta {personaje.archivo}; regeneralo con tools/generar_avatares.py"
    )


def test_no_hay_retratos_huerfanos():
    esperados = {p.archivo for p in PERSONAJES}
    assert {f.name for f in AVATARES.glob("*.webp")} - esperados == set()


# --- Busqueda ------------------------------------------------------------------


@pytest.mark.parametrize("personaje", PERSONAJES, ids=lambda p: p.id)
def test_se_encuentra_por_id(personaje):
    assert por_id(personaje.id) is personaje


@pytest.mark.parametrize("basura", [None, "", "nadie", 42, {}])
def test_un_id_invalido_cae_en_el_por_defecto(basura):
    assert por_id(basura) is POR_DEFECTO


def test_se_respeta_el_default_indicado():
    otro = PERSONAJES[3]
    assert por_id("nadie", otro) is otro


# --- Rival ---------------------------------------------------------------------


@pytest.mark.parametrize("personaje", PERSONAJES, ids=lambda p: p.id)
def test_la_pc_nunca_usa_el_mismo_personaje(personaje):
    assert rival_de(personaje) != personaje


@pytest.mark.parametrize("personaje", PERSONAJES, ids=lambda p: p.id)
def test_el_rival_es_uno_de_la_lista(personaje):
    assert rival_de(personaje) in PERSONAJES


# --- Persistencia --------------------------------------------------------------


def test_se_guarda_y_se_recupera():
    almacen = AlmacenamientoStub()
    elegido = PERSONAJES[4]
    guardar(almacen, elegido)
    assert cargar(almacen) is elegido


def test_sin_nada_guardado_es_el_por_defecto():
    assert cargar(AlmacenamientoStub()) is POR_DEFECTO


def test_un_valor_corrupto_cae_en_el_por_defecto():
    assert cargar(AlmacenamientoStub({CLAVE_PERSONAJE: "inexistente"})) is POR_DEFECTO


def test_un_almacenamiento_roto_no_tumba_el_juego():
    assert cargar(AlmacenamientoRoto()) is POR_DEFECTO
    guardar(AlmacenamientoRoto(), PERSONAJES[0])  # no debe lanzar
