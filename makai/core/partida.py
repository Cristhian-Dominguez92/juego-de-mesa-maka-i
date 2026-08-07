"""Máquina de estados de una partida.

`Partida` no sabe nada de UI: expone el turno de la banca paso a paso
(`banca_debe_pedir` / `banca_pide`) en lugar de resolverlo en un bucle cerrado,
justamente para que la capa de presentación pueda animar carta por carta.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto

from .cartas import Carta, crear_mazo_barajado
from .reglas import (
    MAX_CARTAS_POR_MANO,
    RONDAS_PARA_GANAR,
    Resultado,
    calcular_puntaje,
    resolver,
    suma_punto_el_jugador,
)

#: Cartas que recibe cada mano al repartir.
CARTAS_INICIALES = 2

#: La banca pide mientras su puntaje esté por debajo de este umbral.
UMBRAL_BANCA = 6


class Estado(Enum):
    ESPERANDO_REPARTO = auto()
    TURNO_JUGADOR = auto()
    TURNO_BANCA = auto()
    RONDA_TERMINADA = auto()
    PARTIDA_TERMINADA = auto()


class EstadoInvalido(RuntimeError):
    """Se intentó una acción que no corresponde al estado actual."""


def estrategia_umbral(mano: Sequence[Carta], umbral: int = UMBRAL_BANCA) -> bool:
    """Estrategia por defecto de la banca: pedir hasta alcanzar el umbral.

    Es deliberadamente simple e ignora por completo la mano del jugador. Se
    reemplaza por niveles de dificultad reales en la Fase 4; la firma está
    pensada para poder inyectar otra estrategia sin tocar `Partida`.
    """
    return len(mano) < MAX_CARTAS_POR_MANO and calcular_puntaje(mano) < umbral


@dataclass(frozen=True)
class ResultadoRonda:
    """Resumen de una ronda ya resuelta."""

    resultado: Resultado
    puntaje_jugador: float
    puntaje_banca: float
    puntos_jugador: int
    puntos_banca: int
    partida_terminada: bool
    gano_el_jugador: bool


class Partida:
    """Una partida completa, jugada a `rondas_para_ganar` rondas."""

    def __init__(
        self,
        rondas_para_ganar: int = RONDAS_PARA_GANAR,
        rng: random.Random | None = None,
        estrategia_banca: Callable[[Sequence[Carta]], bool] = estrategia_umbral,
    ) -> None:
        self.rondas_para_ganar = rondas_para_ganar
        self._rng = rng
        self._estrategia_banca = estrategia_banca
        self.puntos_jugador = 0
        self.puntos_banca = 0
        self._reiniciar_ronda()
        self.estado = Estado.ESPERANDO_REPARTO

    # --- Consultas -----------------------------------------------------------

    @property
    def puntaje_jugador(self) -> float:
        return calcular_puntaje(self.mano_jugador)

    @property
    def puntaje_banca(self) -> float:
        return calcular_puntaje(self.mano_banca)

    @property
    def jugador_puede_pedir(self) -> bool:
        return self.estado is Estado.TURNO_JUGADOR and len(self.mano_jugador) < MAX_CARTAS_POR_MANO

    def banca_debe_pedir(self) -> bool:
        """True si la banca todavía quiere otra carta."""
        if self.estado is not Estado.TURNO_BANCA:
            return False
        return self._estrategia_banca(self.mano_banca)

    # --- Acciones ------------------------------------------------------------

    def repartir(self) -> None:
        """Baraja un mazo nuevo y reparte dos cartas a cada mano."""
        self._exigir(Estado.ESPERANDO_REPARTO)
        self._reiniciar_ronda()
        for _ in range(CARTAS_INICIALES):
            self.mano_jugador.append(self._robar())
            self.mano_banca.append(self._robar())
        self.estado = Estado.TURNO_JUGADOR

    def pedir(self) -> Carta:
        """El jugador pide una carta."""
        self._exigir(Estado.TURNO_JUGADOR)
        if len(self.mano_jugador) >= MAX_CARTAS_POR_MANO:
            raise EstadoInvalido(f"El jugador ya tiene el máximo de {MAX_CARTAS_POR_MANO} cartas")
        carta = self._robar()
        self.mano_jugador.append(carta)
        return carta

    def plantarse(self) -> None:
        """El jugador se planta y pasa el turno a la banca."""
        self._exigir(Estado.TURNO_JUGADOR)
        self.estado = Estado.TURNO_BANCA

    def banca_pide(self) -> Carta:
        """La banca toma una carta. Llamar solo si `banca_debe_pedir()`."""
        self._exigir(Estado.TURNO_BANCA)
        if not self.banca_debe_pedir():
            raise EstadoInvalido("La banca no quiere más cartas")
        carta = self._robar()
        self.mano_banca.append(carta)
        return carta

    def resolver_ronda(self) -> ResultadoRonda:
        """Cierra la ronda, actualiza el marcador y devuelve el resumen."""
        self._exigir(Estado.TURNO_BANCA)
        resultado = resolver(self.mano_jugador, self.mano_banca)
        if suma_punto_el_jugador(resultado):
            self.puntos_jugador += 1
        else:
            self.puntos_banca += 1

        terminada = (
            self.puntos_jugador >= self.rondas_para_ganar
            or self.puntos_banca >= self.rondas_para_ganar
        )
        self.estado = Estado.PARTIDA_TERMINADA if terminada else Estado.RONDA_TERMINADA

        return ResultadoRonda(
            resultado=resultado,
            puntaje_jugador=self.puntaje_jugador,
            puntaje_banca=self.puntaje_banca,
            puntos_jugador=self.puntos_jugador,
            puntos_banca=self.puntos_banca,
            partida_terminada=terminada,
            gano_el_jugador=self.puntos_jugador >= self.rondas_para_ganar,
        )

    def nueva_ronda(self) -> None:
        """Prepara la siguiente ronda conservando el marcador."""
        self._exigir(Estado.RONDA_TERMINADA)
        self.estado = Estado.ESPERANDO_REPARTO

    def reiniciar(self) -> None:
        """Vuelve todo a cero para empezar una partida nueva."""
        self.puntos_jugador = 0
        self.puntos_banca = 0
        self._reiniciar_ronda()
        self.estado = Estado.ESPERANDO_REPARTO

    # --- Internos ------------------------------------------------------------

    def _reiniciar_ronda(self) -> None:
        # Mazo nuevo cada ronda: con 40 cartas y 6 como máximo por ronda nunca
        # se agota, pero además evita arrastrar cartas ya vistas.
        self.mazo: list[Carta] = crear_mazo_barajado(self._rng)
        self.mano_jugador: list[Carta] = []
        self.mano_banca: list[Carta] = []

    def _robar(self) -> Carta:
        if not self.mazo:
            raise EstadoInvalido("El mazo se quedó sin cartas")
        return self.mazo.pop()

    def _exigir(self, esperado: Estado) -> None:
        if self.estado is not esperado:
            raise EstadoInvalido(
                f"Se esperaba estado {esperado.name}, pero la partida está en {self.estado.name}"
            )
