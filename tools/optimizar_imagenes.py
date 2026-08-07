"""Convierte las imágenes de las cartas a WebP para achicar el APK.

Los escaneos de la baraja son fotografías: PNG los comprime mal porque el grano
del papel es ruido puro. WebP con pérdida los deja en una fracción del tamaño
sin diferencia visible al tamaño que se muestran.

**Se descarta el canal alfa a propósito.** Los escaneos traen las esquinas
redondeadas recortadas con transparencia, pero un WebP con pérdida y alfa se
renderizaba translúcido en el juego: las cartas se veían desteñidas sobre el
verde de la mesa. Aplanando sobre blanco el problema desaparece, y el redondeo
de las esquinas lo hace la interfaz con `border_radius` y `clip_behavior`.

Requiere Pillow, que es dependencia de desarrollo: no se empaqueta en el APK.

Uso:
    python tools/optimizar_imagenes.py            # convierte y borra los PNG
    python tools/optimizar_imagenes.py --conservar
"""

from __future__ import annotations

import argparse
import pathlib
import sys

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Falta Pillow. Instalalo con: pip install -r requirements-dev.txt")

DESTINO = pathlib.Path("assets") / "Recursos"

#: 82 conserva el grano del papel sin artefactos visibles al tamaño de juego.
CALIDAD = 82

# Los escaneos son de cartas de 1878: el papel amarilleó y las tintas se
# apagaron. Tal cual vienen, sobre el verde de la mesa y al tamaño chico al que
# se muestran, se leen desvaídas. Estos valores levantan el papel a blanco y
# devuelven fuerza a las tintas sin que se vean artificiales.
CONTRASTE = 1.45
SATURACION = 1.55
BRILLO = 1.10


def convertir(origen: pathlib.Path, calidad: int, conservar: bool) -> tuple[int, int]:
    destino = origen.with_suffix(".webp")
    antes = origen.stat().st_size

    with Image.open(origen) as imagen:
        rgba = imagen.convert("RGBA")
        # Aplanar sobre blanco: el papel de la carta ya es casi blanco, así que
        # las esquinas recortadas quedan indistinguibles del borde.
        plano = Image.new("RGB", rgba.size, (255, 255, 255))
        plano.paste(rgba, mask=rgba.getchannel("A"))

        plano = ImageEnhance.Contrast(plano).enhance(CONTRASTE)
        plano = ImageEnhance.Color(plano).enhance(SATURACION)
        plano = ImageEnhance.Brightness(plano).enhance(BRILLO)

        plano.save(destino, "WEBP", quality=calidad, method=6)

    despues = destino.stat().st_size
    if not conservar:
        origen.unlink()
    return antes, despues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", default=str(DESTINO))
    parser.add_argument("--calidad", type=int, default=CALIDAD)
    parser.add_argument("--conservar", action="store_true", help="no borrar los PNG originales")
    args = parser.parse_args()

    carpeta = pathlib.Path(args.destino)
    imagenes = sorted(carpeta.glob("*.png"))
    if not imagenes:
        sys.exit(f"No hay PNG que convertir en {carpeta}")

    total_antes = total_despues = 0
    for origen in imagenes:
        antes, despues = convertir(origen, args.calidad, args.conservar)
        total_antes += antes
        total_despues += despues
        print(f"OK: {origen.stem}.webp  {antes // 1024} KB -> {despues // 1024} KB")

    reduccion = 100 * (1 - total_despues / total_antes)
    print(
        f"\n{len(imagenes)} imágenes: "
        f"{total_antes / 1024 / 1024:.1f} MB -> {total_despues / 1024 / 1024:.1f} MB "
        f"({reduccion:.0f}% menos)"
    )


if __name__ == "__main__":
    main()
