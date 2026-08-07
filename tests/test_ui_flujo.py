"""Test de integración de la capa de UI.

Ejercita los handlers reales de main.py contra un `Page` falso: verifica que los
botones estén bien cableados a la `Partida`, que el marcador se actualice y que
el reinicio de fin de partida funcione. No dibuja nada.

Se salta si flet no está instalado, para que la suite siga corriendo sin la UI.
"""

import asyncio

import pytest

pytest.importorskip("flet")

import main as juego  # noqa: E402


class ClientStorageStub:
    """client_storage respaldado por un dict, para verificar la persistencia."""

    def __init__(self):
        self.datos = {}

    def get(self, clave):
        return self.datos.get(clave)

    def set(self, clave, valor):
        self.datos[clave] = valor
        return True


class PageStub:
    """Lo mínimo de ft.Page que main.py usa."""

    def __init__(self, width=None):
        self.controls = []
        self.overlay = []
        self.client_storage = ClientStorageStub()
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


class Tablero:
    """Acceso a los controles que main.py arma, para no repetir índices.

    La jerarquia es: page -> SafeArea -> Container -> Column.
    """

    def __init__(self, page):
        self.page = page
        root_col = page.controls[0].content.content
        encabezado = root_col.controls[0]
        self.marcador = encabezado.controls[0]
        self.silencio = encabezado.controls[1]
        self.estado = root_col.controls[1].content
        self.cartas_pc = root_col.controls[3]
        self.cartas_jugador = root_col.controls[5]
        self.pedir, self.plantarse, self.repartir = root_col.controls[-1].controls


async def abrir_juego(width=None):
    page = PageStub(width=width)
    await juego.main(page)

    # Pantalla de inicio: SafeArea -> Column, y el ultimo control es el boton.
    boton_comenzar = page.controls[0].content.controls[-1]
    assert boton_comenzar.text == "COMENZAR JUEGO"
    await boton_comenzar.on_click(None)

    return Tablero(page)


# --- Arranque -----------------------------------------------------------------


def test_la_pantalla_de_inicio_se_dibuja():
    page = PageStub()
    asyncio.run(juego.main(page))
    assert page.controls, "la pantalla de inicio no agrego ningun control"
    textos = [c.value for c in page.controls[0].content.controls if hasattr(c, "value")]
    assert "MAKA'I" in textos


def test_se_entra_al_juego_desde_el_inicio(sin_esperas):
    tablero = asyncio.run(abrir_juego())
    assert tablero.marcador.value == "Usuario 0 - 0 PC"
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


