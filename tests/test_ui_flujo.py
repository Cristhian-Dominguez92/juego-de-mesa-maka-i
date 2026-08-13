"""Test de integración de la capa de UI.

Ejercita los handlers reales de main.py contra un `Page` falso: verifica que los
botones estén bien cableados a la `Partida`, que el marcador se actualice y que
el cierre de partida funcione. No dibuja nada.

Se salta si flet no está instalado, para que la suite siga corriendo sin la UI.
"""

import asyncio

import pytest

pytest.importorskip("flet")

import flet as ft  # noqa: E402

import main as juego  # noqa: E402
from makai.ai import Dificultad  # noqa: E402
from makai.core import FICHAS_INICIALES, Rol  # noqa: E402
from makai.ui import estadisticas as stats  # noqa: E402
from makai.ui import personajes as pj  # noqa: E402
from makai.ui import textos  # noqa: E402
from makai.ui.audio import CLAVE_SILENCIO  # noqa: E402
from makai.ui.preferencias import CLAVE_DIFICULTAD  # noqa: E402


class ClientStorageStub:
    """client_storage respaldado por un dict, para verificar la persistencia."""

    def __init__(self, datos=None):
        self.datos = dict(datos or {})

    def get(self, clave):
        return self.datos.get(clave)

    def set(self, clave, valor):
        self.datos[clave] = valor
        return True


class PageStub:
    """Lo mínimo de ft.Page que main.py usa."""

    def __init__(self, width=None, almacenamiento=None):
        self.controls = []
        self.overlay = []
        self.client_storage = almacenamiento or ClientStorageStub()
        self.updates = 0
        self.width = width
        self.title = None
        self.bgcolor = None
        self.theme_mode = None
        self.vertical_alignment = None
        self.scroll = None
        self.on_resized = None

    def clean(self):
        self.controls.clear()

    def add(self, *controles):
        self.controls.extend(controles)

    def update(self):
        self.updates += 1


@pytest.fixture
def sin_esperas(monkeypatch):
    """Anula los sleep de animación para que el test sea instantáneo.

    El audio no hace falta silenciarlo: los controles ft.Audio no están unidos
    a una página real, así que GestorAudio se traga los fallos de reproducción.
    """

    async def no_esperar(_segundos):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_esperar)


def recorrer(control):
    """Recorre el árbol de controles, sea cual sea su forma."""
    yield control
    for atributo in ("controls", "content"):
        hijo = getattr(control, atributo, None)
        if hijo is None:
            continue
        for c in hijo if isinstance(hijo, list) else [hijo]:
            yield from recorrer(c)


def buscar(page, etiqueta):
    """Encuentra un control por su `data`, sin depender de su posición.

    Antes estos helpers indexaban posiciones (`col.controls[4]`), y cada
    cambio de maquetado rompía decenas de tests que nada tenían que ver con
    el cambio. Buscar por etiqueta los deja indiferentes al layout.
    """
    for raiz in page.controls:
        for c in recorrer(raiz):
            if getattr(c, "data", None) == etiqueta:
                return c
    raise AssertionError(f"no se encontro ningun control con data={etiqueta!r}")


def textos_visibles(page):
    valores = []
    for raiz in page.controls:
        for c in recorrer(raiz):
            valor = getattr(c, "value", None)
            if isinstance(valor, str) and valor:
                valores.append(valor)
    return valores


class Menu:
    """Controles de la pantalla de inicio."""

    def __init__(self, page):
        self.page = page
        self.comenzar = buscar(page, "btn_jugar")
        self.reglas = buscar(page, "btn_reglas")
        self.dificultad = buscar(page, "dificultad")
        self.estadisticas = buscar(page, "stats")


class PantallaReglas:
    def __init__(self, page):
        self.page = page
        self.titulo = buscar(page, "titulo_reglas")
        self.volver = buscar(page, "btn_volver")
        self.textos = textos_visibles(page)


