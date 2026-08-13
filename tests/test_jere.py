"""Tests de Maka'i Jere: cuatro o más, sin banca, pozo al centro."""

import random

import pytest

from makai.core.cartas import Carta, Palo
from makai.core.jere import (
    APUESTA_MINIMA,
    CARTAS_INICIALES,
    MAXIMO_JUGADORES,
    MINIMO_JUGADORES,
    ApuestaInvalida,
    Declaracion,
    Estado,
    EstadoInvalido,
    PartidaJere,
)
from makai.core.reglas import MAX_CARTAS_POR_MANO

CUATRO = ("Vos", "Sultano", "Mengano", "El Gordo")


def nueva(semilla=0, nombres=CUATRO, **kwargs):
    return PartidaJere(nombres, rng=random.Random(semilla), **kwargs)


def declarar_todos(partida, del_humano=Declaracion.PLANTO):
    """Hace declarar a todos: al humano lo indicado, a la PC su estrategia."""
    while partida.turno is not None:
        if partida.es_turno_del_humano:
            partida.declarar(del_humano)
        else:
            partida.declarar(partida.declaracion_de_la_pc())


def jugar_ronda(partida, del_humano=Declaracion.PLANTO):
    partida.repartir()
    declarar_todos(partida, del_humano)
    return partida.resolver_ronda()


# --- Cantidad de jugadores -----------------------------------------------------


def test_jere_no_se_juega_de_a_menos_de_cuatro():
    with pytest.raises(ValueError):
        PartidaJere(("Vos", "Sultano", "Mengano"))


@pytest.mark.parametrize("cantidad", range(MINIMO_JUGADORES, MAXIMO_JUGADORES + 1))
def test_se_puede_elegir_la_cantidad(cantidad):
    p = nueva(nombres=tuple(f"J{i}" for i in range(cantidad)))
    assert len(p.jugadores) == cantidad


def test_hay_un_solo_humano():
    p = nueva()
    assert sum(1 for j in p.jugadores if j.es_humano) == 1
    assert p.humano.nombre == "Vos"


# --- Reparto -------------------------------------------------------------------


def test_todos_reciben_dos_cartas():
    p = nueva()
    p.repartir()
    for jugador in p.en_ronda:
        assert len(jugador.mano) == CARTAS_INICIALES


def test_el_reparto_no_repite_cartas():
    p = nueva()
    p.repartir()
    repartidas = [c for j in p.en_ronda for c in j.mano]
    assert len(set(repartidas)) == len(repartidas)


def test_no_se_reparte_dos_veces_seguidas():
    p = nueva()
    p.repartir()
    with pytest.raises(EstadoInvalido):
        p.repartir()


# --- El pozo -------------------------------------------------------------------


def test_todos_ponen_lo_mismo_y_arman_el_pozo():
    p = nueva(fichas_iniciales=100, apuesta=5)
    p.repartir()
    assert p.pozo == 5 * len(CUATRO)
    for jugador in p.jugadores:
        assert jugador.fichas == 95


def test_el_ganador_se_lleva_el_pozo_entero():
    p = nueva(fichas_iniciales=100, apuesta=10)
    r = jugar_ronda(p)
    assert r.pozo == 10 * len(CUATRO)
    assert r.ganador.fichas == 100 - 10 + r.pozo


def test_el_total_de_fichas_se_conserva():
    p = nueva(fichas_iniciales=100, apuesta=5)
    total = 100 * len(CUATRO)
    for _ in range(12):
        r = jugar_ronda(p)
        assert sum(j.fichas for j in p.jugadores) == total
        if r.partida_terminada:
            break
        p.nueva_ronda()


def test_el_pozo_nunca_queda_sin_repartir():
    """La regla es explicita: el pozo se define en la ronda, no se arrastra."""
    p = nueva(7, fichas_iniciales=100, apuesta=5)
    for _ in range(15):
        antes = sum(j.fichas for j in p.jugadores)
        r = jugar_ronda(p)
        assert sum(j.fichas for j in p.jugadores) == antes, "quedaron fichas en la mesa"
        assert r.pozo > 0
        if r.partida_terminada:
            break
        p.nueva_ronda()


