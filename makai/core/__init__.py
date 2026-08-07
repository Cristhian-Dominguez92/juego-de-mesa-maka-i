"""Lógica de juego pura.

Este paquete NO debe importar flet ni ninguna librería de UI o audio. Esa
restricción es lo que permite testear las reglas sin abrir una ventana, y está
verificada por tests/test_core_sin_ui.py.
"""

from .cartas import FIGURAS, VALORES, Carta, Palo, crear_mazo, crear_mazo_barajado
from .estrategia import Contexto, Estrategia, contexto_de, estrategia_umbral
from .partida import (
    APUESTA_MINIMA,
    FICHAS_INICIALES,
    ApuestaInvalida,
    Estado,
    EstadoInvalido,
    Partida,
    ResultadoRonda,
)
from .reglas import (
    MAX_CARTAS_POR_MANO,
    PUNTAJE_TRES_FIGURAS,
    Resultado,
    Rol,
    calcular_puntaje,
    es_tres_figuras,
    ganador_de_ronda,
    resolver,
    siguiente_banca,
)

__all__ = [
    "APUESTA_MINIMA",
    "FICHAS_INICIALES",
    "FIGURAS",
    "MAX_CARTAS_POR_MANO",
    "PUNTAJE_TRES_FIGURAS",
    "VALORES",
    "ApuestaInvalida",
    "Carta",
    "Contexto",
    "Estado",
    "EstadoInvalido",
    "Estrategia",
    "Palo",
    "Partida",
    "Resultado",
    "ResultadoRonda",
    "Rol",
    "calcular_puntaje",
    "contexto_de",
    "crear_mazo",
    "crear_mazo_barajado",
    "es_tres_figuras",
    "estrategia_umbral",
    "ganador_de_ronda",
    "resolver",
    "siguiente_banca",
]
