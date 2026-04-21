import flet as ft
import random
import asyncio
import os
import time
import subprocess
import platform

try:
    import pygame
    pygame.mixer.init()
except Exception:
    pygame = None

# --- Lógica de Juego ---
PALOS = ['Oros', 'Copas', 'Espadas', 'Bastos']
VALORES = ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']

class Carta:
    def __init__(self, palo, valor):
        self.palo = palo
        self.valor = valor
    
    def get_path(self):
        p = {'Oros': 'oro', 'Copas': 'copa', 'Espadas': 'espada', 'Bastos': 'basto'}
        return f"Recursos/{self.valor.lower()}_{p[self.palo]}.jpeg"

def calcular_puntaje(mano):
    figs = ['10', '11', '12']
    c_figs = sum(1 for c in mano if c.valor in figs)
    if len(mano) == 3 and c_figs == 3: 
        return 8.5
    total = sum(10 if c.valor in figs else int(c.valor) for c in mano)
    return total % 10 if total >= 10 else total

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
            bg_path = os.path.join("assets", "Recursos", "Arrocha Rave - Tnga (00).mp3")
            if os.path.exists(bg_path):
                pygame.mixer.music.load(bg_path)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.3)
                audio_bg_playing = True
                print("🎵 Música de fondo reproduciendo...")
        except Exception as e:
            print(f"Error con audio de fondo: {e}")
    
    # Estado inicial
    st = {"mazo": [], "m_u": [], "m_p": [], "p_u": 0, "p_p": 0}

    # Función para mostrar pantalla de inicio
    async def mostrar_inicio(e=None):
        page.clean()
        
        txt_welcome = ft.Text(
            "Bienvenidos al tradicional juego de mesa",
            size=28,
            weight=ft.FontWeight.BOLD,
            color="gold",
            text_align=ft.TextAlign.CENTER
        )
        txt_game_name = ft.Text(
            "MAKA'I",
            size=60,
            weight=ft.FontWeight.BOLD,
            color="orange",
            text_align=ft.TextAlign.CENTER
        )
        txt_subtitle = ft.Text(
            "¡El juego de cartas más emocionante!",
            size=18,
            color="yellow",
            text_align=ft.TextAlign.CENTER,
            italic=True
        )
        
        btn_start = ft.ElevatedButton(
            "COMENZAR JUEGO",
            on_click=mostrar_juego,
            bgcolor="orange800",
            color="white",
            width=300,
            height=50
        )
        
        welcome_col = ft.Column(
            [txt_welcome, txt_game_name, txt_subtitle, ft.Divider(height=40), btn_start],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )
        
        page.add(welcome_col)
        page.update()

    # Función para mostrar el juego principal
    async def mostrar_juego(e=None):
        page.clean()
        play_background_music()
        
        txt_status = ft.Text("¡JAHUGA Maka-'I!", size=30, weight=ft.FontWeight.BOLD)
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
                victory_path = os.path.join("assets", "Recursos", "victoria.mp3")
                if os.path.exists(victory_path):
                    pygame.mixer.Sound(victory_path).play()
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
            if visible and carta is not None:
                img_path = carta.get_path()
            else:
                img_path = "Recursos/dorso.jpeg"
            return ft.Container(
                content=ft.Image(src=img_path, width=100, height=150),
                animate_scale=600, 
                scale=1, 
                border_radius=10
            )

        async def actualizar_tablero(revelar_pc=False):
            row_user.controls = [crear_carta_visual(c) for c in st["m_u"]]
            if revelar_pc:
                row_pc.controls = [crear_carta_visual(c) for c in st["m_p"]]
            else:
                row_pc.controls = [crear_carta_visual(None, visible=False) for _ in st["m_p"]]
            page.update()

        btn_p = ft.FilledButton("PEDIR", disabled=True)
        btn_s = ft.FilledButton("PLANTARSE", disabled=True)
        btn_r = ft.ElevatedButton("REPARTIR", bgcolor="orange800", color="white")

        async def repartir(e):
            nonlocal audio_bg_playing
            if pygame is not None and audio_bg_playing:
                try:
                    pygame.mixer.music.pause()
                    audio_bg_playing = False
                except Exception:
                    pass
            
            st["mazo"] = [Carta(p, v) for p in PALOS for v in VALORES]
            random.shuffle(st["mazo"])
            st["m_u"] = [st["mazo"].pop(), st["mazo"].pop()]
            st["m_p"] = [st["mazo"].pop(), st["mazo"].pop()]
            txt_status.value = f"Puntaje: {calcular_puntaje(st['m_u'])}"
            btn_p.disabled, btn_s.disabled, btn_r.disabled = False, False, True
            await actualizar_tablero()

        async def pedir(e):
            st["m_u"].append(st["mazo"].pop())
            if len(st["m_u"]) >= 3: btn_p.disabled = True
            txt_status.value = f"Puntaje: {calcular_puntaje(st['m_u'])}"
            await actualizar_tablero()

        async def plantarse(e):
            btn_p.disabled, btn_s.disabled = True, True
            while calcular_puntaje(st["m_p"]) < 6 and len(st["m_p"]) < 3:
                txt_status.value = "PC pensando..."
                page.update()
                await asyncio.sleep(0.7)
                st["m_p"].append(st["mazo"].pop())
            
            pu, pp = calcular_puntaje(st["m_u"]), calcular_puntaje(st["m_p"])
            if pu > pp:
                res = "¡GANASTE ESTA RONDA! 🏆"; st["p_u"] += 1
            elif pp > pu:
                res = "Gana la PC 🤖"; st["p_p"] += 1
            else:
                res = "Empate (Banca)"; st["p_p"] += 1
                
            txt_status.value = res
            txt_score.value = f"Usuario {st['p_u']} - {st['p_p']} PC"
            await actualizar_tablero(revelar_pc=True)

            if res.startswith("¡GANASTE"):
                await asyncio.gather(_sonido_victoria(), _animar_victoria())

            await asyncio.sleep(1.5)
            
            if st["p_u"] >= 10:
                txt_status.value = "🏆 ¡FELICIDADES, ACABAS DE GANAR LA PARTIDA! 🏆"
                txt_status.color = "gold"
                txt_status.size = 28
                page.update()
                await asyncio.sleep(3)
                st["p_u"] = 0
                st["p_p"] = 0
                txt_score.value = f"Usuario {st['p_u']} - {st['p_p']} PC"
                txt_status.value = "¡JAHUGA Maka-'I!"
                txt_status.color = "white"
                txt_status.size = 30
                btn_r.disabled = False
                page.update()
            elif st["p_p"] >= 10:
                txt_status.value = "😢 PERDISTE, ¡VUELVE A INTENTARLO!"
                txt_status.color = "red"
                txt_status.size = 28
                page.update()
                await asyncio.sleep(3)
                st["p_u"] = 0
                st["p_p"] = 0
                txt_score.value = f"Usuario {st['p_u']} - {st['p_p']} PC"
                txt_status.value = "¡JAHUGA Maka-'I!"
                txt_status.color = "white"
                txt_status.size = 30
                btn_r.disabled = False
                page.update()
            else:
                btn_r.disabled = False
                page.update()

        btn_p.on_click = pedir
        btn_s.on_click = plantarse
        btn_r.on_click = repartir

        buttons_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
        buttons_row.controls = [btn_p, btn_s, btn_r]
        root_col.controls[-1] = buttons_row
        page.add(root_box)
        page.update()

    # Mostrar pantalla de inicio al cargar
    await mostrar_inicio()

# Ejecución
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
