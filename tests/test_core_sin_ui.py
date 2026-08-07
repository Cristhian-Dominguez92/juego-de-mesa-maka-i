"""Hace cumplir la regla arquitectónica: makai/core no depende de UI ni audio.

Es lo que permite testear las reglas sin abrir una ventana. Si alguien importa
flet dentro de core, este test falla.
"""

import ast
import pathlib

CORE = pathlib.Path(__file__).parent.parent / "makai" / "core"

PROHIBIDOS = {"flet", "pygame", "tkinter", "pyglet", "PIL"}


def modulos_importados(archivo):
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            yield nodo.module.split(".")[0]


def test_core_no_importa_ui_ni_audio():
    infracciones = []
    for archivo in CORE.glob("*.py"):
        for modulo in modulos_importados(archivo):
            if modulo in PROHIBIDOS:
                infracciones.append(f"{archivo.name} importa {modulo}")
    assert not infracciones, "makai/core debe ser puro: " + "; ".join(infracciones)


def test_el_core_se_importa_sin_flet_instalado():
    import importlib
    import sys

    # Aunque flet estuviera instalado, importar el core no debe requerirlo.
    modulos_antes = set(sys.modules)
    importlib.import_module("makai.core")
    nuevos = set(sys.modules) - modulos_antes
    assert not any(m.split(".")[0] in PROHIBIDOS for m in nuevos)


def test_hay_archivos_de_core_para_revisar():
    # Evita que el test pase trivialmente si se mueve el directorio.
    assert list(CORE.glob("*.py"))
