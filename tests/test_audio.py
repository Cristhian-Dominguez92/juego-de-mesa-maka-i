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


def test_el_proyecto_real_no_trae_musica_de_fondo():
    """La musica con licencia hay que aportarla (ver CREDITS.md)."""
    fuentes = descubrir_fuentes("assets", "Recursos")
    assert fuentes["musica_src"] is None
    assert fuentes["victoria_src"] == "Recursos/victoria.mp3"


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
    from flet.core.audio import ReleaseMode

    assert gestor.musica.release_mode == ReleaseMode.LOOP.value


def test_el_efecto_de_victoria_no_se_repite(gestor):
    from flet.core.audio import ReleaseMode

    assert gestor.victoria.release_mode == ReleaseMode.RELEASE.value


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
