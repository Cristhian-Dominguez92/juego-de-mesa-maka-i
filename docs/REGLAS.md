# Reglas del Maka'i (según esta implementación)

> Las reglas de puntuación, la mano de tres figuras, la rotación de la banca y
> el modelo de apuestas fueron **confirmadas por el autor del proyecto**. Lo que
> siga marcado con ❓ es lo que todavía no se validó.
> Cada regla acá descrita está cubierta por un test en `tests/test_reglas.py` y
> `tests/test_partida.py`.

## La baraja

Baraja española de **40 cartas**: cuatro palos (oros, copas, espadas, bastos)
con los valores **1 a 7, 10, 11 y 12**. No hay 8 ni 9.

Las cartas 10, 11 y 12 (sota, caballo y rey) se llaman **figuras**.

## Objetivo

Ganarle las fichas a la banca. Cada jugador arranca con **100 fichas** y la
partida termina cuando uno se queda **sin ninguna**.

## Puntuación

Cada carta aporta su valor numérico; **toda figura vale 10**.

De la suma **solo cuenta el último dígito**:

| Cartas | Suma | Puntaje |
|---|---|---|
| 1 + 2 | 3 | **3** |
| 4 + 5 | 9 | **9** |
| 7 + 3 | 10 | **0** |
| 7 + 7 | 14 | **4** |
| 10 + 5 | 15 | **5** |
| 12 + 11 | 20 | **0** |
| 7 + 7 + 7 | 21 | **1** |

El mejor puntaje posible es **9**.

### Mano especial: tres figuras

Tres figuras cualesquiera (por ejemplo 10 + 11 + 12) valen **8.5**.

Esto la coloca **por encima de cualquier 8 pero por debajo de un 9**. Dos
figuras no cuentan como mano especial: se suman normalmente (10 + 10 = 20 → 0).

## Desarrollo de una ronda

1. Antes de repartir se fija la **apuesta** de la ronda. No puede superar las
   fichas del lado que menos tenga: nadie apuesta lo que el otro no puede pagar.
2. Se baraja un mazo completo y se reparten **2 cartas** a cada lado. Las de la
   PC quedan boca abajo.
3. El jugador puede **pedir** una carta más o **plantarse**. El máximo por mano
   es de **3 cartas**, así que se puede pedir una sola vez.
4. Cuando el jugador se planta, la PC revela sus cartas y decide si pide, según
   la dificultad elegida (ver abajo).
5. Se comparan los puntajes. El ganador se lleva la apuesta del otro.

## La banca

La banca importa por una sola razón: **el empate lo gana la banca**.

**La banca se conserva mientras gane.** Cuando pierde una ronda, pasa al rival.
Las dos cosas se resumen en una: la banca de la ronda siguiente es quien acaba
de ganar. Al empezar la partida, la banca es la PC.

## Dificultad de la PC

En este juego las cartas del jugador están boca arriba y la PC decide después
de que el jugador se plantó, así que su puntaje final ya es conocido.

| Nivel | Cómo juega |
|---|---|
| **Fácil** | Pide hasta llegar a 4. Se planta demasiado temprano. |
| **Normal** | Pide hasta llegar a 6, sin mirar al rival. Es el comportamiento histórico. |
| **Difícil** | Mira la mano del jugador: si va ganando se planta, y si va perdiendo pide. De banca le alcanza con igualar, porque el empate la favorece. |

## Fin de la partida

Gana quien deje al otro **sin fichas**. Después se puede empezar de nuevo con
el marcador restablecido.

## Diferencias conocidas con el juego tradicional

- **No hay múltiples jugadores.** Solo jugador contra PC.
- **El jugador siempre juega primero**, sea o no la banca. En una mesa real el
  orden depende de quién es la banca. ❓
- **La apuesta la fija un solo lado.** No hay subir la apuesta ni retirarse una
  vez repartidas las cartas. ❓
