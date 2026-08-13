"""Genera los efectos de sonido del juego, sin dependencias externas.

Por ahora, el barajeo que suena al repartir.

Un mazo barajándose es, acústicamente, una ráfaga de transitorios muy cortos y
brillantes: cada carta que se suelta es un golpe seco de ruido. Se sintetiza
así: ruido blanco, realzado en agudos con una diferencia de primer orden para
que suene a papel y no a viento, y recortado con una envolvente de ataque
instantáneo y caída muy rápida.

Encima va un siseo de fondo con envolvente lenta, que es el roce del mazo.

Uso:
    python tools/generar_sonidos.py
"""

from __future__ import annotations

import math
import pathlib
import random
import struct
import wave

FRECUENCIA = 22050
DESTINO = pathlib.Path("assets") / "Recursos" / "barajar.wav"

#: Duración total. Acompaña a la animación de reparto, que dura ~0.75 s.
DURACION = 1.0

#: Cuántas cartas se oyen caer.
GOLPES = 34

#: Duración de cada golpe, en segundos.
DURACION_GOLPE = 0.035

#: Realce de agudos. Más cerca de 1 suena más seco y papeloso.
BRILLO = 0.85

#: Volumen general, con margen de sobra para no saturar.
VOLUMEN = 0.30


def golpe(rng: random.Random, muestras: int) -> list[float]:
    """Una carta soltándose: ruido con mucho agudo y caída inmediata."""
    ruido = [rng.uniform(-1.0, 1.0) for _ in range(muestras)]
    # Diferencia de primer orden: atenúa los graves y deja el "papel".
    brillante = [ruido[0]]
    brillante.extend(ruido[i] - BRILLO * ruido[i - 1] for i in range(1, muestras))
    return [m * math.exp(-9.0 * i / muestras) for i, m in enumerate(brillante)]


def siseo(rng: random.Random, muestras: int) -> list[float]:
    """El roce del mazo por debajo de los golpes."""
    ruido = [rng.uniform(-1.0, 1.0) for _ in range(muestras)]
    brillante = [ruido[0]]
    brillante.extend(ruido[i] - 0.6 * ruido[i - 1] for i in range(1, muestras))

    salida = []
    for i, m in enumerate(brillante):
        t = i / muestras
        # Entra rápido, se sostiene y se apaga: la forma de un barajeo.
        envolvente = math.sin(math.pi * t) ** 1.5
        salida.append(m * envolvente)
    return salida


def componer() -> list[float]:
    rng = random.Random(20260808)  # semilla fija: el sonido es reproducible

    total = int(DURACION * FRECUENCIA)
    pista = siseo(rng, total)
    for i, m in enumerate(pista):
        pista[i] = m * 0.22

    muestras_golpe = int(DURACION_GOLPE * FRECUENCIA)
    for k in range(GOLPES):
        t = k / GOLPES
        # Los golpes se aceleran hacia el medio y se espacian al final, que es
        # como suena un barajeo de verdad.
        posicion = (t + 0.35 * math.sin(math.pi * t) * (1 - t)) * 0.82
        inicio = int(posicion * total) + rng.randint(-320, 320)
        inicio = max(0, min(inicio, total - muestras_golpe))

        ganancia = 0.55 + 0.45 * rng.random()
        for i, m in enumerate(golpe(rng, muestras_golpe)):
            pista[inicio + i] += m * ganancia

    return pista


def suavizar_bordes(pista: list[float], milisegundos: int = 8) -> None:
    """Evita el clic de arranque y de corte."""
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
    suavizar_bordes(pista)
    guardar(pista, DESTINO)
    kb = DESTINO.stat().st_size // 1024
    print(f"OK: {DESTINO} ({len(pista) / FRECUENCIA:.2f} s, {kb} KB)")


if __name__ == "__main__":
    main()
