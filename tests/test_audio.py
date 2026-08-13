"""Tests del gestor de audio.

Verifican la lógica (silencio, persistencia, descubrimiento de archivos), no la
reproducción en sí: sin una página real de Flet no hay dispositivo de sonido.
"""

import pytest

pytest.importorskip("flet")

from makai.ui.audio import (  # noqa: E402
    CLAVE_SILENCIO,
    VOLUMEN_EFECTOS,
    VOLUMEN_MUSICA,
    GestorAudio,
    descubrir_fuentes,
)


class ClientStorageStub:
    def __init__(self, datos=None):
        self.datos = dict(datos or {})

    def get(self, clave):
        return self.datos.get(clave)

    def set(self, clave, valor):
        self.datos[clave] = valor
        return True


class PageStub:
    def __init__(self, almacenamiento=None):
        self.overlay = []
        self.client_storage = almacenamiento or ClientStorageStub()


@pytest.fixture
def gestor():
    return GestorAudio(
        PageStub(),
        musica_src="Recursos/background_music.mp3",
        victoria_src="Recursos/victoria.mp3",
    )


# --- Descubrimiento de archivos ----------------------------------------------


def test_descubrir_fuentes_encuentra_el_sonido_de_victoria(tmp_path):
    recursos = tmp_path / "Recursos"
    recursos.mkdir()
    (recursos / "victoria.mp3").write_bytes(b"")

    fuentes = descubrir_fuentes(str(tmp_path), "Recursos")
    assert fuentes["victoria_src"] == "Recursos/victoria.mp3"


def test_un_archivo_ausente_da_none(tmp_path):
    (tmp_path / "Recursos").mkdir()
    fuentes = descubrir_fuentes(str(tmp_path), "Recursos")
    assert fuentes["musica_src"] is None
    assert fuentes["victoria_src"] is None


def test_las_rutas_son_relativas_al_assets_dir(tmp_path):
    """Flet resuelve el src contra assets_dir, no contra el disco."""
    recursos = tmp_path / "Recursos"
    recursos.mkdir()
    (recursos / "background_music.mp3").write_bytes(b"")

    fuentes = descubrir_fuentes(str(tmp_path), "Recursos")
    assert not fuentes["musica_src"].startswith(str(tmp_path))
    assert fuentes["musica_src"] == "Recursos/background_music.mp3"


def test_el_proyecto_real_trae_su_propia_musica():
    """La musica la genera tools/generar_musica.py (ver CREDITS.md)."""
    fuentes = descubrir_fuentes("assets", "Recursos")
    assert fuentes["musica_src"] == "Recursos/background_music.wav"
    assert fuentes["victoria_src"] == "Recursos/victoria.mp3"


def test_se_prefiere_un_mp3_puesto_a_mano(tmp_path):
    """Poder reemplazar la musica sin tocar codigo."""
    recursos = tmp_path / "Recursos"
    recursos.mkdir()
    (recursos / "background_music.wav").write_bytes(b"")
    (recursos / "background_music.mp3").write_bytes(b"")

    fuentes = descubrir_fuentes(str(tmp_path), "Recursos")
    assert fuentes["musica_src"] == "Recursos/background_music.mp3"


# --- Construccion -------------------------------------------------------------


def test_los_controles_se_registran_en_el_overlay(gestor):
    assert len(gestor.page.overlay) == 2


def test_sin_archivos_no_se_crea_ningun_control():
    g = GestorAudio(PageStub())
    assert g.musica is None
    assert g.victoria is None
    assert g.page.overlay == []


# El getter de release_mode devuelve el string crudo que Flet manda al cliente,
# no el miembro del enum, asi que se compara contra .value.


def test_la_musica_se_configura_en_bucle(gestor):
    from flet_audio.audio import ReleaseMode

    assert gestor.musica.release_mode == ReleaseMode.LOOP.value


def test_el_efecto_de_victoria_queda_listo_para_repetirse(gestor):
    """Regresion: con RELEASE el sonido de victoria no sonaba en el APK.

    audioplayers libera el reproductor y descarta la fuente al terminar, y el
    "play" del plugin es un seek(0) + resume() que sobre un reproductor
    liberado no hace nada. STOP conserva la fuente.
    """
    from flet_audio.audio import ReleaseMode

    assert gestor.victoria.release_mode == ReleaseMode.STOP.value
    assert gestor.victoria.release_mode != ReleaseMode.RELEASE.value


# --- Silencio -----------------------------------------------------------------


def test_arranca_con_sonido_por_defecto(gestor):
    assert gestor.silenciado is False
    assert gestor.musica.volume == VOLUMEN_MUSICA
    assert gestor.victoria.volume == VOLUMEN_EFECTOS


def test_alternar_silencio_baja_los_volumenes(gestor):
    assert gestor.alternar_silencio() is True
    assert gestor.silenciado is True
    assert gestor.musica.volume == 0.0
    assert gestor.victoria.volume == 0.0


def test_alternar_dos_veces_vuelve_al_volumen_original(gestor):
    gestor.alternar_silencio()
    assert gestor.alternar_silencio() is False
    assert gestor.musica.volume == VOLUMEN_MUSICA
    assert gestor.victoria.volume == VOLUMEN_EFECTOS


def test_el_silencio_se_persiste(gestor):
    gestor.alternar_silencio()
    assert gestor.page.client_storage.get(CLAVE_SILENCIO) is True
    gestor.alternar_silencio()
    assert gestor.page.client_storage.get(CLAVE_SILENCIO) is False


def test_se_respeta_el_silencio_guardado():
    page = PageStub(ClientStorageStub({CLAVE_SILENCIO: True}))
    g = GestorAudio(page, musica_src="a.mp3", victoria_src="b.mp3")
    assert g.silenciado is True
    assert g.musica.volume == 0.0