# --- Apuestas ------------------------------------------------------------------


def test_no_se_puede_apostar_menos_del_minimo():
    p = nueva()
    with pytest.raises(ApuestaInvalida):
        p.apostar(APUESTA_MINIMA - 1)


def test_nadie_apuesta_mas_de_lo_que_el_mas_pobre_puede_pagar():
    p = nueva(fichas_iniciales=40)
    p.jugadores[2].fichas = 8
    assert p.apuesta_maxima == 8
    with pytest.raises(ApuestaInvalida):
        p.apostar(9)


def test_no_se_puede_apostar_con_la_ronda_en_juego():
    p = nueva()
    p.repartir()
    with pytest.raises(EstadoInvalido):
        p.apostar(10)


# --- Declaraciones: "y pie" ----------------------------------------------------


def test_el_turno_arranca_por_la_mano():
    p = nueva()
    p.repartir()
    assert p.turno is p.jugadores[0]


def test_cada_declaracion_pasa_el_turno_al_siguiente():
    p = nueva()
    p.repartir()
    vistos = []
    while p.turno is not None:
        vistos.append(p.turno.indice)
        p.declarar(Declaracion.PLANTO)
    assert vistos == [0, 1, 2, 3], "el turno debe recorrer la mesa en orden"


def test_pedir_carta_agrega_una_sola():
    p = nueva()
    p.repartir()
    jugador = p.declarar(Declaracion.CARTA)
    assert len(jugador.mano) == CARTAS_INICIALES + 1


def test_plantarse_no_agrega_cartas():
    p = nueva()
    p.repartir()
    jugador = p.declarar(Declaracion.PLANTO)
    assert len(jugador.mano) == CARTAS_INICIALES


def test_nadie_pasa_de_tres_cartas():
    p = nueva()
    p.repartir()
    declarar_todos(p, Declaracion.CARTA)
    for jugador in p.en_ronda:
        assert len(jugador.mano) <= MAX_CARTAS_POR_MANO


def test_queda_registrado_lo_que_canto_cada_uno():
    p = nueva()
    p.repartir()
    p.declarar(Declaracion.CARTA)
    assert p.jugadores[0].declaracion is Declaracion.CARTA
    assert p.jugadores[0].declaracion.value == "carta y pie"
    p.declarar(Declaracion.PLANTO)
    assert p.jugadores[1].declaracion.value == "planto y pie"


def test_no_se_resuelve_si_falta_alguien_por_declarar():
    p = nueva()
    p.repartir()
    p.declarar(Declaracion.PLANTO)
    with pytest.raises(EstadoInvalido):
        p.resolver_ronda()


def test_la_pc_no_declara_en_el_turno_del_humano():
    p = nueva()
    p.repartir()
    assert p.es_turno_del_humano
    with pytest.raises(EstadoInvalido):
        p.declaracion_de_la_pc()


# --- Ganador y desempate -------------------------------------------------------


def test_gana_el_puntaje_mas_alto():
    """Los mejores se miran ANTES de resolver.

    Si hay empate, el desempate reparte cartas nuevas y las manos originales
    dejan de existir: comparar despues daria un resultado sin sentido.
    """
    p = nueva()
    p.repartir()
    declarar_todos(p)

    tope = max(j.puntaje for j in p.en_ronda)
    mejores = {j.nombre for j in p.en_ronda if j.puntaje == tope}

    r = p.resolver_ronda()
    assert r.ganador.nombre in mejores


def test_el_empate_se_define_con_un_desempate():
    p = nueva()
    p.repartir()
    # Se fuerza un empate en 9 entre los dos primeros.
    p.jugadores[0].mano = [Carta(Palo.OROS, 4), Carta(Palo.COPAS, 5)]
    p.jugadores[1].mano = [Carta(Palo.ESPADAS, 7), Carta(Palo.BASTOS, 2)]
    p.jugadores[2].mano = [Carta(Palo.OROS, 1), Carta(Palo.COPAS, 1)]
    p.jugadores[3].mano = [Carta(Palo.ESPADAS, 1), Carta(Palo.BASTOS, 2)]
    declarar_todos(p)

    r = p.resolver_ronda()
    assert r.hubo_desempate
    assert set(r.empatados) == {p.jugadores[0].nombre, p.jugadores[1].nombre}
    assert r.ganador.nombre in r.empatados


