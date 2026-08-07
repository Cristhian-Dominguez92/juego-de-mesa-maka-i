"""Genera la música de fondo del juego, sin dependencias externas.

Usa síntesis Karplus-Strong: se llena un buffer con ruido y se lo recorre
promediando muestras vecinas, lo que produce un sonido de cuerda pulsada. Con
eso se arma un arpegio suave sobre una progresión de acordes, pensado para
sonar en bucle sin cansar.

El resultado es enteramente nuestro y reemplaza al tema comercial que el
proyecto distribuía sin licencia (ver CREDITS.md).

Uso:
    python tools/generar_musica.py
"""

from __future__ import annotations

import math
import pathlib
import random
import struct
import wave

FRECUENCIA = 22050
DESTINO = pathlib.Path("assets") / "Recursos" / "background_music.wav"

#: Cuánto dura cada nota del arpegio, en segundos.
DURACION_NOTA = 0.5

#: Cuántas veces se repite la progresión.
REPETICIONES = 2

#: Cuánto se apaga la cuerda en cada pasada del buffer. Más bajo = más seco.
DECAIMIENTO = 0.996

#: Volumen general. Deja bastante margen para no saturar al mezclar.
VOLUMEN = 0.22

# Notas en Hz.
NOTAS = {
    "C3": 130.81,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "A3": 220.00,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "C5": 523.25,
    "E5": 659.25,
}

#: Progresión: La menor, Fa, Do, Sol. Suena melancólica pero no triste.
PROGRESION = [
    ("A3", ["A3", "C4", "E4", "A4"]),
    ("F3", ["F3", "A3", "C4", "F4"]),
    ("C3", ["C4", "E4", "G4", "C5"]),
    ("G3", ["G3", "B3", "D4", "G4"]),
]


def cuerda(frecuencia: float, muestras: int, rng: random.Random) -> list[float]:
    """Karplus-Strong: ruido inicial filtrado en bucle suena a cuerda pulsada."""
    largo = max(2, int(FRECUENCIA / frecuencia))
    buffer = [rng.uniform(-1.0, 1.0) for _ in range(largo)]

    salida = []
    i = 0
    for _ in range(muestras):
        actual = buffer[i]
        siguiente = buffer[(i + 1) % largo]
        buffer[i] = (actual + siguiente) * 0.5 * DECAIMIENTO
        salida.append(actual)
        i = (i + 1) % largo
    return salida


def envolvente(muestras: int) -> list[float]:
    """Ataque corto y caída larga, para que las notas no empiecen de golpe."""
    ataque = max(1, int(0.008 * FRECUENCIA))
    return [min(1.0, i / ataque) * math.exp(-3.0 * i / muestras) for i in range(muestras)]


def mezclar_nota(
    pista: list[float], inicio: int, freq: float, dur: float, ganancia: float, rng: random.Random
) -> None:
    muestras = int(dur * FRECUENCIA)
    onda = cuerda(freq, muestras, rng)
    sobre = envolvente(muestras)
    for i in range(muestras):
        pos = inicio + i
        if pos < len(pista):
            pista[pos] += onda[i] * sobre[i] * ganancia


def componer() -> list[float]:
    rng = random.Random(20260807)  # semilla fija: la música es reproducible

    por_acorde = len(PROGRESION[0][1]) * DURACION_NOTA
    total = int(por_acorde * len(PROGRESION) * REPETICIONES * FRECUENCIA)
    pista = [0.0] * total

    posicion = 0
    for _ in range(REPETICIONES):
        for bajo, arpegio in PROGRESION:
            # El bajo sostiene todo el acorde, a volumen bajo.
            mezclar_nota(pista, posicion, NOTAS[bajo] / 2, por_acorde, 0.5, rng)
            for j, nota in enumerate(arpegio):
                inicio = posicion + int(j * DURACION_NOTA * FRECUENCIA)
                mezclar_nota(pista, inicio, NOTAS[nota], DURACION_NOTA * 2.2, 0.7, rng)
            posicion += int(por_acorde * FRECUENCIA)
    return pista


def suavizar_bucle(pista: list[float], milisegundos: int = 120) -> None:
    """Funde el final con silencio para que el bucle no haga clic al repetir."""
    n = int(milisegundos / 1000 * FRECUENCIA)
    for i in range(n):
        factor = i / n
        pista[i] *= factor
        pista[-1 - i] *= factor


def guardar(pista: list[float], destino: pathlib.Path) -> None:
    pico = max(abs(m) for m in pista) or 1.0
    escala = VOLUMEN / pico

    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(FRECUENCIA)
        f.writeframes(
            b"".join(
                struct.pack("<h", max(-32768, min(32767, int(m * escala * 32767)))) for m in pista
            )
        )


def main() -> None:
    pista = componer()
    suavizar_bucle(pista)
    guardar(pista, DESTINO)
    segundos = len(pista) / FRECUENCIA
    kb = DESTINO.stat().st_size // 1024
    print(f"OK: {DESTINO} ({segundos:.1f} s, {kb} KB)")


if __name__ == "__main__":
    main()
