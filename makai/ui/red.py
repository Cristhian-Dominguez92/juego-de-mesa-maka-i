"""Salas de una partida en red (LAN o internet).

Vive en `makai/ui` y no en `makai/core` porque coordina sesiones en vivo
—quién está conectado, a quién avisarle que redibuje su pantalla— y no
reglas del juego. La partida en sí la sigue llevando `Partida`, intacta.

No depende de `flet`: cada sesión registra un callback (`notificar`, sin
argumentos) al conectarse, y `Sala` no necesita saber nada de cómo está
hecho ese callback. Eso la mantiene testeable sin levantar una página, igual
que `makai/ui/preferencias.py` y `makai/ui/estadisticas.py`.

Las salas viven en memoria del proceso: se pierden si el servidor se
reinicia (o, en un hosting con capa gratuita, si se duerme por inactividad
y vuelve a arrancar). Alcanza mientras el servidor sea un único proceso
long-lived, que es el caso tanto en LAN como en el despliegue a internet
(ver `asgi.py`). Expuesta a cualquiera en internet y no solo a la LAN de
casa, además hace falta encarecer el acceso: por eso el código es más largo
y `unirse` limita los intentos fallidos por identificador (ver
`DemasiadosIntentos`), y las salas abandonadas expiran solas (ver
`Sala.vencida`).
"""

from __future__ import annotations

import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from makai.core import Estrategia, Partida, Rol, estrategia_umbral

#: Sin O/0 ni I/1: se confunden a simple vista al dictar el código en voz alta.
_ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
#: 6 caracteres: cómodo de tipear a mano y, ya expuesto a internet (no solo a
#: la LAN de casa), bastante más caro de adivinar por fuerza bruta que 4.
LARGO_CODIGO = 6

#: Cuántos códigos inexistentes tolera un mismo identificador (en la
#: práctica, la IP del cliente) antes de bloquearlo un rato.
INTENTOS_MAXIMOS = 8
VENTANA_INTENTOS_SEGUNDOS = 60.0

#: Una sala sin actividad este tiempo se considera abandonada.
TIEMPO_EXPIRACION_SEGUNDOS = 30 * 60.0


class SalaLlena(RuntimeError):
    """El asiento del invitado ya está ocupado."""


class SalaInexistente(KeyError):
    """No hay ninguna sala activa con ese código."""


class DemasiadosIntentos(RuntimeError):
    """El identificador superó el límite de códigos inexistentes probados."""


@dataclass
class Sala:
    """Una partida compartida entre dos sesiones: anfitrión y su rival.

    El anfitrión ocupa `Rol.JUGADOR`; quien se une con el código, `Rol.PC`
    (reaprovechando los roles que ya distingue `Partida`, no porque ese lado
    lo juegue una máquina).
    """

    codigo: str
    partida: Partida
    _notificar: dict[Rol, Callable[[], Awaitable[None]]] = field(default_factory=dict)
    #: Último momento con actividad real (alguien se conectó o jugó). Sirve
    #: solo para detectar salas abandonadas, no para la lógica del juego.
    #: `lambda: time.monotonic()` y no `time.monotonic` a secas: así un test
    #: que parchea `time.monotonic` también cambia este default (el default
    #: factory se resuelve recién al construir la `Sala`, no al importar el
    #: módulo).
    ultima_actividad: float = field(default_factory=lambda: time.monotonic())

    @property
    def completa(self) -> bool:
        return len(self._notificar) == 2

    @property
    def vencida(self) -> bool:
        return time.monotonic() - self.ultima_actividad > TIEMPO_EXPIRACION_SEGUNDOS

    def conectado(self, rol: Rol) -> bool:
        return rol in self._notificar

    def marcar_conectado(self, rol: Rol, notificar: Callable[[], Awaitable[None]]) -> None:
        """Registra el callback de la sesión que ocupa `rol`.

        Es una corrutina (no una función simple) porque el primer aviso que
        recibe el anfitrión —cuando se une el invitado— no es un simple
        redibujado: es la transición completa de "esperando" a la pantalla
        de juego, que sí necesita `await`.
        """
        self._notificar[rol] = notificar
        self.ultima_actividad = time.monotonic()

    def desconectar(self, rol: Rol) -> None:
        self._notificar.pop(rol, None)

    async def avisar_al_otro(self, rol_que_actuo: Rol) -> None:
        """Le avisa al asiento contrario que algo cambió y debe reaccionar."""
        self.ultima_actividad = time.monotonic()
        notificar = self._notificar.get(rol_que_actuo.rival)
        if notificar is not None:
            await notificar()


_SALAS: dict[str, Sala] = {}

#: Intentos fallidos recientes (códigos inexistentes) por identificador.
_intentos_fallidos: dict[str, list[float]] = {}


def generar_codigo() -> str:
    """Código corto y único entre las salas activas en este momento."""
    while True:
        codigo = "".join(random.choices(_ALFABETO_CODIGO, k=LARGO_CODIGO))
        if codigo not in _SALAS:
            return codigo


def _purgar_salas_vencidas() -> None:
    vencidas = [codigo for codigo, sala in _SALAS.items() if sala.vencida]
    for codigo in vencidas:
        del _SALAS[codigo]


def _intentos_recientes(identificador: str) -> list[float]:
    ahora = time.monotonic()
    limite = VENTANA_INTENTOS_SEGUNDOS
    recientes = [t for t in _intentos_fallidos.get(identificador, []) if ahora - t < limite]
    if recientes:
        _intentos_fallidos[identificador] = recientes
    else:
        _intentos_fallidos.pop(identificador, None)
    return recientes


def crear_sala(estrategia_pc: Estrategia = estrategia_umbral) -> Sala:
    """Arranca una sala nueva con una `Partida` vacía y la registra.

    `Partida` exige una estrategia en el constructor aunque acá no se vaya a
    usar (el lado 'PC' lo controla una persona real vía `pedir_pc`): se deja
    el default en vez de bifurcar la clase para el caso en red.

    De paso, barre las salas abandonadas (ver `Sala.vencida`) — así un
    servidor corriendo días no acumula salas fantasma en memoria sin
    necesitar una tarea de fondo aparte.
    """
    _purgar_salas_vencidas()
    codigo = generar_codigo()
    sala = Sala(codigo=codigo, partida=Partida(estrategia_pc=estrategia_pc))
    _SALAS[codigo] = sala
    return sala


def unirse(codigo: str, identificador: str = "") -> Sala:
    """Busca una sala por código para ocupar el asiento del invitado.

    `identificador` es opcional (en la práctica, la IP del cliente) y sirve
    solo para limitar cuántos códigos inexistentes se pueden probar
    seguidos — sin identificador, el límite no se aplica (así no rompe
    nada en escritorio o en los tests con un `Page` de mentira).

    Lanza `DemasiadosIntentos` si ese identificador ya gastó sus intentos,
    `SalaInexistente` si el código no corresponde a ninguna sala activa, o
    `SalaLlena` si el asiento del invitado ya está ocupado.
    """
    codigo = codigo.strip().upper()
    if identificador and len(_intentos_recientes(identificador)) >= INTENTOS_MAXIMOS:
        raise DemasiadosIntentos(identificador)

    sala = _SALAS.get(codigo)
    if sala is None:
        if identificador:
            _intentos_fallidos.setdefault(identificador, []).append(time.monotonic())
        raise SalaInexistente(codigo)
    if sala.conectado(Rol.PC):
        raise SalaLlena(codigo)
    return sala


def cerrar_sala(codigo: str) -> None:
    """Saca la sala del registro. No falla si ya no está."""
    _SALAS.pop(codigo, None)
