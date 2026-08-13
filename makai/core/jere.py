"""Maka'i Jere: la variante de cuatro o más, sin banca y con pozo al centro.

Se diferencia del Maka'i de a dos en tres cosas, y por eso vive en su propio
módulo en lugar de generalizar `Partida`: allá todo gira alrededor de la banca,
que acá no existe.

- **No hay banca.** Nadie tiene ventaja en el empate.
- **Pozo al centro.** Todos ponen lo mismo y el de mayor puntaje se lo lleva
  entero.
- **Empate a desempate.** Los empatados reciben dos cartas nuevas y se define
  ahí, sin opción a una tercera. El pozo se resuelve en la ronda: nunca se
  arrastra a la siguiente.

Cada jugador, cuando le toca, canta su decisión y con eso obliga al siguiente a
declarar: `carta y pie` si pide, `planto y pie` si se planta.

Comparte la baraja y el puntaje con el resto del juego (`cartas`, `reglas`).
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto

from .cartas import Carta, crear_mazo_barajado
from .estrategia import Estrategia, contexto_de, estrategia_umbral
from .reglas import MAX_CARTAS_POR_MANO, calcular_puntaje

#: Cartas que recibe cada jugador al repartir.
CARTAS_INICIALES = 2

#: Jere se juega de cuatro para arriba.
MINIMO_JUGADORES = 4
MAXIMO_JUGADORES = 6

FICHAS_INICIALES = 100
APUESTA_MINIMA = 1
APUESTA_INICIAL = 5

#: Tope de desempates encadenados. Es defensivo: con dos cartas de una baraja
#: barajada de nuevo, empatar muchas veces seguidas es practicamente imposible.
MAX_DESEMPATES = 50


class Estado(Enum):
    ESPERANDO_REPARTO = auto()
    DECLARANDO = auto()
    DESEMPATANDO = auto()
    RONDA_TERMINADA = auto()
    PARTIDA_TERMINADA = auto()


class EstadoInvalido(RuntimeError):
    """Se intentó una acción que no corresponde al estado actual."""


class ApuestaInvalida(ValueError):
    """La apuesta pedida no es jugable con las fichas disponibles."""


class Declaracion(Enum):
    """Lo que canta un jugador cuando le toca."""

    CARTA = "carta y pie"
    PLANTO = "planto y pie"


@dataclass
class Jugador:
    indice: int
    nombre: str
    es_humano: bool
    fichas: int
    mano: list[Carta] = field(default_factory=list)
    declaracion: Declaracion | None = None

    @property
    def puntaje(self) -> float:
        return calcular_puntaje(self.mano)

    @property
    def sigue_en_partida(self) -> bool:
        return self.fichas > 0

    @property
    def puede_pedir(self) -> bool:
        return len(self.mano) < MAX_CARTAS_POR_MANO


@dataclass(frozen=True)
class ResultadoRonda:
    ganador: Jugador
    pozo: int
    hubo_desempate: bool
    empatados: tuple[str, ...]
    partida_terminada: bool


class PartidaJere:
    """Una partida de Maka'i Jere.

    El reparto rota: la mano pasa al siguiente en cada ronda, para que la
    ventaja de declarar último no quede siempre del mismo lado.
    """

    def __init__(
        self,
        nombres: Sequence[str],
        fichas_iniciales: int = FICHAS_INICIALES,
        apuesta: int = APUESTA_INICIAL,
        indice_humano: int = 0,
        rng: random.Random | None = None,
        estrategia_pc: Estrategia = estrategia_umbral,
    ) -> None:
        if not MINIMO_JUGADORES <= len(nombres) <= MAXIMO_JUGADORES:
            raise ValueError(
                f"Jere se juega entre {MINIMO_JUGADORES} y {MAXIMO_JUGADORES} jugadores, "
                f"no {len(nombres)}"
            )
        if fichas_iniciales < APUESTA_MINIMA:
            raise ValueError(f"Hacen falta al menos {APUESTA_MINIMA} fichas para jugar")

        self.nombres = tuple(nombres)
        self.fichas_iniciales = fichas_iniciales
        self.indice_humano = indice_humano
        self._rng = rng
        self._estrategia_pc = estrategia_pc
        self.apuesta_inicial = apuesta
        self.reiniciar()

    # --- Consultas -----------------------------------------------------------

    @property
    def humano(self) -> Jugador:
        return self.jugadores[self.indice_humano]

    @property
    def activos(self) -> list[Jugador]:
        """Los que todavía tienen fichas."""
        return [j for j in self.jugadores if j.sigue_en_partida]

    @property
    def apuesta_maxima(self) -> int:
        """Todos ponen lo mismo, así que manda el que menos fichas tiene."""
        return min((j.fichas for j in self.activos), default=0)

    @property
    def en_ronda(self) -> list[Jugador]:
        """Quiénes están jugando la mano actual."""
        return [j for j in self.jugadores if j.indice in self._en_ronda]

    @property
    def turno(self) -> Jugador | None:
        """A quién le toca declarar, o None si ya declararon todos."""
        if self.estado is not Estado.DECLARANDO or self._turno is None:
            return None
        return self.jugadores[self._turno]

    @property
    def es_turno_del_humano(self) -> bool:
        turno = self.turno
        return turno is not None and turno.es_humano

    # --- Acciones ------------------------------------------------------------

    def apostar(self, cantidad: int) -> None:
        """Fija lo que pone cada uno. Solo antes de repartir."""
        self._exigir(Estado.ESPERANDO_REPARTO)
        if cantidad < APUESTA_MINIMA:
            raise ApuestaInvalida(f"La apuesta mínima es {APUESTA_MINIMA}")
        if cantidad > self.apuesta_maxima:
            raise ApuestaInvalida(
                f"No se puede apostar {cantidad}: el máximo jugable es {self.apuesta_maxima}"
            )
        self.apuesta = cantidad

    def repartir(self) -> None:
        """Cobra la apuesta a todos, arma el pozo y da dos cartas a cada uno."""
        self._exigir(Estado.ESPERANDO_REPARTO)

        activos = self.activos
        self.mazo = crear_mazo_barajado(self._rng)
        self._en_ronda = {j.indice for j in activos}
        self.pozo = 0

        for jugador in activos:
            jugador.mano = []
            jugador.declaracion = None
            jugador.fichas -= self.apuesta
            self.pozo += self.apuesta

        for _ in range(CARTAS_INICIALES):
            for jugador in activos:
                jugador.mano.append(self._robar())

        # El orden de declaración arranca por la mano y sigue por la mesa. Sin
        # esto la rotación no tendría efecto y declararía siempre el mismo
        # primero.
        total = len(self.jugadores)
        self._orden = sorted((j.indice for j in activos), key=lambda i: (i - self._mano) % total)
        self._turno = self._orden[0]
        self.estado = Estado.DECLARANDO

    def declarar(self, declaracion: Declaracion) -> Jugador:
        """El jugador de turno canta, y el turno pasa al siguiente."""
        self._exigir(Estado.DECLARANDO)
        jugador = self.jugadores[self._turno]

        if declaracion is Declaracion.CARTA:
            if not jugador.puede_pedir:
                raise EstadoInvalido(
                    f"{jugador.nombre} ya tiene el máximo de {MAX_CARTAS_POR_MANO} cartas"
                )
            jugador.mano.append(self._robar())

        jugador.declaracion = declaracion
        self._avanzar_turno()
        return jugador

    def declaracion_de_la_pc(self) -> Declaracion:
        """Qué cantaría la PC en el turno actual, según su estrategia."""
        self._exigir(Estado.DECLARANDO)
        jugador = self.jugadores[self._turno]
        if jugador.es_humano:
            raise EstadoInvalido(f"El turno es de {jugador.nombre}, que es el jugador")

        if not jugador.puede_pedir:
            return Declaracion.PLANTO

        # Sin banca, la referencia es la mejor mano visible de los rivales.
        rivales = [o for o in self.en_ronda if o is not jugador]
        mejor = max(rivales, key=lambda o: o.puntaje).mano if rivales else []
        contexto = contexto_de(jugador.mano, mejor, es_banca=False)
        return Declaracion.CARTA if self._estrategia_pc(contexto) else Declaracion.PLANTO

    def resolver_ronda(self) -> ResultadoRonda:
        """Compara las manos y entrega el pozo. Desempata si hace falta."""
        if self.estado is not Estado.DECLARANDO or self._turno is not None:
            raise EstadoInvalido("Todavía faltan jugadores por declarar")

        candidatos = self.en_ronda
        empatados_iniciales = self._mejores(candidatos)
        hubo_desempate = len(empatados_iniciales) > 1
        nombres_empatados = tuple(j.nombre for j in empatados_iniciales)

        ganador = self._definir(empatados_iniciales)
        ganador.fichas += self.pozo

        terminada = len([j for j in self.jugadores if j.sigue_en_partida]) <= 1
        self.estado = Estado.PARTIDA_TERMINADA if terminada else Estado.RONDA_TERMINADA

        return ResultadoRonda(
            ganador=ganador,
            pozo=self.pozo,
            hubo_desempate=hubo_desempate,
            empatados=nombres_empatados,
            partida_terminada=terminada,
        )

    def nueva_ronda(self) -> None:
        """Prepara la siguiente mano y pasa el reparto al de al lado."""
        self._exigir(Estado.RONDA_TERMINADA)
        self.apuesta = min(self.apuesta, self.apuesta_maxima)
        self._rotar_mano()
        self.estado = Estado.ESPERANDO_REPARTO

    def reiniciar(self) -> None:
        self.jugadores = [
            Jugador(
                indice=i,
                nombre=nombre,
                es_humano=(i == self.indice_humano),
                fichas=self.fichas_iniciales,
            )
            for i, nombre in enumerate(self.nombres)
        ]
        self.pozo = 0
        self.apuesta = min(self.apuesta_inicial, self.apuesta_maxima)
        self.mazo: list[Carta] = []
        self._en_ronda: set[int] = set()
        self._orden: list[int] = []
        self._turno: int | None = None
        self._mano = 0
        self.estado = Estado.ESPERANDO_REPARTO

    # --- Internos ------------------------------------------------------------

    def _mejores(self, candidatos: Sequence[Jugador]) -> list[Jugador]:
        tope = max(j.puntaje for j in candidatos)
        return [j for j in candidatos if j.puntaje == tope]

    def _definir(self, empatados: list[Jugador]) -> Jugador:
        """Resuelve el empate repartiendo de nuevo, sin tercera carta.

        El pozo se define sí o sí en esta ronda: no se arrastra.
        """
        for _ in range(MAX_DESEMPATES):
            if len(empatados) == 1:
                return empatados[0]

            self.estado = Estado.DESEMPATANDO
            self.mazo = crear_mazo_barajado(self._rng)
            for jugador in empatados:
                jugador.mano = [self._robar() for _ in range(CARTAS_INICIALES)]
            empatados = self._mejores(empatados)

        # Inalcanzable en la práctica; evita un bucle infinito si algo cambia.
        return empatados[0]

    def _avanzar_turno(self) -> None:
        posicion = self._orden.index(self._turno)
        self._turno = self._orden[posicion + 1] if posicion + 1 < len(self._orden) else None

    def _rotar_mano(self) -> None:
        self._mano = (self._mano + 1) % len(self.jugadores)

    def _robar(self) -> Carta:
        if not self.mazo:
            raise EstadoInvalido("El mazo se quedó sin cartas")
        return self.mazo.pop()

    def _exigir(self, esperado: Estado) -> None:
        if self.estado is not esperado:
            raise EstadoInvalido(
                f"Se esperaba estado {esperado.name}, pero la partida está en {self.estado.name}"
            )
