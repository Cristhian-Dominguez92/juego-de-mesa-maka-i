"""Estadísticas persistentes del jugador.

Se guardan en `client_storage` de Flet. El almacenamiento se inyecta, así que
la lógica se puede testear con un dict sin levantar una página.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

CLAVE = "makai.estadisticas"


class Almacenamiento(Protocol):
    def get(self, clave: str) -> Any: ...

    def set(self, clave: str, valor: Any) -> Any: ...


@dataclass
class Estadisticas:
    """Acumulado histórico. Todos los contadores son monótonos salvo la racha."""

    partidas_jugadas: int = 0
    partidas_ganadas: int = 0
    rondas_jugadas: int = 0
    rondas_ganadas: int = 0
    racha_actual: int = 0
    mejor_racha: int = 0
    fichas_maximas: int = 0

    @property
    def partidas_perdidas(self) -> int:
        return self.partidas_jugadas - self.partidas_ganadas

    @property
    def porcentaje_rondas(self) -> float:
        if not self.rondas_jugadas:
            return 0.0
        return round(100 * self.rondas_ganadas / self.rondas_jugadas, 1)

    def registrar_ronda(self, gano: bool, fichas_jugador: int) -> None:
        self.rondas_jugadas += 1
        if gano:
            self.rondas_ganadas += 1
            self.racha_actual += 1
            self.mejor_racha = max(self.mejor_racha, self.racha_actual)
        else:
            self.racha_actual = 0
        self.fichas_maximas = max(self.fichas_maximas, fichas_jugador)

    def registrar_partida(self, gano: bool) -> None:
        self.partidas_jugadas += 1
        if gano:
            self.partidas_ganadas += 1


def cargar(almacenamiento: Almacenamiento) -> Estadisticas:
    """Lee las estadísticas guardadas.

    Cualquier problema (sin almacenamiento, datos corruptos, campos de una
    versión anterior) devuelve estadísticas en cero: no vale la pena tumbar el
    juego por esto.
    """
    try:
        crudo = almacenamiento.get(CLAVE)
    except Exception:
        return Estadisticas()

    if not isinstance(crudo, dict):
        return Estadisticas()

    campos = {f for f in Estadisticas().__dict__}
    conocidos = {k: v for k, v in crudo.items() if k in campos and isinstance(v, int)}
    try:
        return Estadisticas(**conocidos)
    except TypeError:
        return Estadisticas()


def guardar(almacenamiento: Almacenamiento, estadisticas: Estadisticas) -> None:
    try:
        almacenamiento.set(CLAVE, asdict(estadisticas))
    except Exception:
        pass
