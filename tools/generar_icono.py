"""Genera el ícono de la aplicación, sin dependencias externas.

El diseño es una moneda de oros —el palo más reconocible de la baraja
española— sobre el verde de la mesa. Es geométrico a propósito: se dibuja con
aritmética, sin fuentes ni librerías de imagen, así que el resultado es
enteramente nuestro y no agrega problemas de licencia (ver CREDITS.md).

Uso:
    python tools/generar_icono.py
"""

from __future__ import annotations

import math
import pathlib
import struct
import zlib

LADO = 512

#: Muestras por eje para suavizar los bordes. 3x3 alcanza y es rápido.
SUPERMUESTREO = 3

VERDE_MESA = (26, 74, 26)
VERDE_CLARO = (34, 96, 34)
ORO = (212, 160, 23)
ORO_OSCURO = (150, 108, 12)

#: Radios relativos al lado, de afuera hacia adentro.
RADIO_MONEDA = 0.34
RADIO_ANILLO = 0.27
RADIO_CENTRO = 0.13

#: Cantidad de rayos del borde dentado de la moneda.
RAYOS = 16
PROFUNDIDAD_RAYOS = 0.022


def mezclar(fondo, frente, alfa):
    return tuple(round(f * (1 - alfa) + d * alfa) for f, d in zip(fondo, frente, strict=True))


def color_en(x: float, y: float) -> tuple[int, int, int]:
    """Color del punto (x, y), en coordenadas de 0 a 1."""
    dx, dy = x - 0.5, y - 0.5
    distancia = math.hypot(dx, dy)
    angulo = math.atan2(dy, dx)

    # Fondo con un degradado suave hacia las esquinas.
    fondo = mezclar(VERDE_CLARO, VERDE_MESA, min(1.0, distancia * 1.6))

    # Borde dentado: el radio de la moneda ondula con el angulo.
    borde = RADIO_MONEDA + PROFUNDIDAD_RAYOS * math.cos(angulo * RAYOS)

    if distancia > borde:
        return fondo
    if distancia > RADIO_ANILLO:
        return ORO
    if distancia > RADIO_CENTRO:
        return ORO_OSCURO
    return ORO


def render(lado: int = LADO, muestras: int = SUPERMUESTREO) -> bytes:
    """Devuelve los datos RGB de la imagen, fila por fila."""
    filas = []
    total = muestras * muestras
    for py in range(lado):
        fila = bytearray()
        for px in range(lado):
            acumulado = [0, 0, 0]
            for sy in range(muestras):
                for sx in range(muestras):
                    x = (px + (sx + 0.5) / muestras) / lado
                    y = (py + (sy + 0.5) / muestras) / lado
                    for i, canal in enumerate(color_en(x, y)):
                        acumulado[i] += canal
            fila.extend(bytes(c // total for c in acumulado))
        filas.append(bytes(fila))
    return b"".join(filas)


def escribir_png(destino: pathlib.Path, ancho: int, alto: int, rgb: bytes) -> None:
    """Escribe un PNG RGB de 8 bits. El formato es simple de generar a mano."""

    def bloque(tipo: bytes, datos: bytes) -> bytes:
        cuerpo = tipo + datos
        return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", zlib.crc32(cuerpo))

    # Cada fila del PNG lleva un byte de filtro al principio; 0 es "sin filtro".
    crudo = b"".join(b"\x00" + rgb[y * ancho * 3 : (y + 1) * ancho * 3] for y in range(alto))

    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    destino.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + bloque(b"IHDR", cabecera)
        + bloque(b"IDAT", zlib.compress(crudo, 9))
        + bloque(b"IEND", b"")
    )


def main() -> None:
    destino = pathlib.Path("assets") / "icon.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    escribir_png(destino, LADO, LADO, render())
    print(f"OK: {destino} ({destino.stat().st_size // 1024} KB, {LADO}x{LADO})")


if __name__ == "__main__":
    main()
