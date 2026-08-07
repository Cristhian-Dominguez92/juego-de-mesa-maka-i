"""Dibujo de la baraja española, sin dependencias externas.

Todo se genera con aritmética: no hay fuentes, ni librerías de imagen, ni
assets de terceros. El resultado es enteramente nuestro (ver CREDITS.md).

El estilo es geométrico a propósito. Una baraja tradicional lleva figuras
ilustradas, que no se pueden dibujar con círculos y rectángulos; acá la sota,
el caballo y el rey se distinguen por el número de la esquina y por unos
galones bajo el palo central.

Este módulo solo dibuja. `tools/generar_cartas.py` es el que escribe los
archivos.
"""

from __future__ import annotations

import math
import struct
import zlib
from collections.abc import Callable

# --- Medidas ------------------------------------------------------------------

ANCHO, ALTO = 300, 450
RADIO_ESQUINA = 22
GROSOR_BORDE = 5
MARGEN_INTERIOR = 26

#: Muestras por eje al rasterizar una figura. 3x3 alcanza para bordes suaves.
MUESTRAS = 3

# --- Colores ------------------------------------------------------------------

MARFIL = (246, 241, 228)
TINTA = (38, 38, 44)
DORADO = (196, 154, 52)
ROJO = (168, 46, 46)
VERDE = (40, 104, 62)
AZUL = (44, 78, 140)
FONDO_DORSO = (26, 74, 26)

#: Color de cada palo. Oros y copas en cálidos, espadas y bastos en fríos.
COLOR_PALO = {
    "oro": DORADO,
    "copa": ROJO,
    "espada": AZUL,
    "basto": VERDE,
}


# --- Lienzo -------------------------------------------------------------------


class Lienzo:
    """Imagen RGB en memoria, con mezcla alfa."""

    def __init__(self, ancho: int, alto: int, fondo: tuple[int, int, int]):
        self.ancho = ancho
        self.alto = alto
        self.px = bytearray(bytes(fondo) * (ancho * alto))

    def mezclar(self, x: int, y: int, color: tuple[int, int, int], alfa: float) -> None:
        if alfa <= 0 or not (0 <= x < self.ancho and 0 <= y < self.alto):
            return
        i = (y * self.ancho + x) * 3
        if alfa >= 1:
            self.px[i : i + 3] = bytes(color)
            return
        for c in range(3):
            fondo = self.px[i + c]
            self.px[i + c] = round(fondo + (color[c] - fondo) * alfa)

    def pintar(
        self,
        x0: int,
        y0: int,
        ancho: int,
        alto: int,
        forma: Callable[[float, float], float],
        color: tuple[int, int, int],
        muestras: int = MUESTRAS,
    ) -> None:
        """Rasteriza `forma` en un rectángulo.

        `forma(x, y)` recibe coordenadas de 0 a 1 y devuelve cuánta tinta pone
        en ese punto, de 0 a 1.
        """
        total = muestras * muestras
        for py in range(alto):
            for px in range(ancho):
                cobertura = 0.0
                for sy in range(muestras):
                    for sx in range(muestras):
                        u = (px + (sx + 0.5) / muestras) / ancho
                        v = (py + (sy + 0.5) / muestras) / alto
                        cobertura += forma(u, v)
                if cobertura:
                    self.mezclar(x0 + px, y0 + py, color, cobertura / total)

    def guardar(self, ruta) -> None:
        escribir_png(ruta, self.ancho, self.alto, bytes(self.px))


def escribir_png(ruta, ancho: int, alto: int, rgb: bytes) -> None:
    """Escribe un PNG RGB de 8 bits."""

    def bloque(tipo: bytes, datos: bytes) -> bytes:
        cuerpo = tipo + datos
        return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", zlib.crc32(cuerpo))

    crudo = b"".join(b"\x00" + rgb[y * ancho * 3 : (y + 1) * ancho * 3] for y in range(alto))
    ruta.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + bloque(b"IDAT", zlib.compress(crudo, 9))
        + bloque(b"IEND", b"")
    )


