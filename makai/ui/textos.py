"""Textos largos de la interfaz.

Las reglas van embebidas y no leídas de docs/REGLAS.md: ese archivo no se
empaqueta en el APK. Si se cambian las reglas, hay que tocar los dos lugares;
el test `test_textos.py` verifica que no se contradigan en lo esencial.
"""

from __future__ import annotations

TITULO_REGLAS = "Cómo se juega"

#: Secciones de la pantalla de reglas: (encabezado, cuerpo).
REGLAS: list[tuple[str, str]] = [
    (
        "La baraja",
        "Baraja española de 40 cartas: oros, copas, espadas y bastos, con los "
        "valores 1 a 7, 10, 11 y 12. No hay 8 ni 9.\n"
        "El 10, el 11 y el 12 son las figuras.",
    ),
    (
        "El puntaje",
        "Cada carta suma su valor, y toda figura vale 10.\n"
        "De la suma solo cuenta el último dígito:\n\n"
        "    4 + 5 = 9        →  9\n"
        "    7 + 3 = 10       →  0\n"
        "    10 + 5 = 15      →  5\n"
        "    7 + 7 + 7 = 21   →  1\n\n"
        "El mejor puntaje posible es 9.",
    ),
    (
        "Tres figuras",
        "Tres figuras cualesquiera valen 8.5: le ganan a cualquier 8, pero "
        "pierden con un 9.\n"
        "Dos figuras no son mano especial; se suman normalmente.",
    ),
    (
        "La ronda",
        "Antes de repartir se fija la apuesta. Nadie puede apostar más fichas "
        "de las que el otro puede pagar.\n\n"
        "Recibís 2 cartas y podés PEDIR una más o PLANTARTE. El máximo son 3 "
        "cartas, así que se pide una sola vez.\n\n"
        "Cuando te plantás, la PC juega su mano y se comparan los puntajes. "
        "El ganador se lleva la apuesta.",
    ),
    (
        "La banca",
        "La banca importa por una sola razón: el empate lo gana la banca.\n\n"
        "La banca se conserva mientras gane. Cuando pierde, pasa al rival. "
        "Dicho de otro modo: la banca de la ronda siguiente es quien acaba de "
        "ganar.",
    ),
    (
        "Fin de la partida",
        "Gana quien deje al otro sin fichas.",
    ),
    (
        "Dificultad",
        "Fácil: la PC se planta con manos malas.\n"
        "Normal: pide hasta llegar a 6, sin mirar tus cartas.\n"
        "Difícil: mira tu mano y juega contra tu puntaje real.",
    ),
]
