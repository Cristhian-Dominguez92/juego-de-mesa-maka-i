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

⚠️ El APK generado está **sin firmar**: sirve para probar en un dispositivo con
"orígenes desconocidos" habilitado, pero no es publicable en Google Play. La
firma se configura en `[tool.flet.android.signing]` dentro de `pyproject.toml`.

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
Gana quien tenga más puntaje; el empate favorece a la banca. La partida se juega
a 10 rondas ganadas.

Están documentadas en detalle en [docs/REGLAS.md](docs/REGLAS.md), incluyendo
qué partes se infirieron del código original y cuáles faltan por confirmar.

## Estructura

```
main.py                  Capa de presentación (Flet). Solo dibuja y traduce clics.
makai/core/              Lógica de juego pura, sin dependencias de UI.
  cartas.py                Baraja española de 40 cartas.
  reglas.py                Puntuación y resolución de rondas.
  partida.py               Máquina de estados de la partida.
makai/ui/                Apoyo a la presentación.
  layout.py                Medidas responsive (aritmética pura, sin Flet).
  audio.py                 Música y efectos sobre ft.Audio, con silencio.
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

- **Assets sin licencia verificada.** Las 40 imágenes de cartas son de origen
  desconocido. Ver [CREDITS.md](CREDITS.md).
- **Sin música de fondo.** Se retiró un tema comercial sin licencia. El juego
  ya la reproduce en bucle si dejás un archivo libre en
  `assets/Recursos/background_music.mp3` (ver CREDITS.md); sin él, funciona en
  silencio.
- **La banca no rota** y el empate siempre la favorece, así que el juego está
  sesgado en contra del jugador. Ver [docs/REGLAS.md](docs/REGLAS.md).
- **Sin apuestas.** El Maka'i tradicional se juega apostando.
- **APK sin firmar.**
- **El audio en Android no está verificado en un dispositivo real.** Se migró a
  `ft.Audio`, que sí se empaqueta, pero no se probó el APK.

## Licencia

Código bajo [MIT](LICENSE). Los assets tienen licencias propias — ver
[CREDITS.md](CREDITS.md).
