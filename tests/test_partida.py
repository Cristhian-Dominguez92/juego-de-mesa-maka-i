import random

import pytest

from makai.core.cartas import Carta, Palo
from makai.core.partida import (
    CARTAS_INICIALES,
    Estado,
    EstadoInvalido,
    Partida,
    estrategia_umbral,
)
from makai.core.reglas import MAX_CARTAS_POR_MANO, Resultado


def nueva_partida(semilla=0, **kwargs):
    return Partida(rng=random.Random(semilla), **kwargs)


def jugar_ronda(partida, pedir=0):
    """Juega una ronda completa: reparte, pide N veces, se planta y resuelve."""
    partida.repartir()
    for _ in range(pedir):
        partida.pedir()
    partida.plantarse()
    while partida.banca_debe_pedir():
        partida.banca_pide()
    return partida.resolver_ronda()


# --- Reparto ------------------------------------------------------------------


def test_al_repartir_cada_mano_recibe_dos_cartas():
    p = nueva_partida()
    p.repartir()
    assert len(p.mano_jugador) == len(p.mano_banca) == CARTAS_INICIALES
    assert p.estado is Estado.TURNO_JUGADOR


def test_el_reparto_no_repite_cartas():
    p = nueva_partida()
    p.repartir()
    repartidas = p.mano_jugador + p.mano_banca
    assert len(set(repartidas)) == len(repartidas)


def test_no_se_puede_repartir_dos_veces_seguidas():
    p = nueva_partida()
    p.repartir()
    with pytest.raises(EstadoInvalido):
        p.repartir()


# --- Turno del jugador --------------------------------------------------------


def test_el_jugador_puede_pedir_una_tercera_carta():
    p = nueva_partida()
    p.repartir()
    p.pedir()
    assert len(p.mano_jugador) == MAX_CARTAS_POR_MANO


def test_el_jugador_no_puede_pasar_de_tres_cartas():
    p = nueva_partida()
    p.repartir()
    p.pedir()
    assert not p.jugador_puede_pedir
    with pytest.raises(EstadoInvalido):
        p.pedir()


def test_no_se_puede_pedir_antes_de_repartir():
    p = nueva_partida()
    with pytest.raises(EstadoInvalido):
        p.pedir()


def test_no_se_puede_pedir_despues_de_plantarse():
    p = nueva_partida()
    p.repartir()
    p.plantarse()
    with pytest.raises(EstadoInvalido):
        p.pedir()


# --- Turno de la banca --------------------------------------------------------


def test_la_banca_no_juega_durante_el_turno_del_jugador():
    p = nueva_partida()
    p.repartir()
    assert not p.banca_debe_pedir()


def test_la_banca_se_planta_al_alcanzar_el_umbral():
    p = nueva_partida()
    p.repartir()
    p.plantarse()
    while p.banca_debe_pedir():
        p.banca_pide()
    assert p.puntaje_banca >= 6 or len(p.mano_banca) == MAX_CARTAS_POR_MANO


def test_la_banca_nunca_supera_tres_cartas():
    for semilla in range(30):
        p = nueva_partida(semilla)
        jugar_ronda(p)
        assert len(p.mano_banca) <= MAX_CARTAS_POR_MANO


def test_banca_pide_falla_si_ya_se_planto():
    p = nueva_partida()
    p.repartir()
    p.plantarse()
    while p.banca_debe_pedir():
        p.banca_pide()
    with pytest.raises(EstadoInvalido):
        p.banca_pide()


@pytest.mark.parametrize(
    ("valores", "deberia_pedir"),
    [
        ((1, 2), True),  # 3 < 6
        ((1, 4), True),  # 5 < 6
        ((1, 5), False),  # 6, alcanza el umbral
        ((4, 5), False),  # 9
        ((7, 3), True),  # 10 -> 0
        ((1, 2, 3), False),  # ya tiene tres cartas
    ],
)
def test_estrategia_umbral(valores, deberia_pedir):
    mano = [Carta(Palo.OROS, v) for v in valores]
    assert estrategia_umbral(mano) is deberia_pedir


def test_se_puede_inyectar_otra_estrategia():
    p = nueva_partida(estrategia_banca=lambda mano: False)
    p.repartir()
    p.plantarse()
    assert not p.banca_debe_pedir()
    assert len(p.mano_banca) == CARTAS_INICIALES


# --- Marcador -----------------------------------------------------------------


def test_el_ganador_de_la_ronda_suma_un_punto():
    p = nueva_partida()
    r = jugar_ronda(p)
    if r.resultado is Resultado.GANA_JUGADOR:
        assert (r.puntos_jugador, r.puntos_banca) == (1, 0)
    else:
        assert (r.puntos_jugador, r.puntos_banca) == (0, 1)


def test_el_empate_le_suma_a_la_banca():
    p = nueva_partida()
    p.repartir()
    # Forzamos un empate manipulando las manos ya repartidas.
    p.mano_jugador = [Carta(Palo.OROS, 4), Carta(Palo.COPAS, 5)]
    p.mano_banca = [Carta(Palo.ESPADAS, 7), Carta(Palo.BASTOS, 2)]
    p.plantarse()
    r = p.resolver_ronda()
    assert r.resultado is Resultado.EMPATE
    assert (r.puntos_jugador, r.puntos_banca) == (0, 1)


def test_siempre_se_suma_exactamente_un_punto_por_ronda():
    p = nueva_partida(rondas_para_ganar=1000)
    for ronda in range(1, 26):
        r = jugar_ronda(p)
        assert r.puntos_jugador + r.puntos_banca == ronda
        p.nueva_ronda()


# --- Fin de partida -----------------------------------------------------------


def test_la_partida_termina_al_llegar_al_objetivo():
    p = nueva_partida(rondas_para_ganar=1)
    r = jugar_ronda(p)
    assert r.partida_terminada
    assert p.estado is Estado.PARTIDA_TERMINADA


def test_la_partida_sigue_si_nadie_llego_al_objetivo():
    p = nueva_partida(rondas_para_ganar=10)
    r = jugar_ronda(p)
    assert not r.partida_terminada
    assert p.estado is Estado.RONDA_TERMINADA


def test_no_se_puede_seguir_jugando_una_partida_terminada():
    p = nueva_partida(rondas_para_ganar=1)
    jugar_ronda(p)
    with pytest.raises(EstadoInvalido):
        p.nueva_ronda()


def test_reiniciar_pone_el_marcador_a_cero():
    p = nueva_partida(rondas_para_ganar=1)
    jugar_ronda(p)
    p.reiniciar()
    assert (p.puntos_jugador, p.puntos_banca) == (0, 0)
    assert p.estado is Estado.ESPERANDO_REPARTO
    assert p.mano_jugador == p.mano_banca == []


def test_una_partida_completa_siempre_termina_con_un_ganador():
    for semilla in range(20):
        p = nueva_partida(semilla, rondas_para_ganar=10)
        rondas = 0
        while p.estado is not Estado.PARTIDA_TERMINADA:
            r = jugar_ronda(p)
            rondas += 1
            if not r.partida_terminada:
                p.nueva_ronda()
            assert rondas < 500, "la partida no converge"
        assert max(p.puntos_jugador, p.puntos_banca) == 10


# --- Determinismo -------------------------------------------------------------


def test_la_misma_semilla_reproduce_la_misma_partida():
    a, b = nueva_partida(99), nueva_partida(99)
    ra, rb = jugar_ronda(a), jugar_ronda(b)
    assert a.mano_jugador == b.mano_jugador
    assert a.mano_banca == b.mano_banca
    assert ra == rb
