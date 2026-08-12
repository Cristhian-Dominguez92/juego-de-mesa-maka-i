"""Audio del juego, sobre el paquete flet-audio.

Reemplaza a pygame, que no tiene wheel para Android y dejaba el juego mudo en
el APK.

**Por qué `flet_audio` y no `ft.Audio`.** El control incorporado está obsoleto
desde flet 0.26 y su parte Flutter ya no viene en el paquete base: en el APK se
renderizaba como un recuadro rojo con "Unknown control: audio", que además
tapaba media pantalla. El paquete `flet-audio` trae el plugin Flutter, y
`flet build` lo registra al encontrarlo entre las dependencias del proyecto.
Por eso tiene que estar en `[project].dependencies` de pyproject.toml, no solo
instalado en el entorno.

`ReleaseMode` no se exporta en `flet_audio/__init__.py`: hay que importarlo del
submódulo.
"""

from __future__ import annotations

import os

import flet as ft
from flet_audio import Audio
from flet_audio.audio import ReleaseMode

#: Clave en client_storage donde se recuerda si el jugador silenció el juego.
CLAVE_SILENCIO = "makai.audio.silenciado"

VOLUMEN_MUSICA = 0.3
VOLUMEN_EFECTOS = 0.8


#: Para cada sonido, los nombres aceptados en orden de preferencia. El .wav de
#: la música lo genera `tools/generar_musica.py`; un .mp3 puesto a mano tiene
#: prioridad, para poder reemplazar la música sin tocar código.
CANDIDATOS = {
    "musica_src": ("background_music.mp3", "background_music.wav"),
    "victoria_src": ("victoria.mp3", "victoria.wav"),
}


def descubrir_fuentes(assets_dir: str, recursos: str) -> dict[str, str | None]:
    """Busca en disco los archivos de audio y devuelve sus rutas de asset.

    Las rutas devueltas son relativas a `assets_dir`, que es como las resuelve
    Flet. Un valor None significa que no hay archivo y que ese sonido
    simplemente no va a sonar.
    """
    fuentes: dict[str, str | None] = {}
    for nombre, nombres_posibles in CANDIDATOS.items():
        fuentes[nombre] = None
        for archivo in nombres_posibles:
            if os.path.exists(os.path.join(assets_dir, recursos, archivo)):
                fuentes[nombre] = f"{recursos}/{archivo}"
                break
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
            Audio(
                src=musica_src,
                autoplay=False,
                volume=0.0 if self.silenciado else VOLUMEN_MUSICA,
                release_mode=ReleaseMode.LOOP,
            )
            if musica_src
            else None
        )
        # STOP y no RELEASE: con RELEASE, audioplayers libera el reproductor y
        # descarta la fuente al terminar la reproducción, y el "play" del plugin
        # es un `seek(0)` seguido de `resume()`, que sobre un reproductor
        # liberado no hace nada. Con STOP el sonido queda listo para volver a
        # dispararse.
        self.victoria = (
            Audio(
                src=victoria_src,
                autoplay=False,
                volume=0.0 if self.silenciado else VOLUMEN_EFECTOS,
                release_mode=ReleaseMode.STOP,
            )
            if victoria_src
            else None
        )

        for control in self._controles():
            page.overlay.append(control)

    def registrar(self) -> None:
        """Vuelve a poner los controles en el overlay y los sincroniza.

        `page.clean()` recorre todos los hijos de la página —el overlay
        incluido— y los da de baja del lado del cliente, aunque la lista de
        Python siga teniéndolos. Hay que llamar a esto después de cada cambio
        de pantalla, antes de reproducir nada.
        """
        for control in self._controles():
            if control not in self.page.overlay:
                self.page.overlay.append(control)
        self._musica_sonando = False
        self._intentar(self.page.update)

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

    def _controles(self) -> list[Audio]:
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
        """Ejecuta una acción de audio sin dejar que un fallo tumbe el juego.

        Un archivo faltante o un dispositivo sin salida de sonido no son
        motivo para cortar la partida, pero **sí se informan**: cuando esto
        callaba por completo, que el sonido de victoria no sonara en el APK no
        dejaba ningún rastro que permitiera diagnosticarlo.
        """
        try:
            accion()
        except Exception as e:
            print(f"[audio] fallo {getattr(accion, '__name__', accion)}: {e!r}")
