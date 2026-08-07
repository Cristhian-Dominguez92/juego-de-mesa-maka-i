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


class PageStub:
    """Lo mínimo de ft.Page que main.py usa."""

    def __init__(self):
        self.controls = []
        self.updates = 0
        self.title = None
        self.bgcolor = None
        self.theme_mode = None
        self.vertical_alignment = None

    def clean(self):
        self.controls.clear()

    def add(self, *controles):
        self.controls.extend(controles)

    def update(self):
        self.updates += 1


@pytest.fixture
def sin_esperas(monkeypatch):
    """Anula los sleep de animación y el audio para que el test sea instantáneo."""

    async def no_esperar(_segundos):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_esperar)
    monkeypatch.setattr(juego, "pygame", None)


class Tablero:
    """Acceso a los controles que main.py arma, para no repetir índices."""

    def __init__(self, page):
        self.page = page
        root_col = page.controls[0].content
        self.marcador = root_col.controls[0]
        self.estado = root_col.controls[1].content
        self.cartas_pc = root_col.controls[3]
        self.cartas_jugador = root_col.controls[5]
        self.pedir, self.plantarse, self.repartir = root_col.controls[-1].controls


async def abrir_juego():
    page = PageStub()
    await juego.main(page)

    # Pantalla de inicio: el ultimo control es el boton COMENZAR JUEGO.
    boton_comenzar = page.controls[0].controls[-1]
    assert boton_comenzar.text == "COMENZAR JUEGO"
    await boton_comenzar.on_click(None)

    return Tablero(page)


# --- Arranque -----------------------------------------------------------------


def test_la_pantalla_de_inicio_se_dibuja():
    page = PageStub()
    asyncio.run(juego.main(page))
    assert page.controls, "la pantalla de inicio no agrego ningun control"
    textos = [c.value for c in page.controls[0].controls if hasattr(c, "value")]
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
    finales = {
        "🏆 ¡FELICIDADES, ACABAS DE GANAR LA PARTIDA! 🏆",
        "😢 PERDISTE, ¡VUELVE A INTENTARLO!",
    }
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
