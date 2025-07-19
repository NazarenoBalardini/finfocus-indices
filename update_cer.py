#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_JSON      = "indices/cer.json"
URL_BCRA      = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
TARGET_PREFIX = "CER | Base 02/02/2002"  # texto distintivo en la primera celda

def cargar():
    if os.path.exists(URL_JSON):
        with open(URL_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(data):
    with open(URL_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_nuevo():
    resp = requests.get(URL_BCRA, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Buscamos la tabla y cada fila
    tabla = soup.find("table")
    if not tabla:
        raise RuntimeError("No encontré la tabla de Principales Variables.")

    for tr in tabla.select("tbody tr"):
        celdas = [td.get_text(strip=True) for td in tr.select("td")]
        if not celdas or not celdas[0].startswith(TARGET_PREFIX):
            continue

        # Supongamos estructura: [ "CER | Base ...", "19/07/2025", "607,6799", ... ]
        fecha_str = celdas[1]          # e.g. "19/07/2025"
        val_str   = celdas[2]          # e.g. "607,6799"
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        clave = dt.strftime("%Y-%m-%d")  # "2025-07-19"
        valor = float(val_str.replace(".", "").replace(",", "."))

        return clave, valor

    raise RuntimeError(f"No encontré ninguna fila que comience con '{TARGET_PREFIX}'")

def main():
    data = cargar()
    clave, valor = obtener_nuevo()
    print(f"CER: {clave} → {valor}")

    if clave in data:
        print(f"{clave!r} ya existe en {URL_JSON}, nada que hacer.")
        return

    data[clave] = valor
    guardar(data)
    print(f"✅ Agregado {clave}: {valor}")

if __name__ == "__main__":
    main()
