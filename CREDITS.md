# Créditos y licencias de assets

El **código** de este proyecto está bajo licencia MIT (ver [LICENSE](LICENSE)).
Los **assets** (imágenes y audio) tienen licencias propias y se listan acá.

> Regla del proyecto: ningún asset entra a `assets/` sin una fila en esta tabla
> indicando origen y licencia. Si no se puede documentar, no se distribuye.

## Audio

| Archivo | Origen | Licencia | Estado |
|---|---|---|---|
| `background.wav` | Generado por `tools/generar_sonidos.py` | Propio (MIT) | ✅ OK |
| `applause.wav` | Generado por `tools/generar_sonidos.py` | Propio (MIT) | ✅ OK |
| `victoria.mp3` | Mixkit (`tools/descargar_victoria.py`) | Mixkit Free License | ⚠️ Verificar |
| *(música de fondo)* | — | — | ❌ **Faltante** |

### ⚠️ `victoria.mp3`

Descargado de Mixkit. Su licencia gratuita permite uso comercial sin
atribución, pero **prohíbe redistribuir el archivo como parte de un producto
donde el sonido en sí sea el valor principal**. Para un juego es un uso
aceptable, pero conviene confirmar los términos vigentes en
<https://mixkit.co/license/> y dejar constancia de la fecha de verificación.

### ❌ Música de fondo — ACCIÓN REQUERIDA

El repositorio distribuía `Arrocha Rave - Tnga (00).mp3`, un tema comercial
sin licencia documentada. Se quitó del control de versiones y de `assets/`.
El archivo sigue en `_local/` (ignorado por git) para que no se pierda, pero
**no debe volver a `assets/`**.

Para reponerlo hay que colocar un tema con licencia compatible en:

    assets/Recursos/background_music.mp3

El juego ya funciona sin ese archivo (no suena música de fondo, no falla).

Fuentes recomendadas con licencia clara:

- [Incompetech](https://incompetech.com/music/royalty-free/) — CC-BY (requiere atribución)
- [Freesound](https://freesound.org/) — filtrar por CC0
- [Free Music Archive](https://freemusicarchive.org/) — verificar licencia por pista
- [Pixabay Music](https://pixabay.com/music/) — licencia propia, uso comercial permitido

Si la licencia elegida exige atribución, agregarla en esta tabla **y** en una
pantalla de créditos dentro del juego.

### Pendiente: purgar el historial de git

Quitar el archivo del working tree no lo borra del historial. El repositorio es
público, así que el MP3 sigue siendo descargable desde commits anteriores.
Para purgarlo hace falta reescribir el historial con
[git-filter-repo](https://github.com/newren/git-filter-repo):

```bash
git filter-repo --path "assets/Recursos/Arrocha Rave - Tnga (00).mp3" --invert-paths
```

Esto **reescribe todos los commits y obliga a un `push --force`**. Es una
operación destructiva sobre un repo público: decidila con calma y avisá a
cualquiera que tenga un clon. No se ejecutó automáticamente.

## Imágenes

| Archivo | Origen | Licencia | Estado |
|---|---|---|---|
| `1..12_{oro,copa,espada,basto}.jpeg` (40 cartas) | Desconocido | Desconocida | ❌ **Verificar** |
| `dorso.jpeg` | Desconocido | Desconocida | ❌ **Verificar** |

### ❌ Baraja española — ACCIÓN REQUERIDA

No hay registro del origen de estos 40 escaneos. Si provienen de un mazo
comercial (Fournier, Heraclio Fournier, etc.), el diseño puede estar protegido
y no sería distribuible.

Opciones, de menor a mayor esfuerzo:

1. **Baraja de dominio público.** Existen barajas españolas con derechos
   expirados y versiones vectoriales libres en Wikimedia Commons.
2. **Assets con licencia abierta.** Buscar "Spanish deck" en OpenGameArt o
   itch.io filtrando por CC0.
3. **Arte propio.** Lo más costoso, pero es lo que le daría identidad visual
   propia al juego.

Mientras esto no se resuelva, el proyecto no debería publicarse en una tienda
de aplicaciones.
