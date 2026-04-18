import flet as ft
import random
import asyncio

# --- Lógica de Juego ---
PALOS = ['Oros', 'Copas', 'Espadas', 'Bastos']
VALORES = ['1', '2', '3', '4', '5', '6', '7', '10', '11', '12']

class Carta:
    def __init__(self, palo, valor):
        self.palo = palo
        self.valor = valor
    
    def get_path(self):
        p = {'Oros': 'oro', 'Copas': 'copa', 'Espadas': 'espada', 'Bastos': 'basto'}
        # Usamos comillas simples adentro para no romper el texto
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
    
    # Estado inicial
    st = {"mazo": [], "m_u": [], "m_p": [], "p_u": 0, "p_p": 0}

    # Componentes Visuales
    txt_status = ft.Text("¡JAHUGA Maka-'I!", size=30, weight=ft.FontWeight.BOLD)
    txt_score = ft.Text("Usuario 0 - 0 PC", size=20, color="yellow")
    row_pc = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15)
    row_user = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15)

    def crear_carta_visual(carta, visible=True):
        img_path = carta.get_path() if visible else "Recursos/dorso.jpeg"
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
            row_pc.controls = [ft.Container(bgcolor="blue900", width=100, height=150, border_radius=10) for _ in st["m_p"]]
        page.update() # Sin await aquí

    # --- Acciones ---
    async def repartir(e):
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
            res = "¡GANASTE! 🏆"; st["p_u"] += 1
        elif pp > pu:
            res = "Gana la PC 🤖"; st["p_p"] += 1
        else:
            res = "Empate (Banca)"; st["p_p"] += 1
            
        txt_status.value = res
        txt_score.value = f"Usuario {st['p_u']} - {st['p_p']} PC"
        btn_r.disabled = False
        await actualizar_tablero(revelar_pc=True)

    # Botones con '=' corregido
    btn_p = ft.FilledButton("PEDIR", on_click=pedir, disabled=True)
    btn_s = ft.FilledButton("PLANTARSE", on_click=plantarse, disabled=True)
    btn_r = ft.ElevatedButton("REPARTIR", on_click=repartir, bgcolor="orange800", color="white")

    # Interfaz
    page.add(ft.Column([
        txt_score, txt_status, ft.Text("PC"), row_pc,
        ft.Divider(height=40), row_user, ft.Text("TÚ"),
        ft.Row([btn_p, btn_s, btn_r], alignment=ft.MainAxisAlignment.CENTER)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    
    page.update() # Sin await aquí

# Ejecución
# Al final de tu archivo main.py
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