# --- Formas de los palos ------------------------------------------------------
# Cada función recibe (x, y) de 0 a 1 dentro de su recuadro y devuelve cobertura.


def _anillo(x, y, cx, cy, radio, grosor) -> float:
    d = math.hypot(x - cx, y - cy)
    return 1.0 if abs(d - radio) <= grosor else 0.0


def _disco(x, y, cx, cy, radio) -> float:
    return 1.0 if math.hypot(x - cx, y - cy) <= radio else 0.0


def _caja(x, y, x0, y0, x1, y1) -> float:
    return 1.0 if x0 <= x <= x1 and y0 <= y <= y1 else 0.0


def palo_oro(x: float, y: float) -> float:
    """Moneda: disco con un anillo interior."""
    if _disco(x, y, 0.5, 0.5, 0.44) and not _disco(x, y, 0.5, 0.5, 0.30):
        return 1.0
    if _anillo(x, y, 0.5, 0.5, 0.19, 0.035):
        return 1.0
    return _disco(x, y, 0.5, 0.5, 0.07)


def palo_copa(x: float, y: float) -> float:
    """Copa: cuenco, tallo y pie."""
    # Cuenco: media elipse hacia abajo.
    if y <= 0.52:
        dx, dy = (x - 0.5) / 0.34, (y - 0.20) / 0.34
        if dx * dx + dy * dy <= 1 and y >= 0.16:
            return 1.0
    if _caja(x, y, 0.16, 0.14, 0.84, 0.19):  # borde del cuenco
        return 1.0
    if _caja(x, y, 0.45, 0.52, 0.55, 0.76):  # tallo
        return 1.0
    if _caja(x, y, 0.26, 0.76, 0.74, 0.84):  # pie
        return 1.0
    return 0.0


def palo_espada(x: float, y: float) -> float:
    """Espada apuntando hacia arriba: punta, hoja larga, guarda y empuñadura."""
    if 0.04 <= y <= 0.14:  # punta triangular
        mitad = 0.055 * (y - 0.04) / 0.10
        if abs(x - 0.5) <= mitad:
            return 1.0
    if 0.14 <= y <= 0.66 and abs(x - 0.5) <= 0.055:  # hoja
        return 1.0
    if 0.66 <= y <= 0.73 and abs(x - 0.5) <= 0.26:  # guarda
        return 1.0
    if _caja(x, y, 0.455, 0.73, 0.545, 0.91):  # empuñadura
        return 1.0
    return _disco(x, y, 0.5, 0.93, 0.062)  # pomo


def palo_basto(x: float, y: float) -> float:
    """Bastón: tronco grueso que se ensancha hacia abajo, con muñones."""
    if 0.08 <= y <= 0.92:
        mitad = 0.085 + 0.055 * (y - 0.08) / 0.84
        if abs(x - 0.5) <= mitad:
            return 1.0
    # Muñones de las ramas cortadas, alternados a los costados.
    for cy, lado in ((0.30, -1), (0.55, 1)):
        if _disco(x, y, 0.5 + lado * 0.155, cy, 0.075):
            return 1.0
    return 0.0


PALOS = {
    "oro": palo_oro,
    "copa": palo_copa,
    "espada": palo_espada,
    "basto": palo_basto,
}


# --- Dígitos ------------------------------------------------------------------
# Mapa de bits de 5x7 dibujado a mano. Se probó antes con siete segmentos, pero
# el 7 se leía como "⌐" y el 1 como una barra suelta: la forma real de cada
# dígito es más legible, sobre todo cuando la carta se ve chica en el celular.

ALTO_DIGITO = 7
ANCHO_DIGITO = 5

_MAPA = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
}


def digito(caracter: str) -> Callable[[float, float], float]:
    filas = _MAPA[caracter]

    def forma(x: float, y: float) -> float:
        col = int(x * ANCHO_DIGITO)
        fila = int(y * ALTO_DIGITO)
        if not (0 <= col < ANCHO_DIGITO and 0 <= fila < ALTO_DIGITO):
            return 0.0
        return 1.0 if filas[fila][col] == "1" else 0.0

    return forma
