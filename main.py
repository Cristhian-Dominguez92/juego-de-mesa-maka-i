"""Punto de entrada del juego: capa de presentación (Flet).

La lógica de juego vive en `makai/core` y no depende de Flet. Este archivo se
limita a dibujar el estado de una `Partida` y a traducir clics en acciones.
"""

import asyncio
import os

import flet as ft

from makai.core import Carta, Estado, Partida, Resultado

# pygame solo existe en escritorio: en Android no hay wheel disponible, así que
# el juego debe seguir funcionando (mudo) sin él. Migrar a ft.Audio en la Fase 3.
try:
    import pygame

    pygame.mixer.init()
except Exception:
    pygame = None

# --- Rutas de assets ---
# Las imágenes se resuelven contra assets_dir de Flet (ver ft.app al final), por
# eso van sin el prefijo "assets/". pygame en cambio lee del sistema de archivos
# relativo al directorio de trabajo, y necesita la ruta completa.
ASSETS_DIR = "assets"
RECURSOS = "Recursos"
DORSO = f"{RECURSOS}/dorso.jpeg"

# Música de fondo con licencia libre. Ver CREDITS.md: el archivo no viene en el
# repositorio y hay que aportarlo. El juego funciona sin él.
MUSICA_FONDO = os.path.join(ASSETS_DIR, RECURSOS, "background_music.mp3")
SONIDO_VICTORIA = os.path.join(ASSETS_DIR, RECURSOS, "victoria.mp3")

TITULO = "¡JAHUGA Maka-'I!"

MENSAJE_RONDA = {
    Resultado.GANA_JUGADOR: "¡GANASTE ESTA RONDA! 🏆",
    Resultado.GANA_BANCA: "Gana la PC 🤖",
    Resultado.EMPATE: "Empate (Banca)",
}


def ruta_imagen(carta: Carta) -> str:
    return f"{RECURSOS}/{carta.nombre_archivo}"