def test_alternar_silencio_funciona_sin_archivos_de_audio():
    g = GestorAudio(PageStub())
    assert g.alternar_silencio() is True


def test_un_client_storage_roto_no_tumba_el_juego():
    class StorageRoto:
        def get(self, clave):
            raise RuntimeError("sin almacenamiento")

        def set(self, clave, valor):
            raise RuntimeError("sin almacenamiento")

    page = PageStub(StorageRoto())
    g = GestorAudio(page, musica_src="a.mp3")
    assert g.silenciado is False
    assert g.alternar_silencio() is True


# --- Reproduccion -------------------------------------------------------------


def test_iniciar_musica_es_idempotente(gestor):
    """Se llama cada vez que se entra al juego; no debe reiniciar la pista."""
    llamadas = []
    gestor.musica.play = lambda: llamadas.append("play")

    gestor.iniciar_musica()
    gestor.iniciar_musica()
    gestor.iniciar_musica()

    assert llamadas == ["play"]


def test_iniciar_musica_no_falla_sin_archivo():
    GestorAudio(PageStub()).iniciar_musica()


def test_el_sonido_de_victoria_no_suena_si_esta_silenciado(gestor):
    llamadas = []
    gestor.victoria.play = lambda: llamadas.append("play")

    gestor.sonar_victoria()
    gestor.alternar_silencio()
    gestor.sonar_victoria()

    assert llamadas == ["play"], "sono estando silenciado"


def test_un_fallo_de_reproduccion_no_tumba_el_juego(gestor):
    def explotar():
        raise RuntimeError("sin dispositivo de audio")

    gestor.musica.play = explotar
    gestor.victoria.play = explotar

    gestor.iniciar_musica()
    gestor.sonar_victoria()


# --- Registro tras cambiar de pantalla ----------------------------------------
# Regresion: page.clean() recorre todos los hijos de la pagina —el overlay
# incluido— y los da de baja del lado del cliente. Reproducir con el control
# desregistrado no hace nada.


class PageConClean(PageStub):
    def __init__(self):
        super().__init__()
        self.updates = 0

    def clean(self):
        # Imita a Flet: los objetos siguen en la lista de Python.
        pass

    def update(self):
        self.updates += 1


def test_registrar_repone_los_controles_en_el_overlay():
    page = PageConClean()
    g = GestorAudio(page, musica_src="a.mp3", victoria_src="b.mp3")

    page.overlay.clear()  # como si se hubieran perdido
    g.registrar()

    assert len(page.overlay) == 2
    assert g.musica in page.overlay
    assert g.victoria in page.overlay


def test_registrar_no_duplica_controles():
    page = PageConClean()
    g = GestorAudio(page, musica_src="a.mp3", victoria_src="b.mp3")

    g.registrar()
    g.registrar()

    assert len(page.overlay) == 2


def test_registrar_sincroniza_la_pagina():
    page = PageConClean()
    g = GestorAudio(page, musica_src="a.mp3")
    antes = page.updates
    g.registrar()
    assert page.updates > antes


def test_tras_registrar_la_musica_vuelve_a_arrancar():
    """Al cambiar de pantalla el control se recrea: hay que volver a tocar."""
    page = PageConClean()
    g = GestorAudio(page, musica_src="a.mp3")
    llamadas = []
    g.musica.play = lambda: llamadas.append("play")

    g.iniciar_musica()
    g.iniciar_musica()
    assert llamadas == ["play"]

    g.registrar()
    g.iniciar_musica()
    assert llamadas == ["play", "play"], "no se reanudo tras cambiar de pantalla"


def test_registrar_funciona_sin_archivos_de_audio():
    page = PageConClean()
    GestorAudio(page).registrar()
    assert page.overlay == []


# --- Barajeo ------------------------------------------------------------------


def test_descubrir_fuentes_encuentra_el_barajeo():
    fuentes = descubrir_fuentes("assets", "Recursos")
    assert fuentes["barajar_src"] == "Recursos/barajar.wav"


def test_el_barajeo_suena_al_pedirlo():
    page = PageStub()
    g = GestorAudio(page, barajar_src="barajar.wav")
    llamadas = []
    g.barajar.play = lambda: llamadas.append("play")

    g.sonar_barajeo()
    g.sonar_barajeo()

    assert llamadas == ["play", "play"], "un efecto corto debe poder repetirse"


def test_el_barajeo_no_suena_silenciado():
    page = PageStub()
    g = GestorAudio(page, barajar_src="barajar.wav")
    llamadas = []
    g.barajar.play = lambda: llamadas.append("play")

    g.alternar_silencio()
    g.sonar_barajeo()

    assert llamadas == []


def test_el_barajeo_tambien_queda_listo_para_repetirse():
    from flet_audio.audio import ReleaseMode

    g = GestorAudio(PageStub(), barajar_src="barajar.wav")
    assert g.barajar.release_mode == ReleaseMode.STOP.value


def test_el_silencio_alcanza_a_todos_los_efectos():
    g = GestorAudio(PageStub(), musica_src="a.wav", victoria_src="b.mp3", barajar_src="c.wav")
    g.alternar_silencio()
    assert g.musica.volume == 0.0
    assert g.victoria.volume == 0.0
    assert g.barajar.volume == 0.0


def test_los_tres_sonidos_van_al_overlay():
    page = PageStub()
    GestorAudio(page, musica_src="a.wav", victoria_src="b.mp3", barajar_src="c.wav")
    assert len(page.overlay) == 3


def test_sonar_barajeo_no_falla_sin_archivo():
    GestorAudio(PageStub()).sonar_barajeo()
