"""Punto de entrada del juego: capa de presentación (Flet).

La lógica de juego vive en `makai/core` y no depende de Flet. Este archivo se
limita a dibujar el estado de una `Partida` y a traducir clics.
"""

import asyncio

import flet as ft

from makai.ai import Dificultad, estrategia_para
from makai.core import Carta, Estado, Partida, Resultado, Rol, jere
from makai.ui import animacion, layout, textos
from makai.ui import estadisticas as stats
from makai.ui import personajes as pj
from makai.ui.audio import GestorAudio, descubrir_fuentes
from makai.ui.preferencias import cargar_dificultad, guardar_dificultad

# --- Rutas de assets ---
# Se resuelven contra assets_dir de Flet (ver ft.app al final), por eso van sin
# el prefijo "assets/".
ASSETS_DIR = "assets"
RECURSOS = "Recursos"
DORSO = f"{RECURSOS}/dorso.webp"
FONDO_MENU = "fondo_menu.png"
MESA_MADERA = "mesa_madera.png"
CARPETA_PERSONAJES = "Personajes"

TITULO = "¡JAHUGA Maka-'I!"

# --- Colores de la bandera paraguaya ---
ROJO = "#D52B1E"
BLANCO = "#FFFFFF"
AZUL = "#0038A8"

#: Fondo del menú: casi negro, para que el encaje del ñandutí se insinúe.
NEGRO_MENU = "#0A0A0C"

#: Tono base de la mesa, detrás de la textura de madera. Se ve mientras la
#: imagen carga, así que conviene que sea del mismo color y no verde.
MADERA_BASE = "#8a6742"

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


def ruta_personaje(personaje: pj.Personaje) -> str:
    return f"{CARPETA_PERSONAJES}/{personaje.archivo}"


def titulo_con_contorno(texto: str, tamano: float, color: str) -> ft.Stack:
    """Texto de color con contorno blanco.

    Flutter no dibuja relleno y contorno en una sola pasada, así que se apilan
    dos textos idénticos: el de abajo solo traza el borde, el de arriba rellena.
    """
    trazo = ft.Text(
        texto,
        size=tamano,
        weight=ft.FontWeight.BOLD,
        style=ft.TextStyle(
            foreground=ft.Paint(
                color=BLANCO,
                style=ft.PaintingStyle.STROKE,
                stroke_width=max(3.0, tamano * 0.09),
            )
        ),
    )
    relleno = ft.Text(texto, size=tamano, weight=ft.FontWeight.BOLD, color=color)
    return ft.Stack([trazo, relleno])


def boton_menu(texto: str, color: str, on_click, ancho: float) -> ft.Button:
    """Botón ancho al estilo de la bandera: fondo de color y borde blanco."""
    return ft.Button(
        texto,
        on_click=on_click,
        width=ancho,
        height=54,
        style=ft.ButtonStyle(
            bgcolor=color,
            color=BLANCO,
            side=ft.BorderSide(2, BLANCO),
            shape=ft.RoundedRectangleBorder(radius=6),
            text_style=ft.TextStyle(size=19, weight=ft.FontWeight.BOLD),
        ),
    )


def ficha_personaje(personaje: pj.Personaje, alineado_a_la_izquierda: bool) -> ft.Row:
    """Retrato y nombre de quien juega ese lado de la mesa.

    Van sobre un panel oscuro: la mesa es de madera clara y el texto blanco a
    secas no se leería.
    """
    contenido = [
        ft.Container(
            content=ft.Image(src=ruta_personaje(personaje), width=44, height=44),
            border_radius=22,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.all(2, BLANCO),
        ),
        ft.Text(personaje.nombre, color=BLANCO, weight=ft.FontWeight.BOLD, size=15),
    ]
    if not alineado_a_la_izquierda:
        contenido.reverse()

    return ft.Row(
        [
            ft.Container(
                content=ft.Row(contenido, spacing=8, tight=True),
                bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.BLACK),
                border_radius=24,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
            )
        ],
        alignment=(
            ft.MainAxisAlignment.START if alineado_a_la_izquierda else ft.MainAxisAlignment.END
        ),
    )


