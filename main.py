"""Punto de entrada del juego: capa de presentación (Flet).

La lógica de juego vive en `makai/core` y no depende de Flet. Este archivo se
limita a dibujar el estado de una `Partida` y a traducir clics.
"""

import asyncio

import flet as ft

from makai.ai import Dificultad, estrategia_para
from makai.core import Carta, Estado, Partida, Resultado, Rol
from makai.ui import animacion, layout, textos
from makai.ui import estadisticas as stats
from makai.ui.audio import GestorAudio, descubrir_fuentes
from makai.ui.preferencias import cargar_dificultad, guardar_dificultad

# --- Rutas de assets ---
# Se resuelven contra assets_dir de Flet (ver ft.app al final), por eso van sin
# el prefijo "assets/".
ASSETS_DIR = "assets"
RECURSOS = "Recursos"
DORSO = f"{RECURSOS}/dorso.jpeg"

TITULO = "¡JAHUGA Maka-'I!"

MENSAJE_RONDA = {
    Resultado.GANA_JUGADOR: "¡GANASTE ESTA RONDA! 🏆",
    Resultado.GANA_PC: "Gana la PC 🤖",
    Resultado.EMPATE: "Empate: se la lleva la banca",
}

MENSAJE_GANASTE = "🏆 ¡FELICIDADES, ACABAS DE GANAR LA PARTIDA! 🏆"
MENSAJE_PERDISTE = "😢 TE QUEDASTE SIN FICHAS, ¡VUELVE A INTENTARLO!"

#: Cuánto sube o baja la apuesta con cada clic.
PASO_APUESTA = 5

# Tamaños de fuente pensados para escritorio; en pantallas angostas se reducen.
TAMANO_TITULO = 30
TAMANO_MARCADOR = 20
TAMANO_CIERRE = 28


def ruta_imagen(carta: Carta) -> str:
    return f"{RECURSOS}/{carta.nombre_archivo}"


def texto_banca(banca: Rol) -> str:
    return "🏛 Sos la banca" if banca is Rol.JUGADOR else "🏛 La banca es la PC"


def resumen_estadisticas(e: stats.Estadisticas) -> str:
    if not e.rondas_jugadas:
        return ""
    return (
        f"Partidas: {e.partidas_ganadas}/{e.partidas_jugadas}   ·   "
        f"Rondas ganadas: {e.porcentaje_rondas}%   ·   "
        f"Mejor racha: {e.mejor_racha}"
    )


