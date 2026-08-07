import dataclasses
import random

import pytest

from makai.core.cartas import (
    FIGURAS,
    TAMANO_MAZO,
    VALORES,
    Carta,
    Palo,
    crear_mazo,
    crear_mazo_barajado,
)


def test_la_baraja_espanola_no_tiene_8_ni_9():
    assert 8 not in VALORES
    assert 9 not in VALORES
    assert len(VALORES) == 10


def test_el_mazo_tiene_40_cartas_sin_repetir():
    mazo = crear_mazo()
    assert len(mazo) == TAMANO_MAZO == 40
    assert len(set(mazo)) == 40


def test_cada_palo_aporta_diez_cartas():
    mazo = crear_mazo()
    for palo in Palo:
        assert sum(1 for c in mazo if c.palo is palo) == 10


@pytest.mark.parametrize("valor", sorted(FIGURAS))
def test_las_figuras_se_reconocen(valor):
    assert Carta(Palo.OROS, valor).es_figura


@pytest.mark.parametrize("valor", [1, 2, 3, 4, 5, 6, 7])
def test_los_numeros_bajos_no_son_figuras(valor):
    assert not Carta(Palo.OROS, valor).es_figura


def test_valor_fuera_de_la_baraja_es_rechazado():
    with pytest.raises(ValueError):
        Carta(Palo.COPAS, 8)


def test_la_carta_es_inmutable():
    carta = Carta(Palo.ESPADAS, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        carta.valor = 5


def test_nombre_archivo_coincide_con_el_formato_de_los_assets():
    assert Carta(Palo.OROS, 1).nombre_archivo == "1_oro.jpeg"
    assert Carta(Palo.BASTOS, 12).nombre_archivo == "12_basto.jpeg"
    assert Carta(Palo.COPAS, 10).nombre_archivo == "10_copa.jpeg"
    assert Carta(Palo.ESPADAS, 7).nombre_archivo == "7_espada.jpeg"


def test_barajar_conserva_todas_las_cartas():
    barajado = crear_mazo_barajado(random.Random(1))
    assert sorted(barajado, key=lambda c: (c.palo.value, c.valor)) == sorted(
        crear_mazo(), key=lambda c: (c.palo.value, c.valor)
    )


def test_la_misma_semilla_produce_el_mismo_mazo():
    assert crear_mazo_barajado(random.Random(42)) == crear_mazo_barajado(random.Random(42))


def test_barajar_cambia_el_orden():
    assert crear_mazo_barajado(random.Random(7)) != crear_mazo()
