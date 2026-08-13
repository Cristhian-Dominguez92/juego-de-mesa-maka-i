"""Genera el fondo del menú: un patrón oscuro inspirado en el ñandutí.

El ñandutí es el encaje paraguayo, de motivos radiales tipo telaraña. Acá se
dibuja una versión geométrica y muy tenue: el fondo tiene que dar textura sin
competirle la atención al título ni a los botones.

La baldosa es **repetible**: el motivo se dibuja centrado y además partido en
las cuatro esquinas, de modo que al repetirse los bordes calzan.

Se genera por código, como el resto de los assets, para no depender de material
de terceros (ver CREDITS.md).

Uso:
    python tools/generar_fondo.py
"""

from __future__ import annotations

import math
import pathlib
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Falta Pillow. Instalalo con: pip install -r requirements-dev.txt")

DESTINO = pathlib.Path("assets") / "fondo_menu.png"

#: Lado de la baldosa. Al repetirse cubre cualquier pantalla.
LADO = 256

#: Se dibuja a mayor tamaño y se reduce, para que las líneas queden suaves.
ESCALA = 4

FONDO = (10, 10, 12)
HILO = (44, 46, 52)
HILO_TENUE = (28, 30, 35)

#: Radios del motivo, como fracción del lado.
ANILLOS = (0.12, 0.22, 0.32, 0.42)

#: Rayos que salen del centro, como en la telaraña del ñandutí.
RAYOS = 16


def dibujar_motivo(d: ImageDraw.ImageDraw, cx: float, cy: float, lado: int) -> None:
    """Dibuja un motivo radial centrado en (cx, cy)."""
    grosor = max(1, lado // 220)

    for i, fraccion in enumerate(ANILLOS):
        r = fraccion * lado
        color = HILO if i % 2 == 0 else HILO_TENUE
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=grosor)

    radio_externo = ANILLOS[-1] * lado
    for i in range(RAYOS):
        angulo = 2 * math.pi * i / RAYOS
        d.line(
            [cx, cy, cx + radio_externo * math.cos(angulo), cy + radio_externo * math.sin(angulo)],
            fill=HILO_TENUE,
            width=grosor,
        )

    # Rombo central, que es el remate habitual del motivo.
    r = ANILLOS[0] * lado * 0.7
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=HILO, width=grosor)


def generar(lado: int = LADO, escala: int = ESCALA) -> Image.Image:
    grande = lado * escala
    imagen = Image.new("RGB", (grande, grande), FONDO)
    d = ImageDraw.Draw(imagen)

    # Centrado, y repetido en las cuatro esquinas para que la baldosa calce.
    dibujar_motivo(d, grande / 2, grande / 2, grande)
    for cx in (0, grande):
        for cy in (0, grande):
            dibujar_motivo(d, cx, cy, grande)

    return imagen.resize((lado, lado), Image.LANCZOS)


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    generar().save(DESTINO, "PNG", optimize=True)
    print(f"OK: {DESTINO} ({DESTINO.stat().st_size // 1024} KB, {LADO}x{LADO}, repetible)")


if __name__ == "__main__":
    main()
