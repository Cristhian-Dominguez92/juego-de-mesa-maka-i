"""Punto de entrada ASGI para desplegar el servidor en la nube (Render).

Uvicorn importa `app` de acá. No se usa para jugar en escritorio ni en LAN:
`python main.py` y `python main.py --servidor` siguen funcionando exactamente
igual que siempre.
"""

import flet as ft

from main import ASSETS_DIR
from main import main as jugar

app = ft.app(target=jugar, assets_dir=ASSETS_DIR, export_asgi_app=True)