# --- Aplicación Principal ---
async def main(page: ft.Page):
    page.title = "Maka-i Paraguayo"
    page.bgcolor = "#1a4a1a"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Variables de control de audio
    audio_bg_playing = False

    # Iniciar música de fondo
    def play_background_music():
        nonlocal audio_bg_playing
        if pygame is None or audio_bg_playing:
            return
        try:
            if os.path.exists(MUSICA_FONDO):
                pygame.mixer.music.load(MUSICA_FONDO)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.3)
                audio_bg_playing = True
                print("🎵 Música de fondo reproduciendo...")
        except Exception as e:
            print(f"Error con audio de fondo: {e}")

    partida = Partida()

    # Función para mostrar pantalla de inicio
    async def mostrar_inicio(e=None):
        page.clean()

        txt_welcome = ft.Text(
            "Bienvenidos al tradicional juego de mesa",
            size=28,
            weight=ft.FontWeight.BOLD,
            color="gold",
            text_align=ft.TextAlign.CENTER,
        )
        txt_game_name = ft.Text(
            "MAKA'I",
            size=60,
            weight=ft.FontWeight.BOLD,
            color="orange",
            text_align=ft.TextAlign.CENTER,
        )
        txt_subtitle = ft.Text(
            "¡El juego de cartas más emocionante!",
            size=18,
            color="yellow",
            text_align=ft.TextAlign.CENTER,
            italic=True,
        )

        btn_start = ft.Button(
            "COMENZAR JUEGO",
            on_click=mostrar_juego,
            bgcolor="orange800",
            color="white",
            width=300,
            height=50,
        )

        welcome_col = ft.Column(
            [txt_welcome, txt_game_name, txt_subtitle, ft.Divider(height=40), btn_start],
            # En una Column el eje principal es el vertical, asi que el centrado
            # vertical va en `alignment`. `vertical_alignment` solo existe en Row.
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        page.add(welcome_col)
        page.update()

    # Función para mostrar el juego principal
    async def mostrar_juego(e=None):
        page.clean()
        play_background_music()

        txt_status = ft.Text(TITULO, size=30, weight=ft.FontWeight.BOLD)
        txt_score = ft.Text("Usuario 0 - 0 PC", size=20, color="yellow")
        row_pc = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15)
        row_user = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15)

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

        root_col = ft.Column(
            [
                txt_score,
                status_box,
                ft.Text("PC"),
                row_pc,
                ft.Divider(height=40),
                row_user,
                ft.Text("TÚ"),
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
            if pygame is None:
                return
            try:
                if os.path.exists(SONIDO_VICTORIA):
                    pygame.mixer.Sound(SONIDO_VICTORIA).play()
                    await asyncio.sleep(2)
            except Exception:
                pass

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

        def crear_carta_visual(carta, visible=True):
            img_path = ruta_imagen(carta) if visible and carta is not None else DORSO
            return ft.Container(
                content=ft.Image(src=img_path, width=100, height=150),
                animate_scale=600,
                scale=1,
                border_radius=10,
            )

        async def actualizar_tablero(revelar_pc=False):
            row_user.controls = [crear_carta_visual(c) for c in partida.mano_jugador]
            if revelar_pc:
                row_pc.controls = [crear_carta_visual(c) for c in partida.mano_banca]
            else:
                row_pc.controls = [
                    crear_carta_visual(None, visible=False) for _ in partida.mano_banca
                ]
            page.update()

        btn_p = ft.Button("PEDIR", disabled=True)
        btn_s = ft.Button("PLANTARSE", disabled=True)
        btn_r = ft.Button("REPARTIR", bgcolor="orange800", color="white")

        def mostrar_marcador():
            txt_score.value = f"Usuario {partida.puntos_jugador} - {partida.puntos_banca} PC"

        def restaurar_titulo():
            txt_status.value = TITULO
            txt_status.color = "white"
            txt_status.size = 30

        async def repartir(e):
            nonlocal audio_bg_playing
            if pygame is not None and audio_bg_playing:
                try:
                    pygame.mixer.music.pause()
                    audio_bg_playing = False
                except Exception:
                    pass

            partida.repartir()
            txt_status.value = f"Puntaje: {partida.puntaje_jugador}"
            btn_p.disabled, btn_s.disabled, btn_r.disabled = False, False, True
            await actualizar_tablero()

        async def pedir(e):
            partida.pedir()
            btn_p.disabled = not partida.jugador_puede_pedir
            txt_status.value = f"Puntaje: {partida.puntaje_jugador}"
            await actualizar_tablero()

        async def plantarse(e):
            btn_p.disabled, btn_s.disabled = True, True
            partida.plantarse()

            while partida.banca_debe_pedir():
                txt_status.value = "PC pensando..."
                page.update()
                await asyncio.sleep(0.7)
                partida.banca_pide()

            ronda = partida.resolver_ronda()
            txt_status.value = MENSAJE_RONDA[ronda.resultado]
            mostrar_marcador()
            await actualizar_tablero(revelar_pc=True)

            if ronda.resultado is Resultado.GANA_JUGADOR:
                await asyncio.gather(_sonido_victoria(), _animar_victoria())

            await asyncio.sleep(1.5)

            if ronda.partida_terminada:
                if ronda.gano_el_jugador:
                    txt_status.value = "🏆 ¡FELICIDADES, ACABAS DE GANAR LA PARTIDA! 🏆"
                    txt_status.color = "gold"
                else:
                    txt_status.value = "😢 PERDISTE, ¡VUELVE A INTENTARLO!"
                    txt_status.color = "red"
                txt_status.size = 28
                page.update()
                await asyncio.sleep(3)

                partida.reiniciar()
                mostrar_marcador()
                restaurar_titulo()
            else:
                partida.nueva_ronda()

            btn_r.disabled = False
            page.update()

        btn_p.on_click = pedir
        btn_s.on_click = plantarse
        btn_r.on_click = repartir

        # La partida puede venir de una sesión anterior de esta pantalla.
        if partida.estado is not Estado.ESPERANDO_REPARTO:
            partida.reiniciar()
        mostrar_marcador()

        buttons_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
        buttons_row.controls = [btn_p, btn_s, btn_r]
        root_col.controls[-1] = buttons_row
        page.add(root_box)
        page.update()

    # Mostrar pantalla de inicio al cargar
    await mostrar_inicio()


# Ejecución
if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR)
