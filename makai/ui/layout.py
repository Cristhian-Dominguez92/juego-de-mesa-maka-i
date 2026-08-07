"""Medidas responsive del tablero.

Aritmética pura, sin Flet: así se puede verificar que las cartas entran en
pantalla sin abrir una ventana. La UI usa estos valores para dimensionar los
controles.
"""

from __future__ import annotations

from makai.core.reglas import MAX_CARTAS_POR_MANO

#: Tamaño de carta en escritorio. Coincide con el diseño original.
ANCHO_MAXIMO_CARTA = 100.0

#: Por debajo de esto la figura de la carta deja de distinguirse.
ANCHO_MINIMO_CARTA = 44.0

#: Alto / ancho. Es la proporción real de los escaneos de la baraja Fournier
#: de 1878 (2434x3846). Las cartas españolas son más alargadas que las
#: francesas, así que este valor no es 1.5.
PROPORCION_CARTA = 1.58

#: Separación horizontal entre cartas de una misma mano.
SEPARACION_CARTAS = 15.0

#: Margen a cada lado del tablero.
MARGEN_LATERAL = 16.0

#: Por debajo de este ancho se considera pantalla de teléfono.
ANCHO_PANTALLA_ANGOSTA = 600.0


def ancho_de_carta(
    ancho_pantalla: float | None,
    cartas_por_mano: int = MAX_CARTAS_POR_MANO,
) -> float:
    """Ancho que debe tener cada carta para que la mano entre en pantalla.

    Se reparte el ancho disponible entre las cartas de la mano más grande
    posible, descontando márgenes y separaciones, y se acota entre el mínimo
    legible y el tamaño de escritorio.

    Si `ancho_pantalla` es None (Flet aún no reportó el tamaño), se asume
    escritorio.
    """
    if ancho_pantalla is None or ancho_pantalla <= 0:
        return ANCHO_MAXIMO_CARTA

    separaciones = SEPARACION_CARTAS * (cartas_por_mano - 1)
    disponible = ancho_pantalla - 2 * MARGEN_LATERAL - separaciones
    ancho = disponible / cartas_por_mano

    return max(ANCHO_MINIMO_CARTA, min(ANCHO_MAXIMO_CARTA, ancho))


def alto_de_carta(ancho: float) -> float:
    """Alto correspondiente a un ancho dado, conservando la proporción."""
    return ancho * PROPORCION_CARTA


def es_pantalla_angosta(ancho_pantalla: float | None) -> bool:
    return ancho_pantalla is not None and 0 < ancho_pantalla < ANCHO_PANTALLA_ANGOSTA


def tamano_texto(base: float, ancho_pantalla: float | None) -> float:
    """Escala un tamaño de fuente pensado para escritorio.

    En pantallas angostas se reduce a tres cuartos: los títulos de 60px del
    diseño original desbordan en un teléfono.
    """
    if not es_pantalla_angosta(ancho_pantalla):
        return base
    return round(base * 0.75, 1)


def ancho_ocupado(ancho_carta: float, cartas_por_mano: int = MAX_CARTAS_POR_MANO) -> float:
    """Ancho total que ocupa una mano completa, incluyendo separaciones."""
    return ancho_carta * cartas_por_mano + SEPARACION_CARTAS * (cartas_por_mano - 1)