class Tablero:
    """Controles de la mesa de juego, ubicados por etiqueta."""

    def __init__(self, page):
        self.page = page
        self.marcador = buscar(page, "marcador")
        self.silencio = buscar(page, "silencio")
        self.banca = buscar(page, "banca")
        self.estado = buscar(page, "estado")
        self.cartas_pc = buscar(page, "cartas_pc")
        self.cartas_jugador = buscar(page, "cartas_jugador")
        self.bajar = buscar(page, "apuesta_menos")
        self.apuesta = buscar(page, "apuesta")
        self.subir = buscar(page, "apuesta_mas")
        self.pedir = buscar(page, "btn_pedir")
        self.plantarse = buscar(page, "btn_plantarse")
        self.repartir = buscar(page, "btn_repartir")


async def abrir_menu(width=None, almacenamiento=None):
    page = PageStub(width=width, almacenamiento=almacenamiento)
    await juego.main(page)
    return Menu(page)


async def abrir_juego(width=None, almacenamiento=None):
    menu = await abrir_menu(width=width, almacenamiento=almacenamiento)
    assert menu.comenzar.text == "PARTIDA RÁPIDA"
    await menu.comenzar.on_click(None)
    return Tablero(menu.page)


async def jugar_ronda(tablero, pedir=0):
    await tablero.repartir.on_click(None)
    for _ in range(pedir):
        await tablero.pedir.on_click(None)
    await tablero.plantarse.on_click(None)


async def apostar_el_maximo(tablero):
    """Sube la apuesta hasta el tope, para que una sola ronda decida todo."""
    for _ in range(100):
        if tablero.subir.disabled:
            break
        await tablero.subir.on_click(None)


def marcador_de(fichas_jugador, fichas_pc):
    return f"Vos {fichas_jugador} 🪙  ·  {fichas_pc} 🪙 PC"


# --- Arranque -----------------------------------------------------------------


def test_la_pantalla_de_inicio_se_dibuja():
    page = PageStub()
    asyncio.run(juego.main(page))
    assert page.controls, "la pantalla de inicio no agrego ningun control"
    visibles = textos_visibles(page)
    assert "MAKA'I" in visibles
    assert "PARAGUAYO" in visibles


def test_se_entra_al_juego_desde_el_inicio(sin_esperas):
    tablero = asyncio.run(abrir_juego())
    assert tablero.marcador.value == marcador_de(FICHAS_INICIALES, FICHAS_INICIALES)
    assert [b.text for b in (tablero.pedir, tablero.plantarse, tablero.repartir)] == [
        "PEDIR",
        "PLANTARSE",
        "REPARTIR",
    ]


def test_los_botones_arrancan_en_el_estado_correcto(sin_esperas):
    tablero = asyncio.run(abrir_juego())
    assert tablero.pedir.disabled
    assert tablero.plantarse.disabled
    assert not tablero.repartir.disabled


def test_al_empezar_la_banca_es_la_pc(sin_esperas):
    tablero = asyncio.run(abrir_juego())
    assert tablero.banca.value == juego.texto_banca(Rol.PC)


# --- Una ronda ----------------------------------------------------------------