def franja_bandera(alto: float = 7) -> ft.Column:
    """Las tres bandas horizontales de la bandera paraguaya."""
    return ft.Column(
        [ft.Container(bgcolor=c, height=alto, expand=True) for c in (ROJO, BLANCO, AZUL)],
        spacing=0,
        tight=True,
    )


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
    page.bgcolor = NEGRO_MENU
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    # En pantallas bajas el tablero no entra completo: mejor poder desplazarlo
    # que recortarlo.
    page.scroll = ft.ScrollMode.AUTO

    audio = GestorAudio(page, **descubrir_fuentes(ASSETS_DIR, RECURSOS))
    almacen = page.client_storage
    estadisticas = stats.cargar(almacen)
    dificultad = cargar_dificultad(almacen)
    personaje = pj.cargar(almacen)
    # Jere: cuántos se sientan a la mesa. Los rivales toman personajes
    # prestados, así que no puede haber más jugadores que personajes.
    maximo_jere = min(jere.MAXIMO_JUGADORES, len(pj.PERSONAJES))
    cantidad_jere = jere.MINIMO_JUGADORES
    partida = Partida(estrategia_pc=estrategia_para(dificultad))

    # Función para mostrar pantalla de inicio
    async def mostrar_inicio(e=None):
        nonlocal dificultad
        page.clean()
        page.on_resized = None

        page.bgcolor = NEGRO_MENU
        # Botones anchos pero acotados: a pantalla completa en un monitor
        # quedarían absurdamente largos.
        ancho_boton = min(420.0, (page.width or 480) - 56)

        # El título va en dos líneas y con los colores de la bandera, como los
        # letreros de los juegos de cartas locales.
        titulo = ft.Column(
            [
                titulo_con_contorno("MAKA'I", layout.tamano_texto(72, page.width), ROJO),
                titulo_con_contorno("PARAGUAYO", layout.tamano_texto(46, page.width), AZUL),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
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
            width=ancho_boton,
            border_color=BLANCO,
            color=BLANCO,
            data="dificultad",
        )

        txt_stats = ft.Text(
            resumen_estadisticas(estadisticas),
            size=layout.tamano_texto(13, page.width),
            color="white60",
            text_align=ft.TextAlign.CENTER,
            data="stats",
        )

        btn_start = boton_menu("PARTIDA RÁPIDA", ROJO, mostrar_juego, ancho_boton)
        btn_start.data = "btn_jugar"
        btn_reglas = boton_menu("CÓMO SE JUEGA", AZUL, mostrar_reglas, ancho_boton)
        btn_reglas.data = "btn_reglas"
        btn_jere = boton_menu("MAKA'I JERE", AZUL, mostrar_jere, ancho_boton)
        btn_jere.data = "btn_jere"
        btn_personaje = boton_menu("MI PERSONAJE", ROJO, mostrar_personajes, ancho_boton)
        btn_personaje.data = "btn_personaje"

        welcome_col = ft.Column(
            [
                titulo,
                ft.Container(height=18),
                btn_start,
                btn_jere,
                btn_personaje,
                btn_reglas,
                ft.Container(height=6),
                dd_dificultad,
                txt_stats,
            ],
            # En una Column el eje principal es el vertical, asi que el centrado
            # vertical va en `alignment`. `vertical_alignment` solo existe en Row.
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        fondo = ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=welcome_col, expand=True, padding=20),
                    franja_bandera(),
                ],
                spacing=0,
                expand=True,
            ),
            image=ft.DecorationImage(src=FONDO_MENU, repeat=ft.ImageRepeat.REPEAT),
            expand=True,
        )

        page.add(ft.SafeArea(content=fondo, expand=True))
        page.update()

    # Pantalla de selección de personaje
    async def mostrar_personajes(e=None):
        nonlocal personaje
        page.clean()
        page.on_resized = None
        page.bgcolor = NEGRO_MENU

        async def elegir(e):
            nonlocal personaje
            personaje = pj.por_id(e.control.data.removeprefix("personaje_"), personaje)
            pj.guardar(almacen, personaje)
            # Se vuelve a dibujar para que el marco se mueva al recién elegido.
            await mostrar_personajes()

        tarjetas = []
        for candidato in pj.PERSONAJES:
            elegido = candidato == personaje
            tarjetas.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(src=ruta_personaje(candidato), width=96, height=96),
                            ft.Text(
                                candidato.nombre,
                                color=BLANCO,
                                weight=ft.FontWeight.BOLD,
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        tight=True,
                    ),
                    on_click=elegir,
                    data=f"personaje_{candidato.id}",
                    padding=10,
                    border_radius=10,
                    border=ft.border.all(3, ROJO if elegido else "transparent"),
                    bgcolor=ft.Colors.with_opacity(0.30 if elegido else 0.12, ft.Colors.WHITE),
                    ink=True,
                )
            )

        contenido = ft.Column(
            [
                ft.Text(
                    "Elegí tu personaje",
                    size=layout.tamano_texto(30, page.width),
                    weight=ft.FontWeight.BOLD,
                    color=BLANCO,
                    data="titulo_personajes",
                ),
                ft.Container(height=10),
                ft.Row(
                    tarjetas,
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                    run_spacing=12,
                ),
                ft.Container(height=16),
                boton_menu("VOLVER", AZUL, mostrar_inicio, min(300.0, (page.width or 480) - 56)),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )
        contenido.controls[-1].data = "btn_volver_personajes"

        fondo = ft.Container(
            content=ft.Container(content=contenido, expand=True, padding=20),
            image=ft.DecorationImage(src=FONDO_MENU, repeat=ft.ImageRepeat.REPEAT),
            expand=True,
        )
        page.add(ft.SafeArea(content=fondo, expand=True))
        page.update()

    # --- Maka'i Jere: de cuatro para arriba, sin banca y con pozo al centro ---
    async def mostrar_jere(e=None):
        nonlocal cantidad_jere
        page.clean()
        page.bgcolor = MADERA_BASE
        page.on_resized = None

        # Los rivales toman prestados los personajes que el jugador no usa.
        rivales = [p for p in pj.PERSONAJES if p != personaje][: cantidad_jere - 1]
        nombres = [personaje.nombre] + [r.nombre for r in rivales]
        caras = {personaje.nombre: personaje} | {r.nombre: r for r in rivales}

        partida_jere = jere.PartidaJere(nombres, estrategia_pc=estrategia_para(dificultad))

        txt_pozo = ft.Text(
            "",
            size=layout.tamano_texto(22, page.width),
            weight=ft.FontWeight.BOLD,
            color="amber300",
            data="pozo_jere",
        )
        txt_aviso = ft.Text(
            "",
            size=layout.tamano_texto(15, page.width),
            weight=ft.FontWeight.BOLD,
            color=BLANCO,
            text_align=ft.TextAlign.CENTER,
            data="aviso_jere",
        )
        txt_apuesta = ft.Text(color=BLANCO, data="apuesta_jere")
        txt_fichas = ft.Text(color="amber300", weight=ft.FontWeight.BOLD, data="fichas_jere")
        col_rivales = ft.Column(spacing=6, data="rivales_jere")
        row_mano = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=layout.SEPARACION_CARTAS,
            data="mano_jere",
        )

        btn_carta = ft.Button("CARTA Y PIE", disabled=True, data="btn_carta_pie")
        btn_planto = ft.Button("PLANTO Y PIE", disabled=True, data="btn_planto_pie")
        btn_repartir = ft.Button(
            "REPARTIR", bgcolor="orange800", color=BLANCO, data="btn_repartir_jere"
        )
        btn_menos = ft.IconButton(icon=ft.Icons.REMOVE, icon_color=BLANCO, data="jere_menos")
        btn_mas = ft.IconButton(icon=ft.Icons.ADD, icon_color=BLANCO, data="jere_mas")

        async def cambiar_cantidad(e):
            nonlocal cantidad_jere
            cantidad_jere = int(dd_cantidad.value)
            # La mesa cambia de tamaño: se rearma la pantalla entera.
            await mostrar_jere()

        dd_cantidad = ft.Dropdown(
            label="Jugadores",
            value=str(cantidad_jere),
            options=[
                ft.DropdownOption(key=str(n), text=f"{n} jugadores")
                for n in range(jere.MINIMO_JUGADORES, maximo_jere + 1)
            ],
            on_change=cambiar_cantidad,
            width=150,
            border_color=BLANCO,
            color=BLANCO,
            data="cantidad_jere",
        )

        def panel(hijo):
            return ft.Container(
                content=hijo,
                bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.BLACK),
                border_radius=10,
                padding=8,
            )

        def carta_visual(carta, visible):
            # Con cuatro o más manos en pantalla las cartas van más chicas.
            ancho = layout.ancho_de_carta(page.width) * 0.62
            return ft.Image(
                src=ruta_imagen(carta) if visible and carta else DORSO,
                width=ancho,
                height=layout.alto_de_carta(ancho),
                fit=ft.ImageFit.CONTAIN,
            )

        def fila_rival(jugador):
            cara = caras[jugador.nombre]
            turno = partida_jere.turno
            es_turno = turno is not None and turno.nombre == jugador.nombre
            revelar = partida_jere.estado in (
                jere.Estado.RONDA_TERMINADA,
                jere.Estado.PARTIDA_TERMINADA,
            )
            detalle = f"{jugador.fichas} 🪙"
            if jugador.declaracion:
                detalle += f"  ·  {jugador.declaracion.value}"

            return panel(
                ft.Row(
                    [
                        ft.Image(src=ruta_personaje(cara), width=32, height=32),
                        ft.Column(
                            [
                                ft.Text(
                                    jugador.nombre,
                                    color="amber300" if es_turno else BLANCO,
                                    weight=ft.FontWeight.BOLD,
                                    size=13,
                                ),
                                ft.Text(detalle, color="white70", size=11),
                            ],
                            spacing=0,
                            tight=True,
                        ),
                        ft.Row(
                            [carta_visual(c, revelar) for c in jugador.mano],
                            spacing=4,
                            tight=True,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        def dibujar():
            col_rivales.controls = [
                fila_rival(j)
                for j in partida_jere.jugadores
                if not j.es_humano and (j.sigue_en_partida or j.mano)
            ]

            humano = partida_jere.humano
            row_mano.controls = [carta_visual(c, True) for c in humano.mano]

            txt_pozo.value = f"POZO  {partida_jere.pozo} 🪙"
            txt_apuesta.value = f"Cada uno pone {partida_jere.apuesta} 🪙"
            txt_fichas.value = f"{humano.fichas} 🪙"

            entre_rondas = partida_jere.estado is jere.Estado.ESPERANDO_REPARTO
            btn_menos.disabled = not entre_rondas or partida_jere.apuesta <= 1
            btn_mas.disabled = (
                not entre_rondas or partida_jere.apuesta >= partida_jere.apuesta_maxima
            )
            btn_repartir.disabled = not entre_rondas
            dd_cantidad.disabled = not entre_rondas

            mi_turno = partida_jere.es_turno_del_humano
            btn_carta.disabled = not (mi_turno and humano.puede_pedir)
            btn_planto.disabled = not mi_turno
            if mi_turno:
                txt_aviso.value = "Te toca: ¿carta o planto?"
            page.update()

        async def correr_turnos_de_la_pc():
            """Las PC declaran una por una, cantando en voz alta.

            Sin anunciar cada canto, las cartas que piden aparecen boca abajo
            sin explicación y parece que se hubiera repartido de más. Todos
            reciben dos: la tercera sale de un `carta y pie`.
            """
            while partida_jere.turno is not None and not partida_jere.es_turno_del_humano:
                quien = partida_jere.turno.nombre
                await asyncio.sleep(0.9)
                declaracion = partida_jere.declaracion_de_la_pc()
                partida_jere.declarar(declaracion)
                txt_aviso.value = f"{quien}: {declaracion.value}"
                dibujar()
                await asyncio.sleep(0.4)

        async def cerrar_ronda():
            resultado = partida_jere.resolver_ronda()

            if resultado.hubo_desempate:
                txt_aviso.value = f"Empate entre {', '.join(resultado.empatados)} — desempate"
                dibujar()
                await asyncio.sleep(1.6)

            gano_el_humano = resultado.ganador.es_humano
            txt_aviso.value = (
                f"¡Te llevás el pozo de {resultado.pozo} 🪙!"
                if gano_el_humano
                else f"{resultado.ganador.nombre} se lleva {resultado.pozo} 🪙"
            )
            if gano_el_humano:
                audio.sonar_victoria()
            dibujar()
            await asyncio.sleep(1.8)

            if resultado.partida_terminada:
                txt_aviso.value = (
                    "🏆 ¡GANASTE LA PARTIDA!"
                    if gano_el_humano
                    else f"Ganó {resultado.ganador.nombre}. ¡Otra vez será!"
                )
                dibujar()
                await asyncio.sleep(2.5)
                partida_jere.reiniciar()
                txt_aviso.value = ""
            else:
                partida_jere.nueva_ronda()
            dibujar()

        async def seguir_hasta_el_final():
            await correr_turnos_de_la_pc()
            if partida_jere.turno is None and partida_jere.estado is jere.Estado.DECLARANDO:
                await cerrar_ronda()

        async def repartir(e):
            if partida_jere.estado is not jere.Estado.ESPERANDO_REPARTO:
                return
            audio.sonar_barajeo()
            txt_aviso.value = "Dos cartas para cada uno"
            partida_jere.repartir()
            dibujar()
            await asyncio.sleep(0.7)
            await seguir_hasta_el_final()

        async def declarar(declaracion):
            if not partida_jere.es_turno_del_humano:
                return
            partida_jere.declarar(declaracion)
            txt_aviso.value = f"{personaje.nombre}: {declaracion.value}"
            dibujar()
            await asyncio.sleep(0.4)
            await seguir_hasta_el_final()

        async def pedir_carta(e):
            await declarar(jere.Declaracion.CARTA)

        async def plantarse(e):
            await declarar(jere.Declaracion.PLANTO)

        async def cambiar_apuesta(delta):
            if partida_jere.estado is not jere.Estado.ESPERANDO_REPARTO:
                return
            objetivo = max(1, min(partida_jere.apuesta + delta, partida_jere.apuesta_maxima))
            partida_jere.apostar(objetivo)
            dibujar()

        async def subir(e):
            await cambiar_apuesta(PASO_APUESTA)

        async def bajar(e):
            await cambiar_apuesta(-PASO_APUESTA)

        btn_repartir.on_click = repartir
        btn_carta.on_click = pedir_carta
        btn_planto.on_click = plantarse
        btn_menos.on_click = bajar
        btn_mas.on_click = subir

        contenido = ft.Column(
            [
                ft.Row(
                    [
                        panel(txt_pozo),
                        dd_cantidad,
                        ft.Button("MENÚ", on_click=mostrar_inicio, data="btn_menu_jere"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    wrap=True,
                ),
                col_rivales,
                panel(txt_aviso),
                row_mano,
                panel(
                    ft.Row(
                        [
                            ft.Image(src=ruta_personaje(personaje), width=32, height=32),
                            ft.Text(personaje.nombre, color=BLANCO, weight=ft.FontWeight.BOLD),
                            txt_fichas,
                        ],
                        spacing=8,
                        tight=True,
                    )
                ),
                ft.Row(
                    [btn_menos, txt_apuesta, btn_mas],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
                ft.Row(
                    [btn_carta, btn_planto, btn_repartir],
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True,
                    spacing=8,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        mesa = ft.Container(
            content=ft.Container(content=contenido, padding=14),
            image=ft.DecorationImage(src=MESA_MADERA, repeat=ft.ImageRepeat.REPEAT),
            expand=True,
        )
        page.add(ft.SafeArea(content=mesa, expand=True))
        dibujar()
        audio.registrar()
        audio.iniciar_musica()

    # Pantalla de reglas
    async def mostrar_reglas(e=None):
        page.clean()
        page.on_resized = None
        page.bgcolor = NEGRO_MENU

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
                    data="titulo_reglas",
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
                    data="btn_volver",
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
        page.bgcolor = MADERA_BASE
        # La música se arranca al final, cuando la pantalla ya está montada:
        # `page.clean()` da de baja los controles del overlay y reproducir con
        # el control desregistrado no hace nada.

        # La PC juega con otra cara: ver la propia del otro lado de la mesa
        # rompe la ilusión.
        rival = pj.rival_de(personaje)

        pc_revelada = False

        txt_status = ft.Text(TITULO, weight=ft.FontWeight.BOLD, data="estado")
        txt_fichas = ft.Text(color="yellow", weight=ft.FontWeight.BOLD, data="marcador")
        txt_banca = ft.Text(color="white70", italic=True, data="banca")
        txt_apuesta = ft.Text(color="white", data="apuesta")
        row_pc = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=layout.SEPARACION_CARTAS,
            data="cartas_pc",
        )
        row_user = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=layout.SEPARACION_CARTAS,
            data="cartas_jugador",
        )

        btn_silencio = ft.IconButton(
            icon=ft.Icons.VOLUME_OFF if audio.silenciado else ft.Icons.VOLUME_UP,
            tooltip="Activar sonido" if audio.silenciado else "Silenciar",
            icon_color="white",
            data="silencio",
        )
        btn_menos = ft.IconButton(
            icon=ft.Icons.REMOVE, tooltip="Bajar apuesta", icon_color="white", data="apuesta_menos"
        )
        btn_mas = ft.IconButton(
            icon=ft.Icons.ADD, tooltip="Subir apuesta", icon_color="white", data="apuesta_mas"
        )

        status_box = ft.Container(
            content=txt_status,
            padding=10,
            border_radius=12,
            # Sobre la madera un velo blanco es invisible: el panel va
            # oscuro para que el texto blanco se lea.
            bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
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
                ficha_personaje(rival, alineado_a_la_izquierda=False),
                row_pc,
                ft.Divider(height=30),
                row_user,
                ficha_personaje(personaje, alineado_a_la_izquierda=True),
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
                # Las imágenes vienen sin alfa (ver tools/optimizar_imagenes.py),
                # así que el redondeo de las esquinas lo hace el recorte de acá.
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
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

        btn_p = ft.Button("PEDIR", disabled=True, data="btn_pedir")
        btn_s = ft.Button("PLANTARSE", disabled=True, data="btn_plantarse")
        btn_r = ft.Button("REPARTIR", bgcolor="orange800", color="white", data="btn_repartir")

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
            audio.sonar_barajeo()
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
        mesa = ft.Container(
            content=root_box,
            image=ft.DecorationImage(src=MESA_MADERA, repeat=ft.ImageRepeat.REPEAT),
            expand=True,
            alignment=ft.alignment.center,
        )
        page.add(ft.SafeArea(content=mesa, expand=True))
        page.update()

        # Recién ahora, con la pantalla montada y los controles de audio dados
        # de alta otra vez, tiene sentido reproducir.
        audio.registrar()
        audio.iniciar_musica()

    # Mostrar pantalla de inicio al cargar
    await mostrar_inicio()


# Ejecución
if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR)
