# Reglas del Maka'i (según esta implementación)

> **Advertencia sobre el origen de estas reglas.**
> Este documento describe lo que el juego hace hoy, reconstruido a partir del
> código original (`main.py`, commit `be8b8b7`). **No está validado contra una
> fuente autorizada** del Maka'i tradicional paraguayo. Las secciones marcadas
> con ❓ son las que más conviene confirmar con jugadores antes de tratarlas
> como definitivas. Cada regla acá descrita está cubierta por un test en
> `tests/test_reglas.py` y `tests/test_partida.py`.

## La baraja

Baraja española de **40 cartas**: cuatro palos (oros, copas, espadas, bastos)
con los valores **1 a 7, 10, 11 y 12**. No hay 8 ni 9.

Las cartas 10, 11 y 12 (sota, caballo y rey) se llaman **figuras**.

## Objetivo

Sacar más puntaje que la banca. La partida se juega a **10 rondas ganadas**.

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

### Mano especial: tres figuras ❓

Tres figuras cualesquiera (por ejemplo 10 + 11 + 12) valen **8.5**.

Esto la coloca **por encima de cualquier 8 pero por debajo de un 9**. Dos
figuras no cuentan como mano especial: se suman normalmente (10 + 10 = 20 → 0).

❓ El valor 8.5 viene del código original. Habría que confirmar si en el juego
tradicional esta mano vale más que el 9, o si es un desempate.

## Desarrollo de una ronda

1. Se baraja un mazo completo y se reparten **2 cartas** al jugador y 2 a la
   banca. Las de la banca quedan boca abajo.
2. El jugador puede **pedir** una carta más o **plantarse**. El máximo por mano
   es de **3 cartas**, así que se puede pedir una sola vez.
3. Cuando el jugador se planta, la banca revela sus cartas y pide mientras su
   puntaje sea **menor a 6** y tenga menos de 3 cartas.
4. Se comparan los puntajes. Gana el más alto.

### El empate favorece a la banca ❓

Si ambos tienen el mismo puntaje, **la ronda es para la banca**.

❓ En esta implementación la PC es siempre la banca, por lo que esa ventaja no
rota nunca y el juego queda sesgado en contra del jugador. En el juego
tradicional la banca rota entre los jugadores. Corregirlo está previsto para la
Fase 4.

## Fin de la partida

El primero en llegar a **10 rondas ganadas** gana. El marcador se reinicia y se
puede empezar de nuevo.

## Diferencias conocidas con el juego tradicional

Estas son ausencias reconocidas, no errores de esta documentación:

- **No hay apuestas.** El Maka'i se juega apostando; acá solo se cuentan rondas.
- **La banca no rota.** Ver arriba.
- **No hay múltiples jugadores.** Solo jugador contra PC.
- **La banca juega con una estrategia fija** (umbral de 6) que ignora por
  completo la mano del jugador.
