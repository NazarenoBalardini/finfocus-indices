#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta

# Suprimir el warning de "InsecureRequestWarning"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERIE_ID    = "43"
API_BASE    = "https://api.bcra.gob.ar/estadisticas/v1"
ACTIVO_FILE = "indices/pasiva.json"

def cargar_pasiva():
    """Carga el JSON existente o devuelve {} si no existe."""
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_pasiva(data):
    """Guarda el dict en pasiva.json con indentado."""
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_nuevos(desde: str, hasta: str):
    """
    Llama al endpoint oficial para la serie 43, rango YYYY-MM-DD.
    Devuelve lista de dicts con keys 'fecha' y 'valor'.
    """
    url = f"{API_BASE}/datosvariable/{SERIE_ID}/{desde}/{hasta}"
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("results", [])

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Defino rango: día siguiente a la última fecha registrada
    if fechas:
        ultima = datetime.fromisoformat(fechas[-1]).date()
        desde  = (ultima + timedelta(days=1)).isoformat()
    else:
        desde  = (datetime.now().date() - timedelta(days=30)).isoformat()
    hasta = datetime.now().date().isoformat()

    print(f"Buscando datos de la serie {SERIE_ID} desde {desde} hasta {hasta}...")
    obs = obtener_nuevos(desde, hasta)

    añadidos = 0
    for x in obs:
        # La API devuelve "fecha":"YYYY-MM-DDT00:00:00"
        d = x.get("fecha", "")[:10]
        # Convertimos a float; la API oficial usa punto decimal
        try:
            v = float(x.get("valor", 0))
        except (TypeError, ValueError):
            continue
        if d not in data:
            data[d] = v
            añadidos += 1

    if añadidos:
        guardar_pasiva(data)
        print(f"Añadidas {añadidos} observaciones a {ACTIVO_FILE}.")
    else:
        print("No hubo nuevas observaciones para agregar.")

if __name__ == "__main__":
    main()
