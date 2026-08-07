"""Audio del juego sobre ft.Audio.

Reemplaza a pygame, que no tiene wheel para Android y dejaba el juego mudo en
el APK. ft.Audio viene incluido en flet 0.28.3 (no requiere paquete extra) y se
empaqueta junto con la aplicación.

`ReleaseMode` no está exportado como `ft.ReleaseMode`: hay que importarlo desde
`flet.core.audio`.

MIGRACIÓN PENDIENTE: `ft.Audio` está marcado como obsoleto desde flet 0.26 y
desaparece en 0.29, cuando pasa al paquete `flet-audio`. En 0.28.3 sigue siendo
la única opción: `flet-audio` no publica versiones 0.28.x (salta de 0.1.0 a
0.80.0, ya para la línea 1.0). Al subir de versión de Flet hay que cambiar a
`import flet_audio` y agregar el paquete a las dependencias de pyproject.toml
para que `flet build` incluya el plugin.
"""

from __future__ import annotations

import os

import flet as ft
from flet.core.audio import ReleaseMode

#: Clave en client_storage donde se recuerda si el jugador silenció el juego.
CLAVE_SILENCIO = "makai.audio.silenciado"

VOLUMEN_MUSICA = 0.3
VOLUMEN_EFECTOS = 0.8


def descubrir_fuentes(assets_dir: str, recursos: str) -> dict[str, str | None]:
    """Busca en disco los archivos de audio y devuelve sus rutas de asset.

    Las rutas devueltas son relativas a `assets_dir`, que es como las resuelve
    Flet. Un valor None significa que el archivo no está y que ese sonido
    simplemente no va a sonar.

    La música de fondo no viene en el repositorio por licencia (ver CREDITS.md):
    hay que dejar un archivo con licencia libre en esa ruta.
    """
    archivos = {
        "musica_src": "background_music.mp3",
        "victoria_src": "victoria.mp3",
    }
    fuentes: dict[str, str | None] = {}
    for nombre, archivo in archivos.items():
        existe = os.path.exists(os.path.join(assets_dir, recursos, archivo))
        fuentes[nombre] = f"{recursos}/{archivo}" if existe else None
    return fuentes


class GestorAudio:
    """Controla la música de fondo y los efectos, con silencio persistente."""

    def __init__(
        self,
        page: ft.Page,
        musica_src: str | None = None,
        victoria_src: str | None = None,
    ) -> None:
        self.page = page
        self.silenciado = self._leer_preferencia()
        self._musica_sonando = False

        self.musica = (
            ft.Audio(
                src=musica_src,
                autoplay=False,
                volume=0.0 if self.silenciado else VOLUMEN_MUSICA,
                release_mode=ReleaseMode.LOOP,
            )
            if musica_src
            else None
        )
        self.victoria = (
            ft.Audio(
                src=victoria_src,
                autoplay=False,
                volume=0.0 if self.silenciado else VOLUMEN_EFECTOS,
                release_mode=ReleaseMode.RELEASE,
            )
            if victoria_src
            else None
        )

        for control in self._controles():
            page.overlay.append(control)

    # --- Reproducción --------------------------------------------------------

    def iniciar_musica(self) -> None:
        """Arranca la música de fondo en bucle. Idempotente."""
        if self.musica is None or self._musica_sonando:
            return
        self._intentar(self.musica.play)
        self._musica_sonando = True

    def sonar_victoria(self) -> None:
        if self.victoria is None or self.silenciado:
            return
        self._intentar(self.victoria.play)

    # --- Silencio ------------------------------------------------------------

    def alternar_silencio(self) -> bool:
        """Invierte el silencio, lo persiste y devuelve el estado nuevo."""
        self.silenciado = not self.silenciado
        self._aplicar_volumen()
        self._guardar_preferencia()
        return self.silenciado

    def _aplicar_volumen(self) -> None:
        if self.musica is not None:
            self.musica.volume = 0.0 if self.silenciado else VOLUMEN_MUSICA
            self._intentar(self.musica.update)
        if self.victoria is not None:
            self.victoria.volume = 0.0 if self.silenciado else VOLUMEN_EFECTOS
            self._intentar(self.victoria.update)

    # --- Internos ------------------------------------------------------------

    def _controles(self) -> list[ft.Audio]:
        return [c for c in (self.musica, self.victoria) if c is not None]

    def _leer_preferencia(self) -> bool:
        # client_storage no está disponible en todos los contextos (por ejemplo
        # durante los tests): la preferencia es opcional, nunca crítica.
        try:
            return bool(self.page.client_storage.get(CLAVE_SILENCIO))
        except Exception:
            return False

    def _guardar_preferencia(self) -> None:
        try:
            self.page.client_storage.set(CLAVE_SILENCIO, self.silenciado)
        except Exception:
            pass

    @staticmethod
    def _intentar(accion) -> None:
        """Ejecuta una acción de audio ignorando fallos de reproducción.

        Un archivo faltante o un dispositivo sin salida de sonido no deben
        tumbar el juego.
        """
        try:
            accion()
        except Exception:
            pass
