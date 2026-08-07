"""Tests de los niveles de dificultad de la PC."""

import itertools
import random

import pytest

from makai.ai import (
    DIFICULTADES,
    Dificultad,
    estrategia_dificil,
    estrategia_facil,
    estrategia_normal,
    estrategia_para,
)
from makai.core.cartas import Carta, Palo
from makai.core.estrategia import Contexto
from makai.core.partida import Partida
from makai.core.reglas import Rol


def contexto(propias, rival=(), es_banca=False):
    palos = itertools.cycle(Palo)
    return Contexto(
        mano=tuple(Carta(next(palos), v) for v in propias),
        mano_rival=tuple(Carta(next(palos), v) for v in rival),
        es_banca=es_banca,
    )


# --- Umbrales -----------------------------------------------------------------


def test_facil_se_planta_antes_que_normal():
    # Con 5 puntos: normal (umbral 6) pide, facil (umbral 2) no.
    c = contexto((1, 4))
    assert estrategia_normal(c) is True
    assert estrategia_facil(c) is False


def test_facil_solo_pide_con_manos_muy_malas():
    assert estrategia_facil(contexto((7, 3))) is True  # 10 -> 0
    assert estrategia_facil(contexto((1, 2))) is False  # 3, ya se conforma


def test_normal_mantiene_el_umbral_historico():
    assert estrategia_normal(contexto((1, 4))) is True  # 5 < 6
    assert estrategia_normal(contexto((1, 5))) is False  # 6


@pytest.mark.parametrize("estrategia", [estrategia_facil, estrategia_normal, estrategia_dificil])
def test_ninguna_estrategia_pide_con_tres_cartas(estrategia):
    """Aunque vaya perdiendo: el maximo por mano son 3 cartas."""
    assert estrategia(contexto((1, 1, 1), rival=(4, 5))) is False


# --- Dificil ------------------------------------------------------------------


def test_dificil_se_planta_si_ya_va_ganando():
    # 9 contra 5: no tiene sentido arriesgar.
    assert estrategia_dificil(contexto((4, 5), rival=(1, 4))) is False


def test_dificil_pide_si_va_perdiendo():
    # 3 contra 9: plantarse es perder seguro.
    assert estrategia_dificil(contexto((1, 2), rival=(4, 5))) is True


def test_dificil_de_banca_se_conforma_con_empatar():
    """El empate favorece a la banca, asi que igualar alcanza."""
    empatados = contexto((4, 5), rival=(7, 2), es_banca=True)
    assert estrategia_dificil(empatados) is False


def test_dificil_sin_banca_no_se_conforma_con_empatar():
    """Sin la banca, el empate se pierde: hay que superar al rival."""
    empatados = contexto((4, 5), rival=(7, 2), es_banca=False)
    assert estrategia_dificil(empatados) is True


def test_dificil_mira_al_rival_y_normal_no():
    """Con 7 puntos, normal siempre se planta; dificil depende del rival."""
    assert estrategia_normal(contexto((3, 4), rival=(4, 5))) is False
    assert estrategia_dificil(contexto((3, 4), rival=(4, 5))) is True
    assert estrategia_dificil(contexto((3, 4), rival=(1, 2))) is False


# --- Registro -----------------------------------------------------------------


def test_hay_una_estrategia_por_cada_dificultad():
    assert set(DIFICULTADES) == set(Dificultad)


@pytest.mark.parametrize("dificultad", list(Dificultad))
def test_estrategia_para_devuelve_algo_invocable(dificultad):
    assert callable(estrategia_para(dificultad))


@pytest.mark.parametrize("dificultad", list(Dificultad))
def test_toda_dificultad_tiene_etiqueta(dificultad):
    assert dificultad.etiqueta


def test_desde_texto_acepta_lo_guardado():
    assert Dificultad.desde_texto("dificil") is Dificultad.DIFICIL


@pytest.mark.parametrize("basura", [None, "", "imposible", 42, {}])
def test_desde_texto_tolera_valores_invalidos(basura):
    assert Dificultad.desde_texto(basura) is Dificultad.NORMAL


def test_desde_texto_respeta_el_default_dado():
    assert Dificultad.desde_texto("nada", Dificultad.FACIL) is Dificultad.FACIL


# --- Comportamiento en partidas reales ----------------------------------------


def tasa_de_rondas_ganadas(dificultad, rondas=6000, semilla=7):
    """Porcentaje de rondas que gana un jugador pasivo contra este nivel.

    Se mide por ronda y no por partida: una partida completa amplifica
    cualquier ventaja hasta saturar (con una ventaja chica el jugador pierde
    casi el 100% igual), lo que borra las diferencias entre niveles.

    El jugador se planta siempre con 2 cartas, asi que la unica variable es la
    estrategia de la PC. La banca queda fija en la PC para que todas las
    mediciones sean comparables.
    """
    estrategia = estrategia_para(dificultad)
    rng = random.Random(semilla)
    ganadas = 0
    for _ in range(rondas):
        p = Partida(
            fichas_iniciales=10**9,
            banca_inicial=Rol.PC,
            rng=rng,
            estrategia_pc=estrategia,
        )
        p.repartir()
        p.plantarse()
        while p.pc_debe_pedir():
            p.pc_pide()
        ganadas += p.resolver_ronda().ganador is Rol.JUGADOR
    return 100 * ganadas / rondas


@pytest.mark.lento
def test_los_niveles_estan_realmente_ordenados():
    """Cada nivel tiene que ser medible mas dificil que el anterior.

    Regresion: una version anterior usaba umbral 4 para Facil, que esta pegado
    al optimo de la PC (5) y por lo tanto jugaba igual de bien que Normal. El
    test de entonces solo comparaba cada nivel contra Dificil, nunca Facil
    contra Normal, asi que no lo detecto.
    """
    facil = tasa_de_rondas_ganadas(Dificultad.FACIL)
    normal = tasa_de_rondas_ganadas(Dificultad.NORMAL)
    dificil = tasa_de_rondas_ganadas(Dificultad.DIFICIL)

    medidas = f"facil={facil:.1f}% normal={normal:.1f}% dificil={dificil:.1f}%"
    assert facil > normal, f"Facil no es mas facil que Normal: {medidas}"
    assert normal > dificil, f"Normal no es mas facil que Dificil: {medidas}"

    # Margenes holgados frente al ruido de muestreo (~0.6 puntos de error
    # estandar con 6000 rondas), pero suficientes para detectar niveles que se
    # solapan.
    assert facil - normal > 2, f"Facil y Normal casi no se distinguen: {medidas}"
    assert normal - dificil > 1.5, f"Normal y Dificil casi no se distinguen: {medidas}"