def test_repartir_muestra_dos_cartas_por_lado(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert len(tablero.cartas_jugador.controls) == 2
    assert len(tablero.cartas_pc.controls) == 2
    assert not tablero.pedir.disabled
    assert not tablero.plantarse.disabled
    assert tablero.repartir.disabled


def test_pedir_agrega_una_tercera_carta_y_se_deshabilita(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.pedir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert len(tablero.cartas_jugador.controls) == 3
    assert tablero.pedir.disabled, "no se puede pedir una cuarta carta"


def test_plantarse_mueve_las_fichas(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await jugar_ronda(tablero)
        return tablero

    tablero = asyncio.run(flujo())
    esperados = {marcador_de(105, 95), marcador_de(95, 105)}
    assert tablero.marcador.value in esperados
    assert not tablero.repartir.disabled
    assert tablero.pedir.disabled
    assert tablero.plantarse.disabled


def test_el_mensaje_de_la_ronda_es_uno_de_los_previstos(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await jugar_ronda(tablero)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.estado.value in juego.MENSAJE_RONDA.values()


def test_el_total_de_fichas_se_conserva(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        for _ in range(8):
            await jugar_ronda(tablero)
        return tablero.marcador.value

    marcador = asyncio.run(flujo())
    numeros = [int(t) for t in marcador.replace("·", " ").split() if t.isdigit()]
    assert sum(numeros) == 2 * FICHAS_INICIALES


# --- Apuestas -----------------------------------------------------------------


def test_la_apuesta_arranca_visible(sin_esperas):
    tablero = asyncio.run(abrir_juego())
    assert "Apuesta:" in tablero.apuesta.value


def test_subir_y_bajar_la_apuesta(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        inicial = tablero.apuesta.value
        await tablero.subir.on_click(None)
        subida = tablero.apuesta.value
        await tablero.bajar.on_click(None)
        return inicial, subida, tablero.apuesta.value

    inicial, subida, final = asyncio.run(flujo())
    assert subida != inicial
    assert final == inicial


def test_no_se_puede_bajar_por_debajo_del_minimo(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        for _ in range(20):
            await tablero.bajar.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.apuesta.value == "Apuesta: 1 🪙"
    assert tablero.bajar.disabled


def test_no_se_puede_subir_por_encima_del_maximo(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await apostar_el_maximo(tablero)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.apuesta.value == f"Apuesta: {FICHAS_INICIALES} 🪙"
    assert tablero.subir.disabled


def test_la_apuesta_no_se_puede_cambiar_con_la_ronda_en_juego(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        antes = tablero.apuesta.value
        await tablero.subir.on_click(None)
        return antes, tablero.apuesta.value, tablero.subir.disabled

    antes, despues, deshabilitado = asyncio.run(flujo())
    assert antes == despues
    assert deshabilitado


def test_apostar_mas_alto_mueve_mas_fichas(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        for _ in range(3):  # 5 -> 20
            await tablero.subir.on_click(None)
        await jugar_ronda(tablero)
        return tablero.marcador.value

    marcador = asyncio.run(flujo())
    assert marcador in {marcador_de(120, 80), marcador_de(80, 120)}


# --- Banca --------------------------------------------------------------------


def test_la_banca_pasa_al_ganador_de_la_ronda(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await jugar_ronda(tablero)
        return tablero

    tablero = asyncio.run(flujo())
    # Quien haya ganado, el cartel debe coincidir con el marcador.
    gano_jugador = tablero.marcador.value == marcador_de(105, 95)
    esperado = Rol.JUGADOR if gano_jugador else Rol.PC
    assert tablero.banca.value == juego.texto_banca(esperado)


@pytest.mark.lento
def test_la_banca_cambia_de_lado_a_lo_largo_de_la_partida(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        vistos = set()
        for _ in range(40):
            await jugar_ronda(tablero)
            vistos.add(tablero.banca.value)
        return vistos

    vistos = asyncio.run(flujo())
    assert len(vistos) == 2, "la banca nunca cambio de lado"


# --- Fin de partida -----------------------------------------------------------


def test_apostando_todo_una_ronda_define_la_partida(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await apostar_el_maximo(tablero)
        await jugar_ronda(tablero)
        return tablero

    tablero = asyncio.run(flujo())
    # Tras terminar, la partida se reinicia y vuelve el titulo.
    assert tablero.marcador.value == marcador_de(FICHAS_INICIALES, FICHAS_INICIALES)
    assert tablero.estado.value == juego.TITULO
    assert tablero.estado.color == "white"
    assert not tablero.repartir.disabled


def test_se_muestra_el_cierre_de_partida(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        mensajes = []
        original = tablero.page.update

        def update():
            original()
            mensajes.append(tablero.estado.value)

        tablero.page.update = update

        await apostar_el_maximo(tablero)
        await jugar_ronda(tablero)
        return mensajes

    mensajes = asyncio.run(flujo())
    finales = {juego.MENSAJE_GANASTE, juego.MENSAJE_PERDISTE}
    assert finales & set(mensajes), "no se mostro el mensaje de fin de partida"


def test_se_puede_seguir_jugando_tras_terminar(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await apostar_el_maximo(tablero)
        await jugar_ronda(tablero)
        await jugar_ronda(tablero)
        return tablero.marcador.value

    marcador = asyncio.run(flujo())
    assert marcador in {marcador_de(105, 95), marcador_de(95, 105)}


# --- Dificultad ---------------------------------------------------------------


def test_la_dificultad_se_guarda_al_elegirla():
    async def flujo():
        menu = await abrir_menu()
        menu.dificultad.value = Dificultad.DIFICIL.value
        await menu.dificultad.on_change(None)
        return menu.page.client_storage.get(CLAVE_DIFICULTAD)

    assert asyncio.run(flujo()) == Dificultad.DIFICIL.value


def test_se_respeta_la_dificultad_guardada():
    async def flujo():
        almacen = ClientStorageStub({CLAVE_DIFICULTAD: Dificultad.FACIL.value})
        menu = await abrir_menu(almacenamiento=almacen)
        return menu.dificultad.value

    assert asyncio.run(flujo()) == Dificultad.FACIL.value


def test_una_dificultad_corrupta_no_rompe_el_menu():
    async def flujo():
        almacen = ClientStorageStub({CLAVE_DIFICULTAD: "imposible"})
        menu = await abrir_menu(almacenamiento=almacen)
        return menu.dificultad.value

    assert asyncio.run(flujo()) == Dificultad.NORMAL.value


def test_el_menu_ofrece_las_tres_dificultades():
    async def flujo():
        menu = await abrir_menu()
        return [o.key for o in menu.dificultad.options]

    assert asyncio.run(flujo()) == [d.value for d in Dificultad]


# --- Estadísticas -------------------------------------------------------------


def test_las_estadisticas_se_guardan_al_jugar(sin_esperas):
    async def flujo():
        almacen = ClientStorageStub()
        tablero = await abrir_juego(almacenamiento=almacen)
        await jugar_ronda(tablero)
        return stats.cargar(almacen)

    e = asyncio.run(flujo())
    assert e.rondas_jugadas == 1


def test_la_partida_terminada_queda_registrada(sin_esperas):
    async def flujo():
        almacen = ClientStorageStub()
        tablero = await abrir_juego(almacenamiento=almacen)
        await apostar_el_maximo(tablero)
        await jugar_ronda(tablero)
        return stats.cargar(almacen)

    e = asyncio.run(flujo())
    assert e.partidas_jugadas == 1
    assert e.rondas_jugadas == 1


def test_el_menu_muestra_las_estadisticas_guardadas():
    async def flujo():
        almacen = ClientStorageStub()
        stats.guardar(
            almacen,
            stats.Estadisticas(
                partidas_jugadas=4, partidas_ganadas=3, rondas_jugadas=50, rondas_ganadas=30
            ),
        )
        menu = await abrir_menu(almacenamiento=almacen)
        return menu.estadisticas.value

    texto = asyncio.run(flujo())
    assert "3/4" in texto
    assert "60.0%" in texto


def test_sin_historial_el_menu_no_muestra_estadisticas():
    async def flujo():
        menu = await abrir_menu()
        return menu.estadisticas.value

    assert asyncio.run(flujo()) == ""


# --- Silencio -----------------------------------------------------------------


def test_el_boton_de_silencio_alterna_icono_y_estado(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        estados = [tablero.silencio.icon]
        await tablero.silencio.on_click(None)
        estados.append(tablero.silencio.icon)
        await tablero.silencio.on_click(None)
        estados.append(tablero.silencio.icon)
        return tablero, estados

    tablero, estados = asyncio.run(flujo())
    assert estados == [ft.Icons.VOLUME_UP, ft.Icons.VOLUME_OFF, ft.Icons.VOLUME_UP]
    assert tablero.silencio.tooltip == "Silenciar"


def test_el_silencio_se_recuerda_en_client_storage(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.silencio.on_click(None)
        return tablero.page.client_storage.get(CLAVE_SILENCIO)

    assert asyncio.run(flujo()) is True


def test_arranca_silenciado_si_asi_quedo_la_vez_anterior(sin_esperas):
    async def flujo():
        almacen = ClientStorageStub({CLAVE_SILENCIO: True})
        return await abrir_juego(almacenamiento=almacen)

    tablero = asyncio.run(flujo())
    assert tablero.silencio.icon == ft.Icons.VOLUME_OFF
    assert tablero.silencio.tooltip == "Activar sonido"


# --- Responsive ---------------------------------------------------------------


def test_en_pantalla_chica_las_cartas_se_achican(sin_esperas):
    async def flujo(width):
        tablero = await abrir_juego(width=width)
        await tablero.repartir.on_click(None)
        return tablero.cartas_jugador.controls[0].content.width

    ancho_chico = asyncio.run(flujo(320))
    ancho_escritorio = asyncio.run(flujo(1280))
    assert ancho_chico < ancho_escritorio


def test_las_cartas_entran_en_pantalla_de_telefono(sin_esperas):
    from makai.ui.layout import MARGEN_LATERAL, SEPARACION_CARTAS

    async def flujo():
        tablero = await abrir_juego(width=320)
        await tablero.repartir.on_click(None)
        await tablero.pedir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    cartas = tablero.cartas_jugador.controls
    assert len(cartas) == 3
    ocupado = sum(c.content.width for c in cartas) + SEPARACION_CARTAS * (len(cartas) - 1)
    assert ocupado <= 320 - 2 * MARGEN_LATERAL + 0.01


def test_redimensionar_recalcula_las_cartas(sin_esperas):
    async def flujo():
        tablero = await abrir_juego(width=1280)
        await tablero.repartir.on_click(None)
        antes = tablero.cartas_jugador.controls[0].content.width

        tablero.page.width = 320
        await tablero.page.on_resized(None)
        return antes, tablero.cartas_jugador.controls[0].content.width

    antes, despues = asyncio.run(flujo())
    assert despues < antes


def test_redimensionar_no_revela_las_cartas_de_la_pc(sin_esperas):
    """El resize vuelve a dibujar el tablero: no debe filtrar la mano oculta."""

    async def flujo():
        tablero = await abrir_juego(width=1280)
        await tablero.repartir.on_click(None)
        tablero.page.width = 400
        await tablero.page.on_resized(None)
        return [c.content.src for c in tablero.cartas_pc.controls]

    fuentes = asyncio.run(flujo())
    assert fuentes == [juego.DORSO, juego.DORSO]


def test_redimensionar_conserva_las_cartas_reveladas(sin_esperas):
    async def flujo():
        tablero = await abrir_juego(width=1280)
        await jugar_ronda(tablero)
        tablero.page.width = 400
        await tablero.page.on_resized(None)
        return [c.content.src for c in tablero.cartas_pc.controls]

    fuentes = asyncio.run(flujo())
    assert juego.DORSO not in fuentes, "tras plantarse la mano de la PC queda visible"


# --- Clics fuera de turno -----------------------------------------------------
# Regresion: al jugar de verdad aparecian EstadoInvalido en consola. Deshabilitar
# el boton no alcanza, porque entre el clic y el redibujado se cuelan eventos.


def test_repartir_dos_veces_seguidas_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        cartas = len(tablero.cartas_jugador.controls)
        await tablero.repartir.on_click(None)
        return cartas, len(tablero.cartas_jugador.controls)

    antes, despues = asyncio.run(flujo())
    assert antes == despues == 2, "el segundo reparto no debe repartir de nuevo"


def test_plantarse_dos_veces_seguidas_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await jugar_ronda(tablero)
        marcador = tablero.marcador.value
        await tablero.plantarse.on_click(None)
        return marcador, tablero.marcador.value

    antes, despues = asyncio.run(flujo())
    assert antes == despues, "el segundo plantarse no debe resolver otra ronda"


def test_pedir_de_mas_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        for _ in range(3):
            await tablero.pedir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert len(tablero.cartas_jugador.controls) == 3


def test_pedir_o_plantarse_antes_de_repartir_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.pedir.on_click(None)
        await tablero.plantarse.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.marcador.value == marcador_de(FICHAS_INICIALES, FICHAS_INICIALES)
    assert tablero.cartas_jugador.controls == []


# --- Pantalla de reglas -------------------------------------------------------


def test_se_puede_abrir_las_reglas_desde_el_menu():
    async def flujo():
        menu = await abrir_menu()
        assert menu.reglas.text == "CÓMO SE JUEGA"
        await menu.reglas.on_click(None)
        return PantallaReglas(menu.page)

    reglas = asyncio.run(flujo())
    assert reglas.titulo.value == textos.TITULO_REGLAS


def test_las_reglas_muestran_todas_las_secciones():
    async def flujo():
        menu = await abrir_menu()
        await menu.reglas.on_click(None)
        return PantallaReglas(menu.page)

    reglas = asyncio.run(flujo())
    for encabezado, cuerpo in textos.REGLAS:
        assert encabezado in reglas.textos
        assert cuerpo in reglas.textos


def test_desde_las_reglas_se_vuelve_al_menu():
    async def flujo():
        menu = await abrir_menu()
        await menu.reglas.on_click(None)
        pantalla = PantallaReglas(menu.page)
        assert pantalla.volver.text == "VOLVER"
        await pantalla.volver.on_click(None)
        return Menu(menu.page)

    menu = asyncio.run(flujo())
    assert menu.comenzar.text == "PARTIDA RÁPIDA"


def test_las_reglas_no_dejan_un_on_resized_del_juego_colgado(sin_esperas):
    """Volver del juego a otra pantalla debe soltar el handler de resize."""

    async def flujo():
        menu = await abrir_menu()
        await menu.reglas.on_click(None)
        return menu.page.on_resized

    assert asyncio.run(flujo()) is None


# --- Animaciones --------------------------------------------------------------


def test_tras_repartir_ninguna_carta_queda_invisible(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    for fila in (tablero.cartas_jugador, tablero.cartas_pc):
        for c in fila.controls:
            assert c.opacity == 1, "una carta quedo a medio aparecer"
            assert c.scale.scale == 1, "una carta quedo encogida"


def test_la_carta_pedida_termina_visible(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.pedir.on_click(None)
        return tablero.cartas_jugador.controls[-1]

    nueva = asyncio.run(flujo())
    assert nueva.opacity == 1
    assert nueva.scale.scale == 1


def test_pedir_no_vuelve_a_animar_las_cartas_ya_repartidas(sin_esperas):
    """La tercera carta se agrega; las dos primeras no se redibujan."""

    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        antes = list(tablero.cartas_jugador.controls)
        await tablero.pedir.on_click(None)
        return antes, tablero.cartas_jugador.controls

    antes, despues = asyncio.run(flujo())
    assert despues[:2] == antes, "se recrearon las cartas ya visibles"
    assert len(despues) == 3


def test_al_plantarse_las_cartas_de_la_pc_quedan_de_frente(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await jugar_ronda(tablero)
        return tablero.cartas_pc.controls

    cartas = asyncio.run(flujo())
    for c in cartas:
        assert c.content.src != juego.DORSO, "una carta de la PC quedo boca abajo"
        assert c.scale.scale_x == 1, "una carta de la PC quedo de canto"


def test_las_cartas_que_pide_la_pc_se_muestran_boca_abajo(sin_esperas):
    """Mientras la PC juega, sus cartas nuevas no deben revelarse."""
    vistas = []

    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        original = tablero.page.update

        def update():
            original()
            vistas.append([c.content.src for c in tablero.cartas_pc.controls])

        tablero.page.update = update
        await tablero.plantarse.on_click(None)

    asyncio.run(flujo())
    # Antes del volteo, todo lo que se vio de la PC eran dorsos.
    primeras = vistas[0] if vistas else []
    assert all(src == juego.DORSO for src in primeras)


# --- Barajeo al repartir ------------------------------------------------------


def test_repartir_dispara_el_sonido_de_barajeo(sin_esperas, monkeypatch):
    """main.py no expone el gestor, asi que se espia el metodo en la clase."""
    sonidos = []
    from makai.ui.audio import GestorAudio

    monkeypatch.setattr(GestorAudio, "sonar_barajeo", lambda self: sonidos.append("barajeo"))

    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)

    asyncio.run(flujo())
    assert sonidos == ["barajeo"], "el reparto debe sonar exactamente una vez"


def test_repartir_fuera_de_turno_no_dispara_el_barajeo(sin_esperas, monkeypatch):
    """El clic descartado no debe sonar: seria un barajeo fantasma."""
    sonidos = []
    from makai.ui.audio import GestorAudio

    monkeypatch.setattr(GestorAudio, "sonar_barajeo", lambda self: sonidos.append("barajeo"))

    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.repartir.on_click(None)  # fuera de turno

    asyncio.run(flujo())
    assert sonidos == ["barajeo"]


# --- Personajes ---------------------------------------------------------------


class PantallaPersonajes:
    def __init__(self, page):
        self.page = page
        self.titulo = buscar(page, "titulo_personajes")
        self.volver = buscar(page, "btn_volver_personajes")

    def tarjeta(self, identificador):
        return buscar(self.page, f"personaje_{identificador}")


class ClicFalso:
    """Imita el evento de Flet, que trae el control que se toco."""

    def __init__(self, control):
        self.control = control


async def abrir_personajes(almacenamiento=None):
    menu = await abrir_menu(almacenamiento=almacenamiento)
    assert menu_boton_personaje(menu).text == "MI PERSONAJE"
    await menu_boton_personaje(menu).on_click(None)
    return PantallaPersonajes(menu.page)


def menu_boton_personaje(menu):
    return buscar(menu.page, "btn_personaje")


def test_el_menu_ofrece_elegir_personaje():
    async def flujo():
        menu = await abrir_menu()
        return menu_boton_personaje(menu).text

    assert asyncio.run(flujo()) == "MI PERSONAJE"


def test_la_pantalla_muestra_los_seis_personajes():
    async def flujo():
        pantalla = await abrir_personajes()
        return [pantalla.tarjeta(p.id) for p in pj.PERSONAJES]

    tarjetas = asyncio.run(flujo())
    assert len(tarjetas) == len(pj.PERSONAJES)


def test_elegir_un_personaje_lo_guarda():
    async def flujo():
        almacen = ClientStorageStub()
        pantalla = await abrir_personajes(almacenamiento=almacen)
        tarjeta = pantalla.tarjeta("vaicho")
        await tarjeta.on_click(ClicFalso(tarjeta))
        return almacen

    almacen = asyncio.run(flujo())
    assert pj.cargar(almacen).id == "vaicho"


def test_se_respeta_el_personaje_guardado():
    async def flujo():
        almacen = ClientStorageStub({pj.CLAVE_PERSONAJE: "leporato"})
        tablero = await abrir_juego(almacenamiento=almacen)
        return textos_visibles(tablero.page)

    assert "Leporato" in asyncio.run(flujo())


def test_desde_los_personajes_se_vuelve_al_menu():
    async def flujo():
        pantalla = await abrir_personajes()
        await pantalla.volver.on_click(None)
        return Menu(pantalla.page)

    menu = asyncio.run(flujo())
    assert menu.comenzar.text == "PARTIDA RÁPIDA"


def test_la_mesa_muestra_las_dos_caras(sin_esperas):
    async def flujo():
        almacen = ClientStorageStub({pj.CLAVE_PERSONAJE: "gordo"})
        tablero = await abrir_juego(almacenamiento=almacen)
        return textos_visibles(tablero.page)

    visibles = asyncio.run(flujo())
    assert "El Gordo" in visibles, "falta el nombre del jugador"
    rival = pj.rival_de(pj.por_id("gordo"))
    assert rival.nombre in visibles, "falta el nombre del rival"


def test_el_rival_nunca_es_el_mismo_que_el_jugador(sin_esperas):
    for elegido in pj.PERSONAJES:

        async def flujo(elegido=elegido):
            almacen = ClientStorageStub({pj.CLAVE_PERSONAJE: elegido.id})
            tablero = await abrir_juego(almacenamiento=almacen)
            return textos_visibles(tablero.page)

        visibles = asyncio.run(flujo())
        assert visibles.count(elegido.nombre) == 1, f"{elegido.nombre} aparece dos veces"
