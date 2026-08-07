"""Máquina de estados de una partida.

`Partida` no sabe nada de UI: expone el turno de la PC paso a paso
(`pc_debe_pedir` / `pc_pide`) en lugar de resolverlo en un bucle cerrado,
justamente para que la capa de presentación pueda animar carta por carta.

La partida se juega por fichas: cada ronda se apuesta una cantidad y el ganador
se la lleva. Termina cuando alguien se queda sin fichas.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto

from .cartas import Carta, crear_mazo_barajado
from .estrategia import Estrategia, contexto_de, estrategia_umbral
from .reglas import (
    MAX_CARTAS_POR_MANO,
    Resultado,
    Rol,
    calcular_puntaje,
    ganador_de_ronda,
    resolver,
    siguiente_banca,
)

#: Cartas que recibe cada mano al repartir.
CARTAS_INICIALES = 2

#: Fichas con las que arranca cada lado.
FICHAS_INICIALES = 100

#: Apuesta mínima por ronda.
APUESTA_MINIMA = 1

#: Apuesta con la que arranca cada partida.
APUESTA_INICIAL = 5


class Estado(Enum):
    ESPERANDO_REPARTO = auto()
    TURNO_JUGADOR = auto()
    TURNO_PC = auto()
    RONDA_TERMINADA = auto()
    PARTIDA_TERMINADA = auto()


class EstadoInvalido(RuntimeError):
    """Se intentó una acción que no corresponde al estado actual."""


class ApuestaInvalida(ValueError):
    """La apuesta pedida no es jugable con las fichas disponibles."""


@dataclass(frozen=True)
class ResultadoRonda:
    """Resumen de una ronda ya resuelta."""

    resultado: Resultado
    ganador: Rol
    banca: Rol
    banca_siguiente: Rol
    apuesta: int
    puntaje_jugador: float
    puntaje_pc: float
    fichas_jugador: int
    fichas_pc: int
    partida_terminada: bool
    gano_el_jugador: bool


class Partida:
    """Una partida completa, jugada hasta que un lado se queda sin fichas."""

    def __init__(
        self,
        fichas_iniciales: int = FICHAS_INICIALES,
        banca_inicial: Rol = Rol.PC,
        rng: random.Random | None = None,
        estrategia_pc: Estrategia = estrategia_umbral,
    ) -> None:
        if fichas_iniciales < APUESTA_MINIMA:
            raise ValueError(f"Hacen falta al menos {APUESTA_MINIMA} fichas para jugar una ronda")
        self.fichas_iniciales = fichas_iniciales
        self.banca_inicial = banca_inicial
        self._rng = rng
        self._estrategia_pc = estrategia_pc
        self.reiniciar()

    # --- Consultas -----------------------------------------------------------

    @property
    def fichas_jugador(self) -> int:
        return self.fichas[Rol.JUGADOR]

    @property
    def fichas_pc(self) -> int:
        return self.fichas[Rol.PC]

    @property
    def apuesta_maxima(self) -> int:
        """Nadie puede apostar más fichas de las que el otro puede pagar."""
        return min(self.fichas[Rol.JUGADOR], self.fichas[Rol.PC])

    @property
    def jugador_es_banca(self) -> bool:
        return self.banca is Rol.JUGADOR

    @property
    def puntaje_jugador(self) -> float:
        return calcular_puntaje(self.mano_jugador)

    @property
    def puntaje_pc(self) -> float:
        return calcular_puntaje(self.mano_pc)

    @property
    def jugador_puede_pedir(self) -> bool:
        return self.estado is Estado.TURNO_JUGADOR and len(self.mano_jugador) < MAX_CARTAS_POR_MANO

    def pc_debe_pedir(self) -> bool:
        """True si la PC todavía quiere otra carta."""
        if self.estado is not Estado.TURNO_PC:
            return False
        contexto = contexto_de(self.mano_pc, self.mano_jugador, es_banca=self.banca is Rol.PC)
        return self._estrategia_pc(contexto)

    # --- Acciones ------------------------------------------------------------

    def cambiar_estrategia(self, estrategia: Estrategia) -> None:
        """Cambia el nivel de juego de la PC. Solo entre rondas."""
        self._exigir(Estado.ESPERANDO_REPARTO)
        self._estrategia_pc = estrategia

    def apostar(self, cantidad: int) -> None:
        """Fija la apuesta de la ronda. Solo antes de repartir."""
        self._exigir(Estado.ESPERANDO_REPARTO)
        if cantidad < APUESTA_MINIMA:
            raise ApuestaInvalida(f"La apuesta mínima es {APUESTA_MINIMA}")
        if cantidad > self.apuesta_maxima:
            raise ApuestaInvalida(
                f"No se puede apostar {cantidad}: el máximo jugable es {self.apuesta_maxima}"
            )
        self.apuesta = cantidad

    def repartir(self) -> None:
        """Baraja un mazo nuevo y reparte dos cartas a cada mano."""
        self._exigir(Estado.ESPERANDO_REPARTO)
        self._reiniciar_ronda()
        for _ in range(CARTAS_INICIALES):
            self.mano_jugador.append(self._robar())
            self.mano_pc.append(self._robar())
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
        """El jugador se planta y pasa el turno a la PC."""
        self._exigir(Estado.TURNO_JUGADOR)
        self.estado = Estado.TURNO_PC

    def pc_pide(self) -> Carta:
        """La PC toma una carta. Llamar solo si `pc_debe_pedir()`."""
        self._exigir(Estado.TURNO_PC)
        if not self.pc_debe_pedir():
            raise EstadoInvalido("La PC no quiere más cartas")
        carta = self._robar()
        self.mano_pc.append(carta)
        return carta

    def resolver_ronda(self) -> ResultadoRonda:
        """Cierra la ronda: mueve las fichas, rota la banca y devuelve el resumen."""
        self._exigir(Estado.TURNO_PC)

        resultado = resolver(self.mano_jugador, self.mano_pc)
        ganador = ganador_de_ronda(resultado, self.banca)
        perdedor = ganador.rival

        # La apuesta nunca supera las fichas de ninguno de los dos, asi que
        # esto no puede dejar a nadie en negativo.
        self.fichas[ganador] += self.apuesta
        self.fichas[perdedor] -= self.apuesta

        banca_previa = self.banca
        self.banca = siguiente_banca(ganador)

        terminada = self.fichas[perdedor] <= 0
        self.estado = Estado.PARTIDA_TERMINADA if terminada else Estado.RONDA_TERMINADA

        return ResultadoRonda(
            resultado=resultado,
            ganador=ganador,
            banca=banca_previa,
            banca_siguiente=self.banca,
            apuesta=self.apuesta,
            puntaje_jugador=self.puntaje_jugador,
            puntaje_pc=self.puntaje_pc,
            fichas_jugador=self.fichas[Rol.JUGADOR],
            fichas_pc=self.fichas[Rol.PC],
            partida_terminada=terminada,
            gano_el_jugador=terminada and self.fichas[Rol.JUGADOR] > 0,
        )

    def nueva_ronda(self) -> None:
        """Prepara la siguiente ronda conservando fichas y banca."""
        self._exigir(Estado.RONDA_TERMINADA)
        # Tras perder fichas, la apuesta anterior puede haber quedado fuera de
        # rango: se recorta al maximo jugable.
        self.apuesta = min(self.apuesta, self.apuesta_maxima)
        self.estado = Estado.ESPERANDO_REPARTO

    def reiniciar(self) -> None:
        """Vuelve todo al estado inicial para empezar una partida nueva."""
        self.fichas: dict[Rol, int] = {
            Rol.JUGADOR: self.fichas_iniciales,
            Rol.PC: self.fichas_iniciales,
        }
        self.banca = self.banca_inicial
        self.apuesta = min(APUESTA_INICIAL, self.apuesta_maxima)
        self._reiniciar_ronda()
        self.estado = Estado.ESPERANDO_REPARTO

    # --- Internos ------------------------------------------------------------

    def _reiniciar_ronda(self) -> None:
        # Mazo nuevo cada ronda: con 40 cartas y 6 como máximo por ronda nunca
        # se agota, pero además evita arrastrar cartas ya vistas.
        self.mazo: list[Carta] = crear_mazo_barajado(self._rng)
        self.mano_jugador: list[Carta] = []
        self.mano_pc: list[Carta] = []

    def _robar(self) -> Carta:
        if not self.mazo:
            raise EstadoInvalido("El mazo se quedó sin cartas")
        return self.mazo.pop()

    def _exigir(self, esperado: Estado) -> None:
        if self.estado is not esperado:
            raise EstadoInvalido(
                f"Se esperaba estado {esperado.name}, pero la partida está en {self.estado.name}"
            )
