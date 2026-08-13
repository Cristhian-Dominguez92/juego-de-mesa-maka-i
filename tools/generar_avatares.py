"""Dibuja los retratos de los personajes, sin depender de arte de terceros.

Son caricaturas geométricas: círculos y elipses. No pretenden ser ilustración,
sino que cada personaje se distinga de un vistazo a tamaño chico, que es como
se ven en la mesa.

Lo que diferencia a uno de otro son los parámetros de RECETAS: ancho de cara,
tono de piel, pelo, barba y accesorio. La lista de personajes vive en
`makai/ui/personajes.py`, que es la fuente de verdad; acá solo se dibujan.

Uso:
    python tools/generar_avatares.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Falta Pillow. Instalalo con: pip install -r requirements-dev.txt")

from makai.ui.personajes import PERSONAJES  # noqa: E402

DESTINO = pathlib.Path("assets") / "Personajes"

LADO = 192
ESCALA = 4  # se dibuja en grande y se reduce, para bordes suaves

PIEL_CLARA = (238, 199, 168)
PIEL_MEDIA = (214, 168, 130)
PIEL_MORENA = (176, 128, 92)

NEGRO = (38, 34, 32)
CASTANO = (92, 62, 40)
CANOSO = (198, 196, 192)
BLANCO = (250, 250, 250)

#: Cada personaje: color de fondo, tono de piel, ancho de cara (fracción del
#: lado), pelo, barba, bigote y accesorio.
RECETAS = {
    "sultano": {
        "fondo": (58, 96, 148),
        "piel": PIEL_MEDIA,
        "ancho": 0.62,
        "pelo": CASTANO,
        "bigote": None,
        "barba": None,
        "accesorio": None,
    },
    "mengano": {
        "fondo": (148, 74, 58),
        "piel": PIEL_CLARA,
        "ancho": 0.60,
        "pelo": NEGRO,
        "bigote": NEGRO,
        "barba": None,
        "accesorio": "gorra",
    },
    "gordo": {
        "fondo": (150, 118, 44),
        "piel": PIEL_CLARA,
        "ancho": 0.80,  # cara ancha: es lo que lo identifica
        "pelo": NEGRO,
        "bigote": NEGRO,
        "barba": None,
        "accesorio": None,
    },
    "flaco": {
        "fondo": (62, 122, 96),
        "piel": PIEL_MEDIA,
        "ancho": 0.46,  # cara angosta
        "pelo": CASTANO,
        "bigote": None,
        "barba": None,
        "accesorio": None,
    },
    "vaicho": {
        "fondo": (122, 92, 52),
        "piel": PIEL_MORENA,
        "ancho": 0.62,
        "pelo": NEGRO,
        "bigote": NEGRO,
        "barba": None,
        "accesorio": "sombrero",  # sombrero de paja, del campo
    },
    "leporato": {
        "fondo": (96, 76, 138),
        "piel": PIEL_CLARA,
        "ancho": 0.64,
        "pelo": None,  # pelado
        "bigote": None,
        "barba": CANOSO,
        "accesorio": "lentes",
    },
}

PAJA = (222, 190, 118)
PAJA_OSCURA = (188, 154, 88)


def dibujar(receta: dict, lado: int) -> Image.Image:
    im = Image.new("RGB", (lado, lado), receta["fondo"])
    d = ImageDraw.Draw(im)

    cx = lado / 2
    ancho = receta["ancho"] * lado
    alto = 0.66 * lado
    cy = 0.52 * lado

    # Cuello y hombros, para que la cabeza no flote.
    d.rounded_rectangle(
        [cx - ancho * 0.28, cy + alto * 0.30, cx + ancho * 0.28, lado],
        radius=lado * 0.06,
        fill=receta["piel"],
    )
    d.ellipse([cx - lado * 0.52, lado * 0.86, cx + lado * 0.52, lado * 1.5], fill=(46, 46, 54))

    # Cabeza.
    caja = [cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2]
    d.ellipse(caja, fill=receta["piel"])

    # Orejas.
    r_oreja = lado * 0.055
    for lado_x in (-1, 1):
        ox = cx + lado_x * ancho / 2
        d.ellipse([ox - r_oreja, cy - r_oreja, ox + r_oreja, cy + r_oreja], fill=receta["piel"])

    # Pelo: un casquete sobre la mitad superior.
    if receta["pelo"]:
        d.chord(
            [cx - ancho / 2 - 2, cy - alto / 2 - 2, cx + ancho / 2 + 2, cy + alto * 0.12],
            180,
            360,
            fill=receta["pelo"],
        )

    # Ojos.
    sep = ancho * 0.22
    oy = cy - alto * 0.06
    r_ojo = lado * 0.035
    for lado_x in (-1, 1):
        ox = cx + lado_x * sep
        d.ellipse([ox - r_ojo, oy - r_ojo, ox + r_ojo, oy + r_ojo], fill=BLANCO)
        r_pupila = r_ojo * 0.5
        d.ellipse(
            [ox - r_pupila, oy - r_pupila, ox + r_pupila, oy + r_pupila],
            fill=NEGRO,
        )

    # Barba: media luna en la parte baja de la cara.
    if receta["barba"]:
        d.chord(
            [cx - ancho / 2, cy - alto * 0.16, cx + ancho / 2, cy + alto / 2],
            0,
            180,
            fill=receta["barba"],
        )

    # Boca, siempre: un bigote no debe dejar la cara sin gesto.
    d.arc(
        [cx - ancho * 0.18, cy + alto * 0.10, cx + ancho * 0.18, cy + alto * 0.32],
        10,
        170,
        fill=(150, 84, 72),
        width=max(2, lado // 60),
    )

    # Bigote: dos mitades curvas, no una barra.
    if receta["bigote"]:
        by = cy + alto * 0.10
        mitad = ancho * 0.19
        grosor = alto * 0.055
        for lado_x in (-1, 1):
            d.chord(
                [
                    cx + lado_x * mitad - mitad,
                    by - grosor,
                    cx + lado_x * mitad + mitad,
                    by + grosor * 2.4,
                ],
                180,
                360,
                fill=receta["bigote"],
            )

    accesorio = receta["accesorio"]
    if accesorio == "gorra":
        d.chord(
            [cx - ancho / 2 - 4, cy - alto / 2 - 6, cx + ancho / 2 + 4, cy + alto * 0.02],
            180,
            360,
            fill=(180, 58, 48),
        )
        d.rounded_rectangle(
            [cx - ancho * 0.62, cy - alto * 0.20, cx + ancho * 0.10, cy - alto * 0.12],
            radius=lado * 0.02,
            fill=(150, 44, 36),
        )
    elif accesorio == "sombrero":
        # El ala va bien por encima de los ojos: apoyada sobre las cejas los
        # tapaba y el personaje quedaba sin mirada.
        ala_y = cy - alto * 0.30
        d.ellipse(
            [cx - ancho * 0.95, ala_y - alto * 0.11, cx + ancho * 0.95, ala_y + alto * 0.11],
            fill=PAJA,
        )
        d.ellipse(
            [cx - ancho * 0.42, cy - alto * 0.82, cx + ancho * 0.42, ala_y + alto * 0.04],
            fill=PAJA,
        )
        d.rounded_rectangle(
            [cx - ancho * 0.42, ala_y - alto * 0.14, cx + ancho * 0.42, ala_y - alto * 0.04],
            radius=lado * 0.02,
            fill=PAJA_OSCURA,
        )
    elif accesorio == "lentes":
        grosor = max(2, lado // 55)
        for lado_x in (-1, 1):
            ox = cx + lado_x * sep
            r = lado * 0.062
            d.ellipse([ox - r, oy - r, ox + r, oy + r], outline=NEGRO, width=grosor)
        d.line(
            [cx - sep + lado * 0.062, oy, cx + sep - lado * 0.062, oy],
            fill=NEGRO,
            width=grosor,
        )

    return im


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)

    faltantes = [p.id for p in PERSONAJES if p.id not in RECETAS]
    if faltantes:
        sys.exit(f"Sin receta de dibujo: {faltantes}")

    total = 0
    for personaje in PERSONAJES:
        grande = dibujar(RECETAS[personaje.id], LADO * ESCALA)
        imagen = grande.resize((LADO, LADO), Image.LANCZOS)
        ruta = DESTINO / personaje.archivo
        imagen.save(ruta, "WEBP", quality=88, method=6)
        total += ruta.stat().st_size
        print(f"OK: {ruta.name} ({ruta.stat().st_size // 1024} KB)")

    print(f"\n{len(PERSONAJES)} retratos, {total // 1024} KB en total")


if __name__ == "__main__":
    main()