def test_plantarse_resuelve_la_ronda_y_actualiza_el_marcador(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.plantarse.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.marcador.value in ("Usuario 1 - 0 PC", "Usuario 0 - 1 PC")
    assert not tablero.repartir.disabled, "se debe poder repartir la ronda siguiente"
    assert tablero.pedir.disabled
    assert tablero.plantarse.disabled


def test_el_mensaje_de_la_ronda_es_uno_de_los_previstos(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.plantarse.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    assert tablero.estado.value in juego.MENSAJE_RONDA.values()


# --- Partida completa ---------------------------------------------------------


def grabar_pantalla(tablero):
    """Registra marcador y mensaje en cada page.update().

    Hace falta porque el fin de partida muestra el 10 y el mensaje de
    victoria/derrota, pero reinicia el marcador antes de que el handler
    termine: mirando solo el estado final esos pasos son invisibles.
    """
    historial = []
    original = tablero.page.update

    def update():
        original()
        historial.append((tablero.marcador.value, tablero.estado.value))

    tablero.page.update = update
    return historial


@pytest.mark.lento
def test_una_partida_completa_no_rompe_y_reinicia_el_marcador(sin_esperas):
    """Juega hasta que alguien llega a 10, verifica el cierre y sigue jugando.

    Cubre el camino de fin de partida, que en el codigo original estaba
    duplicado en dos bloques identicos.
    """

    async def flujo():
        tablero = await abrir_juego()
        historial = grabar_pantalla(tablero)
        for _ in range(200):
            await tablero.repartir.on_click(None)
            await tablero.plantarse.on_click(None)
            if tablero.marcador.value == "Usuario 0 - 0 PC":
                # La partida termino y se reinicio: jugamos una ronda mas.
                await tablero.repartir.on_click(None)
                await tablero.plantarse.on_click(None)
                return tablero, historial
        pytest.fail("la partida nunca termino en 200 rondas")

    tablero, historial = asyncio.run(flujo())
    marcadores = [m for m, _ in historial]
    mensajes = [e for _, e in historial]

    # Alguien llego a 10 en algun momento.
    assert any("10" in m for m in marcadores), "nadie llego a 10"

    # Se mostro el cierre de partida.
    finales = {juego.MENSAJE_GANASTE, juego.MENSAJE_PERDISTE}
    assert finales & set(mensajes), "no se mostro el mensaje de fin de partida"

    # Y se pudo seguir jugando despues del reinicio.
    assert tablero.marcador.value in ("Usuario 1 - 0 PC", "Usuario 0 - 1 PC")
    assert not tablero.repartir.disabled


@pytest.mark.lento
def test_el_titulo_se_restaura_tras_terminar_la_partida(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        for _ in range(200):
            await tablero.repartir.on_click(None)
            await tablero.plantarse.on_click(None)
            if tablero.marcador.value == "Usuario 0 - 0 PC":
                return tablero
        pytest.fail("la partida nunca termino en 200 rondas")

    tablero = asyncio.run(flujo())
    assert tablero.estado.value == juego.TITULO
    assert tablero.estado.color == "white"
    assert tablero.estado.size == 30


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
    import flet as ft

    assert estados == [ft.Icons.VOLUME_UP, ft.Icons.VOLUME_OFF, ft.Icons.VOLUME_UP]
    assert tablero.silencio.tooltip == "Silenciar"


def test_el_silencio_se_recuerda_en_client_storage(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.silencio.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    from makai.ui.audio import CLAVE_SILENCIO

    assert tablero.page.client_storage.get(CLAVE_SILENCIO) is True


def test_arranca_silenciado_si_asi_quedo_la_vez_anterior(sin_esperas):
    from makai.ui.audio import CLAVE_SILENCIO

    async def flujo():
        page = PageStub()
        page.client_storage.set(CLAVE_SILENCIO, True)
        await juego.main(page)
        await page.controls[0].content.controls[-1].on_click(None)
        return Tablero(page)

    tablero = asyncio.run(flujo())
    import flet as ft

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
        despues = tablero.cartas_jugador.controls[0].content.width
        return antes, despues

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
        await tablero.repartir.on_click(None)
        await tablero.plantarse.on_click(None)
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
        # Segundo clic antes de que el cliente redibuje el boton deshabilitado.
        await tablero.repartir.on_click(None)
        return cartas, len(tablero.cartas_jugador.controls)

    antes, despues = asyncio.run(flujo())
    assert antes == despues == 2, "el segundo reparto no debe repartir de nuevo"


def test_plantarse_dos_veces_seguidas_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.plantarse.on_click(None)
        marcador = tablero.marcador.value
        await tablero.plantarse.on_click(None)
        return marcador, tablero.marcador.value

    antes, despues = asyncio.run(flujo())
    assert antes == despues, "el segundo plantarse no debe resolver otra ronda"


def test_pedir_de_mas_no_rompe(sin_esperas):
    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        await tablero.pedir.on_click(None)
        await tablero.pedir.on_click(None)
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
    assert tablero.marcador.value == "Usuario 0 - 0 PC"
    assert tablero.cartas_jugador.controls == []


def test_plantarse_durante_el_turno_de_la_pc_no_rompe(sin_esperas):
    """El turno de la banca dura varios segundos: hay tiempo de volver a hacer clic."""

    async def flujo():
        tablero = await abrir_juego()
        await tablero.repartir.on_click(None)
        # Dispara el turno de la banca y, en el medio, otro clic.
        primera = tablero.plantarse.on_click(None)
        await primera
        await tablero.plantarse.on_click(None)
        await tablero.repartir.on_click(None)
        await tablero.repartir.on_click(None)
        return tablero

    tablero = asyncio.run(flujo())
    # Una sola ronda resuelta, y una nueva repartida.
    puntos = tablero.marcador.value
    assert puntos in ("Usuario 1 - 0 PC", "Usuario 0 - 1 PC")
    assert len(tablero.cartas_jugador.controls) == 2
