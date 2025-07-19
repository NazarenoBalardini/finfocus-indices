#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
from datetime import datetime, timedelta

# Código de la serie "Tasa de uso de la Justicia" en la API del BCRA
SERIE_CODE  = "43"
API_URL     = f"https://api.estadisticasbcra.com/serie/{SERIE_CODE}"
API_KEY     = os.getenv("BCRA_API_KEY")  # Se inyecta desde GitHub Secrets
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

def obtener_nuevos(desde, hasta):
    """
    Llama al endpoint de BCRA para la serie 43 entre dos fechas
    y devuelve lista de {"d":"YYYY-MM-DD","v":valor}.
    """
    headers = {"Authorization": f"BEARER {API_KEY}"}
    params  = {"start_date": desde, "end_date": hasta}
    resp    = requests.get(API_URL, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def main():
    if not API_KEY:
        raise RuntimeError("Falta la variable de entorno BCRA_API_KEY.")
    
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Defino rango: desde última fecha +1 día (o hace 30 días si está vacío)
    if fechas:
        ult   = datetime.fromisoformat(fechas[-1]).date()
        desde = (ult + timedelta(days=1)).isoformat()
    else:
        desde = (datetime.now().date() - timedelta(days=30)).isoformat()
    hasta = datetime.now().date().isoformat()

    print(f"Buscando datos de la serie 43 desde {desde} hasta {hasta}...")
    obs = obtener_nuevos(desde, hasta)

    añadidos = 0
    for x in obs:
        d, v = x.get("d"), x.get("v")
        if d and (d not in data):
            data[d] = v
            añadidos += 1

    if añadidos:
        guardar_pasiva(data)
        print(f"Añadidas {añadidos} observaciones a {ACTIVO_FILE}.")
    else:
        print("No hay nuevas observaciones para agregar.")

if __name__ == "__main__":
    main()
