"""Genera las 40 cartas de la baraja española y el dorso.

Uso:
    python tools/generar_cartas.py            # las 40 cartas + dorso
    python tools/generar_cartas.py --muestra  # solo unas pocas, para revisar

Ver tools/baraja.py para el dibujo. Los archivos van a assets/Recursos/ con el
mismo nombre que espera el juego (`Carta.nombre_archivo`).
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from baraja import (  # noqa: E402
    ALTO,
    ANCHO,
    COLOR_PALO,
    DORADO,
    FONDO_DORSO,
    GROSOR_BORDE,
    MARFIL,
    MARGEN_INTERIOR,
    PALOS,
    RADIO_ESQUINA,
    TINTA,
    Lienzo,
    digito,
)

DESTINO = pathlib.Path("assets") / "Recursos"

FIGURAS = {10: 1, 11: 2, 12: 3}  # cuántos galones lleva cada figura

#: Posición de los palos en el centro, por cantidad. Coordenadas de 0 a 1
#: dentro del área central de la carta.
DISPOSICION = {
    1: [(0.5, 0.5)],
    2: [(0.5, 0.25), (0.5, 0.75)],
    3: [(0.5, 0.18), (0.5, 0.5), (0.5, 0.82)],
    4: [(0.28, 0.25), (0.72, 0.25), (0.28, 0.75), (0.72, 0.75)],
    5: [(0.28, 0.25), (0.72, 0.25), (0.5, 0.5), (0.28, 0.75), (0.72, 0.75)],
    6: [
        (0.28, 0.18),
        (0.72, 0.18),
        (0.28, 0.5),
        (0.72, 0.5),
        (0.28, 0.82),
        (0.72, 0.82),
    ],
    # El séptimo va justo en el medio, entre las dos columnas.
    7: [
        (0.26, 0.16),
        (0.74, 0.16),
        (0.26, 0.5),
        (0.74, 0.5),
        (0.26, 0.84),
        (0.74, 0.84),
        (0.5, 0.5),
    ],
}


def _dentro_de_la_carta(x: float, y: float) -> bool:
    """True si el punto cae dentro del rectángulo redondeado de la carta."""
    px, py = x * ANCHO, y * ALTO
    r = RADIO_ESQUINA
    cx = min(max(px, r), ANCHO - r)
    cy = min(max(py, r), ALTO - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def _borde(x: float, y: float) -> float:
    """Marco de la carta: dentro del contorno pero no del contorno interior."""
    if not _dentro_de_la_carta(x, y):
        return 0.0
    g = GROSOR_BORDE
    px, py = x * ANCHO, y * ALTO
    adentro = g <= px <= ANCHO - g and g <= py <= ALTO - g
    return 0.0 if adentro else 1.0


def lienzo_de_carta() -> Lienzo:
    """Carta en blanco: fondo marfil recortado a esquinas redondeadas."""
    lienzo = Lienzo(ANCHO, ALTO, FONDO_DORSO)
    lienzo.pintar(0, 0, ANCHO, ALTO, lambda x, y: 1.0 if _dentro_de_la_carta(x, y) else 0.0, MARFIL)
    lienzo.pintar(0, 0, ANCHO, ALTO, _borde, DORADO)
    return lienzo


def dibujar_indice(lienzo: Lienzo, valor: int, palo: str, invertido: bool = False) -> None:
    """Número y palo pequeño en una esquina."""
    color = COLOR_PALO[palo]
    ancho_d, alto_d = 24, 34
    sep = 6
    texto = str(valor)
    ancho_total = len(texto) * ancho_d + (len(texto) - 1) * sep

    x0, y0 = 20, 20
    if invertido:
        x0 = ANCHO - 20 - ancho_total
        y0 = ALTO - 20 - alto_d - 8 - 26

    for i, caracter in enumerate(texto):
        lienzo.pintar(x0 + i * (ancho_d + sep), y0, ancho_d, alto_d, digito(caracter), TINTA)

    # Palo chico justo debajo del número. Va grande porque en el celular la
    # carta se ve a un tercio de este tamaño.
    lado = 34
    lienzo.pintar(x0 + (ancho_total - lado) // 2, y0 + alto_d + 6, lado, lado, PALOS[palo], color)


def dibujar_centro(lienzo: Lienzo, valor: int, palo: str) -> None:
    """Los palos del centro de la carta."""
    color = COLOR_PALO[palo]
    forma = PALOS[palo]

    izq, arriba = MARGEN_INTERIOR + 62, MARGEN_INTERIOR + 28
    ancho = ANCHO - izq - MARGEN_INTERIOR - 8
    alto = ALTO - arriba - MARGEN_INTERIOR - 28

    if valor in FIGURAS:
        # Figura: un palo grande y galones que distinguen sota/caballo/rey.
        lado = 128
        lienzo.pintar(izq + (ancho - lado) // 2, arriba + 20, lado, lado, forma, color)
        for i in range(FIGURAS[valor]):
            y = arriba + 170 + i * 22
            lienzo.pintar(izq + (ancho - 84) // 2, y, 84, 12, lambda x, y: 1.0, color)
        return

    lado = 54 if valor <= 5 else 46
    for fx, fy in DISPOSICION[valor]:
        x = izq + round(fx * ancho) - lado // 2
        y = arriba + round(fy * alto) - lado // 2
        lienzo.pintar(x, y, lado, lado, forma, color)


def generar_carta(valor: int, palo: str) -> Lienzo:
    lienzo = lienzo_de_carta()
    dibujar_indice(lienzo, valor, palo)
    dibujar_indice(lienzo, valor, palo, invertido=True)
    dibujar_centro(lienzo, valor, palo)
    return lienzo


def generar_dorso() -> Lienzo:
    """Dorso: rombos sobre el verde de la mesa."""
    lienzo = Lienzo(ANCHO, ALTO, FONDO_DORSO)
    lienzo.pintar(
        0, 0, ANCHO, ALTO, lambda x, y: 1.0 if _dentro_de_la_carta(x, y) else 0.0, FONDO_DORSO
    )

    paso = 38
    lado = 24
    for fila in range(1, ALTO // paso):
        for col in range(1, ANCHO // paso):
            cx = col * paso + (paso // 2 if fila % 2 else 0)
            cy = fila * paso
            if not _dentro_de_la_carta((cx + 0.5) / ANCHO, (cy + 0.5) / ALTO):
                continue
            lienzo.pintar(
                cx - lado // 2,
                cy - lado // 2,
                lado,
                lado,
                lambda x, y: 1.0 if abs(x - 0.5) + abs(y - 0.5) <= 0.5 else 0.0,
                DORADO,
            )

    lienzo.pintar(0, 0, ANCHO, ALTO, _borde, DORADO)
    return lienzo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--muestra",
        action="store_true",
        help="genera solo unas pocas cartas, para revisar el estilo",
    )
    parser.add_argument("--destino", default=str(DESTINO))
    args = parser.parse_args()

    destino = pathlib.Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    if args.muestra:
        pedidos = [(1, "oro"), (5, "copa"), (7, "basto"), (12, "espada")]
    else:
        pedidos = [
            (v, p)
            for p in ("oro", "copa", "espada", "basto")
            for v in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)
        ]

    for valor, palo in pedidos:
        ruta = destino / f"{valor}_{palo}.png"
        generar_carta(valor, palo).guardar(ruta)
        print(f"OK: {ruta.name}")

    ruta = destino / "dorso.png"
    generar_dorso().guardar(ruta)
    print(f"OK: {ruta.name}")


if __name__ == "__main__":
    main()
