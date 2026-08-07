"""Genera el ícono de la aplicación a partir del rey de oros de la baraja.

Recorta la moneda de oros del rey de oros de la baraja Fournier de 1878, que
está en dominio público igual que el resto de las cartas (ver CREDITS.md).

**Por qué la moneda y no el rey**: Android recorta el ícono en círculo o en
cuadrado redondeado según el launcher, y solo garantiza el 66% central. Una
figura de cuerpo entero pierde los costados; la moneda, centrada, sobrevive
cualquier recorte y además se lee mejor en chico.

La carta se descarga al vuelo desde Wikimedia en alta resolución: la que se
distribuye en assets/ está a 330 px y quedaría borrosa al ampliarla a 512.

Requiere Pillow (dependencia de desarrollo, no se empaqueta en el APK).

Uso:
    python tools/generar_icono.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

try:
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("Falta Pillow. Instalalo con: pip install -r requirements-dev.txt")

from descargar_baraja import _pedir, urls_de_miniaturas  # noqa: E402

DESTINO = pathlib.Path("assets") / "icon.png"

CARTA = "Fournier 1878 - errege urrea (ref. 44470).png"

#: Ancho al que se pide la carta. Con esto la moneda queda holgada para 512.
ANCHO_ORIGEN = 900

LADO = 512

#: Margen de verde alrededor de la moneda, como fracción del lado.
MARGEN = 0.05

#: Verde de la mesa, el mismo que el fondo del juego.
VERDE_MESA = (26, 74, 26)

#: Centro y radio del recorte, como fracción del ancho de la carta.
CENTRO_X = 0.2604
CENTRO_Y = 0.2417
RADIO = 0.1333

# Los mismos valores que tools/optimizar_imagenes.py: el escaneo de 1878 tiene
# el papel amarillento y las tintas apagadas.
CONTRASTE = 1.45
SATURACION = 1.55
BRILLO = 1.10


def realzar(imagen: Image.Image) -> Image.Image:
    imagen = ImageEnhance.Contrast(imagen).enhance(CONTRASTE)
    imagen = ImageEnhance.Color(imagen).enhance(SATURACION)
    return ImageEnhance.Brightness(imagen).enhance(BRILLO)


def descargar_carta() -> Image.Image:
    import io

    url = urls_de_miniaturas([CARTA], ANCHO_ORIGEN)[CARTA]
    return Image.open(io.BytesIO(_pedir(url))).convert("RGBA")


def recortar_moneda(carta: Image.Image) -> Image.Image:
    ancho = carta.size[0]
    cx, cy, r = CENTRO_X * ancho, CENTRO_Y * ancho, RADIO * ancho
    return carta.crop((round(cx - r), round(cy - r), round(cx + r), round(cy + r)))


def componer(moneda: Image.Image) -> Image.Image:
    fondo = Image.new("RGB", (LADO, LADO), VERDE_MESA)
    margen = round(LADO * MARGEN)
    lado_interior = LADO - 2 * margen
    fondo.paste(
        realzar(moneda).convert("RGB").resize((lado_interior, lado_interior), Image.LANCZOS),
        (margen, margen),
    )
    return fondo


def main() -> None:
    print(f"Descargando {CARTA}...")
    icono = componer(recortar_moneda(descargar_carta()))

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    icono.save(DESTINO, "PNG", optimize=True)
    print(f"OK: {DESTINO} ({DESTINO.stat().st_size // 1024} KB, {LADO}x{LADO})")


if __name__ == "__main__":
    main()
