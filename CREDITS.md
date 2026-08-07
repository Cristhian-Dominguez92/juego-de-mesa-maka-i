# Créditos y licencias de assets

El **código** de este proyecto está bajo licencia MIT (ver [LICENSE](LICENSE)).
Los **assets** (imágenes y audio) se listan acá con su origen.

> Regla del proyecto: ningún asset entra a `assets/` sin una fila en esta tabla
> indicando origen y licencia. Si no se puede documentar, no se distribuye.

## Imágenes

| Archivo | Origen | Licencia | Estado |
|---|---|---|---|
| `Recursos/1..12_{oro,copa,espada,basto}.webp` (40 cartas) | Baraja de Heraclio Fournier, 1878 | Dominio público | ✅ OK |
| `Recursos/dorso.webp` | Ídem | Dominio público | ✅ OK |
| `icon.png` | `tools/generar_icono.py` | Propio (MIT) | ✅ OK |

### La baraja

Es la baraja española clásica que Heraclio Fournier imprimió en Vitoria en
**1878**, diseñada por Ignacio Díaz Olano y Emilio Soubrier. Está **en dominio
público**: sus autores murieron hace más de setenta años. Wikimedia Commons la
marca además con Creative Commons Public Domain Mark 1.0.

**No exige atribución ni ShareAlike.** La acreditamos igual porque corresponde.

- [Categoría en Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Heraclio_Fournier%E2%80%99s_1878_card_deck)
- Los nombres allá están en euskera (`bateko urrea` = as de oros,
  `errege ezpata` = rey de espadas); `tools/descargar_baraja.py` los traduce.

Para reconstruir los assets desde cero:

```bash
python tools/descargar_baraja.py --ancho 300
```

```bash
python tools/optimizar_imagenes.py
```

El primero baja las miniaturas desde Wikimedia. El segundo las convierte a
WebP, y hace **dos cosas que importan**:

1. **Descarta el canal alfa**, aplanando sobre blanco. Los escaneos traen las
   esquinas redondeadas recortadas con transparencia; el redondeo lo hace ahora
   la interfaz con `border_radius` y `clip_behavior`.
2. **Levanta contraste, saturación y brillo.** Son cartas de 1878: el papel
   amarilleó y las tintas se apagaron. Tal cual vienen, sobre el verde de la
   mesa y al tamaño chico al que se muestran, se ven desvaídas. Los valores son
   constantes al principio del script.

Los originales pesan 3,24 MB cada uno (130 MB en total, inviable para un APK).
La cadena queda en **1,3 MB para las 41 imágenes**: menos de la quinta parte de
lo que pesaban los escaneos de origen desconocido que había antes.

### Generador propio de cartas (alternativa, no se usa)

`tools/generar_cartas.py` y `tools/baraja.py` dibujan una baraja completa con
aritmética pura, sin fuentes ni librerías de imagen. Se hizo antes de encontrar
la baraja Fournier y **no es lo que se distribuye**: el estilo es geométrico y
las figuras no son ilustradas.

Se conserva como respaldo. Si alguna vez hiciera falta una baraja cuya
titularidad sea enteramente del proyecto, ya está escrita:

```bash
python tools/generar_cartas.py --muestra
```

## Audio

| Archivo | Origen | Licencia | Estado |
|---|---|---|---|
| `Recursos/background_music.wav` | `tools/generar_musica.py` | Propio (MIT) | ✅ OK |
| `Recursos/background.wav` | `tools/generar_sonidos.py` | Propio (MIT) | ✅ OK |
| `Recursos/applause.wav` | `tools/generar_sonidos.py` | Propio (MIT) | ✅ OK |
| `Recursos/victoria.mp3` | Mixkit | Mixkit Free License | ⚠️ Verificar |

Regenerar la música:

```bash
python tools/generar_musica.py
```

Usa síntesis Karplus-Strong (ruido filtrado en bucle, que suena a cuerda
pulsada) sobre una progresión Lam–Fa–Do–Sol. Son 16 segundos que se repiten,
con fundido en ambos extremos para que el bucle no haga clic.

El juego prefiere `background_music.mp3` si existe, así que se puede reemplazar
por otro tema sin tocar código. Cualquier reemplazo necesita su fila en la
tabla.

### ⚠️ `victoria.mp3`

Descargado de Mixkit con `tools/descargar_victoria.py`. Su licencia gratuita
permite uso comercial sin atribución, pero **prohíbe redistribuir el archivo
como parte de un producto donde el sonido en sí sea el valor principal**. Para
un juego es un uso aceptable, pero conviene confirmar los términos vigentes en
<https://mixkit.co/license/> y dejar constancia de la fecha de verificación.

Si preferís no depender de un tercero, se puede generar un sonido de victoria
propio con el mismo enfoque que la música.

## Material retirado

### Música comercial

El repositorio distribuía `Arrocha Rave - Tnga (00).mp3`, un tema comercial sin
licencia documentada. Se quitó del control de versiones y de `assets/`. El
archivo sigue en `_local/` (ignorado por git) para que no se pierda, pero **no
debe volver**.

### Escaneos de la baraja

Las 40 imágenes originales eran de origen desconocido. Si provenían de un mazo
comercial, su diseño podía estar protegido. Fueron reemplazadas por la baraja
Fournier y quedaron en `_local/cartas_jpeg_originales/`, fuera de git.

### Pendiente: purgar el historial de git

Quitar un archivo del working tree no lo borra del historial. El repositorio es
público, así que tanto el MP3 como los escaneos siguen siendo descargables
desde commits anteriores. Para purgarlos hace falta reescribir el historial con
[git-filter-repo](https://github.com/newren/git-filter-repo):

```bash
git filter-repo --path "assets/Recursos/Arrocha Rave - Tnga (00).mp3" --invert-paths
```

Esto **reescribe todos los commits y obliga a un `push --force`**. Es una
operación destructiva sobre un repo público: decidila con calma y avisá a
cualquiera que tenga un clon. No se ejecutó automáticamente.
