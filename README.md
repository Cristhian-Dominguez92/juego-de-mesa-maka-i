# Maka'i

Implementación digital del **Maka'i**, el tradicional juego de cartas paraguayo,
hecha con [Flet](https://flet.dev) (Python) para escritorio y Android.

> **Estado: prototipo.** Jugable en escritorio contra la PC. Ver
> [Limitaciones conocidas](#limitaciones-conocidas) antes de distribuirlo.

## Requisitos

- **Python >= 3.10 y < 3.14.** Flet 0.28.3 no publica wheels para 3.14; si tenés
  3.14 instalado, el proyecto no va a arrancar. Usá 3.12 o 3.13.
- Para compilar el APK: [Flutter](https://docs.flutter.dev/get-started/install)
  (canal `stable`) y el Android SDK.

## Instalación

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements-dev.txt
```

## Ejecutar

```bash
python main.py
```

## Compilar el APK

```bash
flet build apk
```

El resultado queda en `build/apk/`. El CI de GitHub Actions lo compila
automáticamente en cada push a `main` (ver `.github/workflows/build.yml`).

Por defecto el APK sale **sin firmar**: sirve para probar en un dispositivo con
"orígenes desconocidos" habilitado, pero no es publicable en Google Play.

### Firmar el APK

El keystore contiene tu clave privada de publicación. **Generalo vos** y no lo
compartas: quien lo tenga junto con su contraseña puede publicar
actualizaciones en tu nombre. Google Play no permite cambiar la clave de una
app ya publicada, así que si lo perdés, perdés la app.

```bash
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Guardalo fuera del repositorio (`*.jks` está en `.gitignore`) y hacé una copia
de seguridad en un lugar seguro.

Para firmar localmente, descomentá `[tool.flet.android.signing]` en
`pyproject.toml` y exportá las contraseñas antes de compilar:

```bash
export FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD='tu-contraseña'
```

Para que el CI firme, cargá tres secretos en el repositorio de GitHub
(Settings → Secrets and variables → Actions):

| Secreto | Contenido |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | El `.jks` codificado: `base64 -w0 upload-keystore.jks` |
| `ANDROID_KEYSTORE_PASSWORD` | Contraseña del keystore |
| `ANDROID_KEY_PASSWORD` | Contraseña de la clave |

Sin esos secretos el workflow sigue funcionando: compila igual y avisa que el
APK va sin firmar.

## Tests

```bash
pytest -q
```

Para el ciclo rápido, saltando los que juegan partidas completas:

```bash
pytest -q -m "not lento"
```

Los tests de `makai/core/` no necesitan Flet. Los de `tests/test_ui_flujo.py`
sí (se saltan solos si no está instalado): construyen los controles reales de
`main.py` contra un `Page` falso, que es lo que detecta cambios incompatibles
en la API de Flet.

> **Si la suite tarda minutos en Windows**, casi siempre es el antivirus
> escaneando el import de `flet` (`flet.core.icons` es un módulo enorme). Los
> tests en sí tardan segundos; el costo está en el import. Agregar el
> directorio del proyecto y el del venv a las exclusiones de Windows Defender
> lo resuelve.

## Reglas del juego

Cada jugador recibe 2 cartas y puede pedir una tercera (máximo 3). El puntaje es
la suma de las cartas, donde las figuras (10, 11, 12) valen 10, y **solo cuenta
el último dígito** de la suma. Tres figuras es una mano especial que vale 8.5.
Gana quien tenga más puntaje; el empate favorece a la banca, y la banca pasa a
quien gane la ronda.

Se juega por fichas: cada ronda se apuesta y el ganador se lleva la apuesta del
otro. La partida termina cuando alguien se queda sin fichas.

Están documentadas en detalle en [docs/REGLAS.md](docs/REGLAS.md).

## Estructura

```
main.py                  Capa de presentación (Flet). Solo dibuja y traduce clics.
makai/core/              Lógica de juego pura, sin dependencias de UI.
  cartas.py                Baraja española de 40 cartas.
  reglas.py                Puntuación y resolución de rondas.
  partida.py               Máquina de estados de la partida.
makai/ai/                Estrategias de la PC, por nivel de dificultad.
makai/ui/                Apoyo a la presentación.
  layout.py                Medidas responsive (aritmética pura, sin Flet).
  animacion.py             Reparto y volteo de cartas.
  audio.py                 Música y efectos sobre ft.Audio, con silencio.
  estadisticas.py          Historial del jugador, persistido.
  preferencias.py          Dificultad elegida, persistida.
  textos.py                Contenido de la pantalla de reglas.
tests/                   Suite de tests (no requiere Flet).
docs/REGLAS.md           Reglas del juego, con lo confirmado y lo pendiente.
pyproject.toml           Metadatos y configuración de `flet build`.
requirements.txt         Dependencias que se empaquetan en el APK.
requirements-dev.txt     Dependencias solo de escritorio + herramientas.
assets/Recursos/         Imágenes de cartas y audio.
tools/                   Scripts auxiliares, no forman parte del juego.
_local/                  Archivos locales fuera de control de versiones.
```

**Regla de arquitectura:** `makai/core/` no puede importar `flet`, `pygame` ni
ninguna otra librería de UI o audio. Es lo que permite testear las reglas sin
abrir una ventana, y está verificado por `tests/test_core_sin_ui.py`.

## Limitaciones conocidas

Estas son las razones por las que el proyecto todavía no es distribuible:

- **APK sin firmar** por defecto. Ver [Firmar el APK](#firmar-el-apk).
- **El APK nunca se compiló.** Hace falta Flutter y el Android SDK; el primer
  `flet build apk` puede necesitar ajustes.
- **El audio en Android no está verificado en un dispositivo real.** Se migró a
  `ft.Audio`, que sí se empaqueta, pero no se probó el APK.
- **`victoria.mp3` es de Mixkit**, el único asset de terceros que queda. Su
  licencia permite este uso, pero conviene confirmar los términos vigentes.
  Ver [CREDITS.md](CREDITS.md).
- **El historial de git todavía contiene los assets retirados** (el tema con
  copyright y los escaneos de origen desconocido). Purgarlos requiere reescribir
  la historia del repositorio; ver CREDITS.md.

## Licencia

Código bajo [MIT](LICENSE). Los assets tienen licencias propias — ver
[CREDITS.md](CREDITS.md).