def test_el_desempate_reparte_dos_cartas_sin_opcion_a_tercera():
    p = nueva()
    p.repartir()
    p.jugadores[0].mano = [Carta(Palo.OROS, 4), Carta(Palo.COPAS, 5)]
    p.jugadores[1].mano = [Carta(Palo.ESPADAS, 7), Carta(Palo.BASTOS, 2)]
    p.jugadores[2].mano = [Carta(Palo.OROS, 1), Carta(Palo.COPAS, 1)]
    p.jugadores[3].mano = [Carta(Palo.ESPADAS, 1), Carta(Palo.BASTOS, 2)]
    declarar_todos(p)
    p.resolver_ronda()

    for nombre in (p.jugadores[0].nombre, p.jugadores[1].nombre):
        jugador = next(j for j in p.jugadores if j.nombre == nombre)
        assert len(jugador.mano) == CARTAS_INICIALES


def test_sin_empate_no_se_informa_desempate():
    p = nueva()
    p.repartir()
    p.jugadores[0].mano = [Carta(Palo.OROS, 4), Carta(Palo.COPAS, 5)]  # 9
    p.jugadores[1].mano = [Carta(Palo.ESPADAS, 1), Carta(Palo.BASTOS, 1)]  # 2
    p.jugadores[2].mano = [Carta(Palo.OROS, 1), Carta(Palo.COPAS, 2)]  # 3
    p.jugadores[3].mano = [Carta(Palo.ESPADAS, 2), Carta(Palo.BASTOS, 2)]  # 4
    declarar_todos(p)

    r = p.resolver_ronda()
    assert not r.hubo_desempate
    assert r.ganador is p.jugadores[0]


# --- Rotación de la mano -------------------------------------------------------


def test_la_mano_rota_en_cada_ronda():
    p = nueva(fichas_iniciales=1000, apuesta=1)
    primeros = []
    for _ in range(4):
        p.repartir()
        primeros.append(p.turno.indice)
        declarar_todos(p)
        p.resolver_ronda()
        p.nueva_ronda()
    assert primeros == [0, 1, 2, 3], "la mano debe pasar al de al lado"


# --- Fin de partida ------------------------------------------------------------


def test_el_que_se_queda_sin_fichas_sale():
    p = nueva(fichas_iniciales=5, apuesta=5)
    jugar_ronda(p)
    sin_fichas = [j for j in p.jugadores if not j.sigue_en_partida]
    assert len(sin_fichas) == len(CUATRO) - 1


def test_la_partida_termina_cuando_queda_uno():
    p = nueva(fichas_iniciales=5, apuesta=5)
    r = jugar_ronda(p)
    assert r.partida_terminada
    assert p.estado is Estado.PARTIDA_TERMINADA
    assert len(p.activos) == 1


def test_toda_partida_termina_con_un_solo_ganador():
    for semilla in range(12):
        p = nueva(semilla, fichas_iniciales=30, apuesta=5)
        for _ in range(400):
            r = jugar_ronda(p)
            if r.partida_terminada:
                break
            p.nueva_ronda()
        assert p.estado is Estado.PARTIDA_TERMINADA
        assert len(p.activos) == 1
        assert p.activos[0].fichas == 30 * len(CUATRO)


def test_reiniciar_devuelve_todo_al_principio():
    p = nueva(fichas_iniciales=20, apuesta=5)
    jugar_ronda(p)
    p.reiniciar()
    assert all(j.fichas == 20 for j in p.jugadores)
    assert p.pozo == 0
    assert p.estado is Estado.ESPERANDO_REPARTO


# --- Determinismo --------------------------------------------------------------


def test_la_misma_semilla_reproduce_la_misma_ronda():
    a, b = nueva(99), nueva(99)
    ra, rb = jugar_ronda(a), jugar_ronda(b)
    assert [j.mano for j in a.jugadores] == [j.mano for j in b.jugadores]
    assert ra.ganador.nombre == rb.ganador.nombre
