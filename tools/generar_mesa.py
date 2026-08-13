"""Genera la textura de madera de la mesa de juego.

La veta se arma con funciones periódicas: una onda base a lo largo del eje
vertical, deformada por unas pocas sinusoides de frecuencia entera. Que las
frecuencias sean enteras es lo que hace que la baldosa **calce consigo misma**
al repetirse, sin costura visible.

Encima van las juntas entre tablas y un moteado fino, que es lo que evita que
la madera se vea plástica.

Se genera por código, como el resto de los assets (ver CREDITS.md).

Uso:
    python tools/generar_mesa.py
"""

from __future__ import annotations

import math
import pathlib
import random
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow. Instalalo con: pip install -r requirements-dev.txt")

DESTINO = pathlib.Path("assets") / "mesa_madera.png"

#: Lado de la baldosa. Al repetirse cubre cualquier pantalla.
LADO = 512

#: Tablas a lo ancho de la baldosa.
TABLAS = 4

#: Tonos de la madera, del claro al oscuro.
CLARA = (176, 134, 92)
OSCURA = (120, 84, 52)
JUNTA = (74, 50, 30)

#: Cuántas vetas por tabla.
VETAS = 7

#: Cuánto serpentea la veta. Bajo a propósito: la veta de la madera corre casi
#: paralela a la tabla, y con valores altos el resultado parece arena ondulada.
DEFORMACION = 0.55

#: Cuánto se afinan las líneas oscuras. Más alto, veta más marcada y fina.
NITIDEZ = 3.0


def mezclar(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def turbulencia(x: float, y: float) -> float:
    """Deformación periódica, para que la veta no sea una raya recta.

    Las frecuencias son bajas en el eje de la tabla y enteras en los dos ejes:
    enteras para que la baldosa calce consigo misma al repetirse, y bajas para
    que la veta se curve despacio en vez de ondular.
    """
    return (
        math.sin(2 * math.pi * (1 * x))
        + 0.45 * math.sin(2 * math.pi * (2 * x + 1 * y))
        + 0.2 * math.sin(2 * math.pi * (3 * x - 1 * y))
    )


def tono_de_tabla(indice: int) -> float:
    """Desplazamiento de tono de cada tabla, para que no sean clones."""
    return 0.5 * math.sin(indice * 2.399) + 0.25 * math.sin(indice * 5.117)


def generar(lado: int = LADO) -> Image.Image:
    rng = random.Random(20260808)
    imagen = Image.new("RGB", (lado, lado))
    px = imagen.load()

    alto_tabla = lado / TABLAS

    for j in range(lado):
        v = j / lado
        tabla = int(j / alto_tabla)
        desplazamiento = tono_de_tabla(tabla)

        for i in range(lado):
            u = i / lado

            # Veta: onda a lo largo de la tabla, curvada por la turbulencia.
            # El término en sin(6πv) hace que las líneas se agrupen y se
            # separen; con espaciado parejo la textura parece corrugado.
            fase = (
                VETAS * TABLAS * v
                + 0.9 * math.sin(2 * math.pi * 3 * v)
                + DEFORMACION * turbulencia(u, v)
            )
            onda = 0.5 + 0.5 * math.sin(2 * math.pi * fase)
            # Elevar a una potencia concentra el oscuro en líneas finas, que es
            # como se ve la veta real; sin esto quedan bandas anchas y parejas.
            veta = onda**NITIDEZ

            claridad = min(1.0, max(0.0, veta * 0.80 + desplazamiento * 0.22))
            color = mezclar(CLARA, OSCURA, claridad)

            # Junta entre tablas: una franja oscura cada alto_tabla.
            distancia = min(j % alto_tabla, alto_tabla - (j % alto_tabla))
            if distancia < 1.6:
                color = mezclar(color, JUNTA, 1 - distancia / 1.6)

            # Moteado fino: sin esto la madera parece plástico.
            ruido = rng.randint(-6, 6)
            px[i, j] = tuple(max(0, min(255, c + ruido)) for c in color)

    return imagen


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    generar().save(DESTINO, "PNG", optimize=True)
    kb = DESTINO.stat().st_size // 1024
    print(f"OK: {DESTINO} ({kb} KB, {LADO}x{LADO}, repetible)")


if __name__ == "__main__":
    main()
