"""Descarga la baraja española de Heraclio Fournier (1878) desde Wikimedia.

La baraja está en **dominio público**: sus autores (Ignacio Díaz Olano y
Emilio Soubrier) murieron hace más de 70 años. Wikimedia la marca además con
Creative Commons Public Domain Mark 1.0. No exige atribución ni ShareAlike.

Los archivos originales pesan 3,24 MB cada uno (2434x3846). Este script pide
las miniaturas que Wikimedia genera al vuelo, que es lo que el juego necesita.

Los nombres en Commons están en euskera —Fournier era de Vitoria— así que hay
que traducirlos a los que espera el juego (`Carta.nombre_archivo`).

Uso:
    python tools/descargar_baraja.py --destino assets/Recursos
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"

#: Wikimedia rechaza pedidos sin un User-Agent que identifique la herramienta.
AGENTE = "MakaiCardDownloader/1.0 (https://github.com/Cristhian-Dominguez92/juego-de-mesa-maka-i)"

PLANTILLA = "Fournier 1878 - {rango} {palo} (ref. 44470).png"
ARCHIVO_DORSO = "Fournier 1878 - Atzealdea (ref. 44470).png"

#: Rangos en euskera. txota = sota, zaldi = caballo, errege = rey.
RANGOS = {
    "bateko": 1,
    "biko": 2,
    "hiruko": 3,
    "lauko": 4,
    "bosteko": 5,
    "seiko": 6,
    "zazpiko": 7,
    "txota": 10,
    "zaldi": 11,
    "errege": 12,
}

#: Palos en euskera. urrea = oro, kopa = copa, ezpata = espada, bastoia = basto.
PALOS = {
    "urrea": "oro",
    "kopa": "copa",
    "ezpata": "espada",
    "bastoia": "basto",
}


def _pedir(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(peticion, timeout=60) as respuesta:
        return respuesta.read()


def urls_de_miniaturas(titulos: list[str], ancho: int) -> dict[str, str]:
    """Pregunta a la API por la miniatura de cada archivo.

    Se consulta la API en vez de armar la URL a mano porque la ruta real
    depende de un hash del nombre.
    """
    urls: dict[str, str] = {}
    # La API acepta hasta 50 títulos por pedido.
    for i in range(0, len(titulos), 50):
        lote = titulos[i : i + 50]
        parametros = urllib.parse.urlencode(
            {
                "action": "query",
                "titles": "|".join(f"File:{t}" for t in lote),
                "prop": "imageinfo",
                "iiprop": "url|size",
                "iiurlwidth": ancho,
                "format": "json",
            }
        )
        datos = json.loads(_pedir(f"{API}?{parametros}"))
        for pagina in datos["query"]["pages"].values():
            if "imageinfo" not in pagina:
                raise RuntimeError(f"Wikimedia no reconoce {pagina.get('title')!r}")
            titulo = pagina["title"].removeprefix("File:")
            urls[titulo] = pagina["imageinfo"][0]["thumburl"]
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", default="assets/Recursos")
    parser.add_argument("--ancho", type=int, default=400, help="ancho de la miniatura en píxeles")
    args = parser.parse_args()

    destino = pathlib.Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    # Nombre en Commons -> nombre que espera el juego.
    equivalencias = {ARCHIVO_DORSO: "dorso.png"}
    for rango_eu, valor in RANGOS.items():
        for palo_eu, palo in PALOS.items():
            origen = PLANTILLA.format(rango=rango_eu, palo=palo_eu)
            equivalencias[origen] = f"{valor}_{palo}.png"

    print(f"Consultando {len(equivalencias)} archivos en Wikimedia Commons...")
    urls = urls_de_miniaturas(list(equivalencias), args.ancho)

    total = 0
    for origen, nombre_final in sorted(equivalencias.items(), key=lambda p: p[1]):
        datos = _pedir(urls[origen])
        (destino / nombre_final).write_bytes(datos)
        total += len(datos)
        print(f"OK: {nombre_final} ({len(datos) // 1024} KB)")
        time.sleep(0.15)  # cortesía con los servidores de Wikimedia

    print(f"\nListo: {len(equivalencias)} archivos, {total // 1024} KB en total")


if __name__ == "__main__":
    main()