# --- Aplicación Principal ---
async def main(page: ft.Page):
    page.title = "Maka-i Paraguayo"
    page.bgcolor = "#1a4a1a"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # En pantallas bajas el tablero no entra completo: mejor poder desplazarlo
    # que recortarlo.
    page.scroll = ft.ScrollMode.AUTO

    audio = GestorAudio(page, **descubrir_fuentes(ASSETS_DIR, RECURSOS))
    almacen = page.client_storage
    estadisticas = stats.cargar(almacen)
    dificultad = cargar_dificultad(almacen)
    partida = Partida(estrategia_pc=estrategia_para(dificultad))

    # Función para mostrar pantalla de inicio
    async def mostrar_inicio(e=None):
        nonlocal dificultad
        page.clean()
        page.on_resized = None

        txt_welcome = ft.Text(
            "Bienvenidos al tradicional juego de mesa",
            size=layout.tamano_texto(28, page.width),
            weight=ft.FontWeight.BOLD,
            color="gold",
            text_align=ft.TextAlign.CENTER,
        )
        txt_game_name = ft.Text(
            "MAKA'I",
            size=layout.tamano_texto(60, page.width),
            weight=ft.FontWeight.BOLD,
            color="orange",
            text_align=ft.TextAlign.CENTER,
        )
        txt_subtitle = ft.Text(
            "¡El juego de cartas más emocionante!",
            size=layout.tamano_texto(18, page.width),
            color="yellow",
            text_align=ft.TextAlign.CENTER,
            italic=True,
        )

        async def cambiar_dificultad(e):
            nonlocal dificultad
            dificultad = Dificultad.desde_texto(dd_dificultad.value, dificultad)
            guardar_dificultad(almacen, dificultad)

        dd_dificultad = ft.Dropdown(
            label="Dificultad",
            value=dificultad.value,
            options=[ft.DropdownOption(key=d.value, text=d.etiqueta) for d in Dificultad],
            on_change=cambiar_dificultad,
            width=220,
        )

        txt_stats = ft.Text(
            resumen_estadisticas(estadisticas),
            size=layout.tamano_texto(14, page.width),
            color="white70",
            text_align=ft.TextAlign.CENTER,
        )

        btn_start = ft.Button(
            "COMENZAR JUEGO",
            on_click=mostrar_juego,
            bgcolor="orange800",
            color="white",
            width=300,
            height=50,
        )
        btn_reglas = ft.TextButton(
            "Cómo se juega",
            on_click=mostrar_reglas,
            style=ft.ButtonStyle(color="white70"),
        )

        welcome_col = ft.Column(
            [
                txt_welcome,
                txt_game_name,
                txt_subtitle,
                ft.Divider(height=20),
                dd_dificultad,
                txt_stats,
                ft.Divider(height=20),
                btn_start,
                btn_reglas,
            ],
            # En una Column el eje principal es el vertical, asi que el centrado
            # vertical va en `alignment`. `vertical_alignment` solo existe en Row.
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )

        page.add(ft.SafeArea(content=welcome_col, expand=True))
        page.update()

    # Pantalla de reglas
    async def mostrar_reglas(e=None):
        page.clean()
        page.on_resized = None

        secciones = []
        for encabezado, cuerpo in textos.REGLAS:
            secciones.append(
                ft.Text(
                    encabezado,
                    size=layout.tamano_texto(20, page.width),
                    weight=ft.FontWeight.BOLD,
                    color="gold",
                )
            )
            secciones.append(
                ft.Text(cuerpo, size=layout.tamano_texto(15, page.width), color="white")
            )
            secciones.append(ft.Divider(height=16, color="transparent"))

        contenido = ft.Column(
            [
                ft.Text(
                    textos.TITULO_REGLAS,
                    size=layout.tamano_texto(32, page.width),
                    weight=ft.FontWeight.BOLD,
                    color="orange",
                ),
                ft.Divider(height=16),
                *secciones,
                ft.Button(
                    "VOLVER",
                    on_click=mostrar_inicio,
                    bgcolor="orange800",
                    color="white",
                    width=200,
                    height=44,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=6,
        )

        page.add(ft.SafeArea(content=contenido, expand=True))
        page.update()

    # Función para mostrar el juego principal
    async def mostrar_juego(e=None):
        page.clean()
        audio.iniciar_musica()

        pc_revelada = False

        txt_status = ft.Text(TITULO, weight=ft.FontWeight.BOLD)
        txt_fichas = ft.Text(color="yellow", weight=ft.FontWeight.BOLD)
        txt_banca = ft.Text(color="white70", italic=True)
        txt_apuesta = ft.Text(color="white")
        row_pc = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=layout.SEPARACION_CARTAS)
        row_user = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=layout.SEPARACION_CARTAS)

        btn_silencio = ft.IconButton(
            icon=ft.Icons.VOLUME_OFF if audio.silenciado else ft.Icons.VOLUME_UP,
            tooltip="Activar sonido" if audio.silenciado else "Silenciar",
            icon_color="white",
        )
        btn_menos = ft.IconButton(icon=ft.Icons.REMOVE, tooltip="Bajar apuesta", icon_color="white")
        btn_mas = ft.IconButton(icon=ft.Icons.ADD, tooltip="Subir apuesta", icon_color="white")

        status_box = ft.Container(
            content=txt_status,
            padding=10,
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            scale=1.0,
            animate_scale=450,
            rotate=ft.Rotate(0.0),
            animate_rotation=350,
            offset=ft.Offset(0, 0),
            animate_offset=120,
        )

        encabezado = ft.Row(
            [txt_fichas, btn_silencio],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        fila_apuesta = ft.Row(
            [btn_menos, txt_apuesta, btn_mas],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )

        root_col = ft.Column(
            [
                encabezado,
                txt_banca,
                status_box,
                ft.Text("PC"),
                row_pc,
                ft.Divider(height=30),
                row_user,
                ft.Text("TÚ"),
                fila_apuesta,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        root_box = ft.Container(
            content=root_col,
            offset=ft.Offset(0, 0),
            animate_offset=80,
        )

        async def _sonido_victoria():
            audio.sonar_victoria()

        async def _animar_victoria():
            txt_status.color = "yellow"
            status_box.scale = 1.18
            status_box.rotate = ft.Rotate(-0.06)
            page.update()
            await asyncio.sleep(0.10)

            for dx in (0.02, -0.02, 0.018, -0.018, 0.014, -0.014, 0.0):
                root_box.offset = ft.Offset(dx, 0)
                page.update()
                await asyncio.sleep(0.05)

            status_box.scale = 1.0
            status_box.rotate = ft.Rotate(0.0)
            page.update()

        def aplicar_tamanos():
            """Ajusta las fuentes al ancho actual de la ventana."""
            txt_status.size = layout.tamano_texto(TAMANO_TITULO, page.width)
            txt_fichas.size = layout.tamano_texto(TAMANO_MARCADOR, page.width)
            txt_banca.size = layout.tamano_texto(14, page.width)
            txt_apuesta.size = layout.tamano_texto(16, page.width)

        def crear_carta_visual(carta, visible=True, por_aparecer=False):
            ancho = layout.ancho_de_carta(page.width)
            img_path = ruta_imagen(carta) if visible and carta is not None else DORSO
            contenedor = ft.Container(
                content=ft.Image(
                    src=img_path,
                    width=ancho,
                    height=layout.alto_de_carta(ancho),
                    fit=ft.ImageFit.CONTAIN,
                ),
                animate_scale=animacion.DURACION_APARICION,
                animate_opacity=animacion.DURACION_APARICION,
                scale=animacion.escala(),
                opacity=1,
                border_radius=10,
            )
            return animacion.ocultar(contenedor) if por_aparecer else contenedor

        async def actualizar_tablero(revelar_pc=False):
            """Redibuja el tablero completo, sin animación."""
            nonlocal pc_revelada
            pc_revelada = revelar_pc
            row_user.controls = [crear_carta_visual(c) for c in partida.mano_jugador]
            if revelar_pc:
                row_pc.controls = [crear_carta_visual(c) for c in partida.mano_pc]
            else:
                row_pc.controls = [crear_carta_visual(None, visible=False) for _ in partida.mano_pc]
            page.update()

        async def repartir_animado():
            """Reparte alternando entre las dos manos, como en la mesa."""
            nonlocal pc_revelada
            pc_revelada = False
            row_user.controls = [
                crear_carta_visual(c, por_aparecer=True) for c in partida.mano_jugador
            ]
            row_pc.controls = [
                crear_carta_visual(None, visible=False, por_aparecer=True) for _ in partida.mano_pc
            ]
            page.update()
            await animacion.aparecer(
                animacion.repartir_alternando(row_user.controls, row_pc.controls),
                page.update,
            )

        async def agregar_carta_animada(fila, carta, visible=True):
            """Suma una carta a una mano ya repartida, sin redibujar el resto."""
            nueva = crear_carta_visual(carta, visible=visible, por_aparecer=True)
            fila.controls.append(nueva)
            page.update()
            await animacion.aparecer([nueva], page.update)

        async def revelar_mano_pc():
            """Da vuelta las cartas de la PC, una por una."""
            nonlocal pc_revelada
            for contenedor, carta in zip(row_pc.controls, partida.mano_pc, strict=True):

                def mostrar(contenedor=contenedor, carta=carta):
                    contenedor.content.src = ruta_imagen(carta)

                await animacion.voltear(contenedor, mostrar, page.update)
            pc_revelada = True

        async def al_redimensionar(e=None):
            """Recalcula tamaños cuando cambia la ventana o rota el teléfono."""
            aplicar_tamanos()
            await actualizar_tablero(revelar_pc=pc_revelada)

        btn_p = ft.Button("PEDIR", disabled=True)
        btn_s = ft.Button("PLANTARSE", disabled=True)
        btn_r = ft.Button("REPARTIR", bgcolor="orange800", color="white")

        def mostrar_marcador():
            txt_fichas.value = f"Vos {partida.fichas_jugador} 🪙  ·  {partida.fichas_pc} 🪙 PC"
            txt_banca.value = texto_banca(partida.banca)
            txt_apuesta.value = f"Apuesta: {partida.apuesta} 🪙"

        def actualizar_botones_apuesta():
            """La apuesta solo se toca entre rondas y dentro del rango jugable."""
            entre_rondas = partida.estado is Estado.ESPERANDO_REPARTO
            btn_menos.disabled = not entre_rondas or partida.apuesta <= 1
            btn_mas.disabled = not entre_rondas or partida.apuesta >= partida.apuesta_maxima

        def restaurar_titulo():
            txt_status.value = TITULO
            txt_status.color = "white"
            txt_status.size = layout.tamano_texto(TAMANO_TITULO, page.width)

        async def alternar_silencio(e):
            silenciado = audio.alternar_silencio()
            btn_silencio.icon = ft.Icons.VOLUME_OFF if silenciado else ft.Icons.VOLUME_UP
            btn_silencio.tooltip = "Activar sonido" if silenciado else "Silenciar"
            page.update()

        async def cambiar_apuesta(delta):
            if partida.estado is not Estado.ESPERANDO_REPARTO:
                return
            objetivo = partida.apuesta + delta
            objetivo = max(1, min(objetivo, partida.apuesta_maxima))
            partida.apostar(objetivo)
            mostrar_marcador()
            actualizar_botones_apuesta()
            page.update()

        async def subir_apuesta(e):
            await cambiar_apuesta(PASO_APUESTA)

        async def bajar_apuesta(e):
            await cambiar_apuesta(-PASO_APUESTA)

        # Deshabilitar un boton no basta como guarda: entre el clic y el
        # redibujado en el cliente se cuelan mas eventos, y un doble clic manda
        # dos acciones. Cada handler comprueba el estado real de la partida y
        # descarta en silencio lo que llegue fuera de turno.

        async def repartir(e):
            if partida.estado is not Estado.ESPERANDO_REPARTO:
                return
            partida.repartir()
            txt_status.value = f"Puntaje: {partida.puntaje_jugador}"
            btn_p.disabled, btn_s.disabled, btn_r.disabled = False, False, True
            actualizar_botones_apuesta()
            await repartir_animado()

        async def pedir(e):
            if not partida.jugador_puede_pedir:
                return
            carta = partida.pedir()
            btn_p.disabled = not partida.jugador_puede_pedir
            txt_status.value = f"Puntaje: {partida.puntaje_jugador}"
            await agregar_carta_animada(row_user, carta)

        async def plantarse(e):
            if partida.estado is not Estado.TURNO_JUGADOR:
                return
            btn_p.disabled, btn_s.disabled = True, True
            partida.plantarse()

            while partida.pc_debe_pedir():
                txt_status.value = "PC pensando..."
                page.update()
                await asyncio.sleep(0.7)
                partida.pc_pide()
                await agregar_carta_animada(row_pc, None, visible=False)

            ronda = partida.resolver_ronda()
            gano_ronda = ronda.ganador is Rol.JUGADOR
            estadisticas.registrar_ronda(gano_ronda, ronda.fichas_jugador)

            await revelar_mano_pc()
            txt_status.value = MENSAJE_RONDA[ronda.resultado]
            mostrar_marcador()
            page.update()

            if gano_ronda:
                await asyncio.gather(_sonido_victoria(), _animar_victoria())

            await asyncio.sleep(1.5)

            if ronda.partida_terminada:
                estadisticas.registrar_partida(ronda.gano_el_jugador)
                stats.guardar(almacen, estadisticas)

                if ronda.gano_el_jugador:
                    txt_status.value = MENSAJE_GANASTE
                    txt_status.color = "gold"
                else:
                    txt_status.value = MENSAJE_PERDISTE
                    txt_status.color = "red"
                txt_status.size = layout.tamano_texto(TAMANO_CIERRE, page.width)
                page.update()
                await asyncio.sleep(3)

                partida.reiniciar()
                restaurar_titulo()
            else:
                partida.nueva_ronda()
                stats.guardar(almacen, estadisticas)

            mostrar_marcador()
            actualizar_botones_apuesta()
            btn_r.disabled = False
            page.update()

        btn_p.on_click = pedir
        btn_s.on_click = plantarse
        btn_r.on_click = repartir
        btn_silencio.on_click = alternar_silencio
        btn_menos.on_click = bajar_apuesta
        btn_mas.on_click = subir_apuesta
        page.on_resized = al_redimensionar

        # La partida puede venir de una sesión anterior de esta pantalla, y la
        # dificultad pudo cambiar en el menú.
        if partida.estado is not Estado.ESPERANDO_REPARTO:
            partida.reiniciar()
        partida.cambiar_estrategia(estrategia_para(dificultad))
        mostrar_marcador()
        actualizar_botones_apuesta()
        aplicar_tamanos()

        buttons_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True)
        buttons_row.controls = [btn_p, btn_s, btn_r]
        root_col.controls[-1] = buttons_row
        page.add(ft.SafeArea(content=root_box, expand=True))
        page.update()

    # Mostrar pantalla de inicio al cargar
    await mostrar_inicio()


# Ejecución
if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR)
