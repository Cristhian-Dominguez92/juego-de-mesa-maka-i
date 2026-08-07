"""Lógica de juego pura.

Este paquete NO debe importar flet ni ninguna librería de UI o audio. Esa
restricción es lo que permite testear las reglas sin abrir una ventana, y está
verificada por tests/test_core_sin_ui.py.
"""

from .cartas import FIGURAS, VALORES, Carta, Palo, crear_mazo, crear_mazo_barajado
from .partida import Estado, Partida, ResultadoRonda, estrategia_umbral
from .reglas import (
    MAX_CARTAS_POR_MANO,
    PUNTAJE_TRES_FIGURAS,
    RONDAS_PARA_GANAR,
    Resultado,
    calcular_puntaje,
    es_tres_figuras,
    resolver,
)

__all__ = [
    "FIGURAS",
    "MAX_CARTAS_POR_MANO",
    "PUNTAJE_TRES_FIGURAS",
    "RONDAS_PARA_GANAR",
    "VALORES",
    "Carta",
    "Estado",
    "Palo",
    "Partida",
    "Resultado",
    "ResultadoRonda",
    "calcular_puntaje",
    "crear_mazo",
    "crear_mazo_barajado",
    "es_tres_figuras",
    "estrategia_umbral",
    "resolver",
]
