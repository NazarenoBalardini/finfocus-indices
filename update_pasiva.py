#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
from datetime import datetime, timedelta

SERIE_ID    = "43"
API_BASE    = "https://api.bcra.gob.ar/estadisticas/v1"
ACTIVO_FILE = "indices/pasiva.json"

def cargar_pasiva():
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_pasiva(data):
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_nuevos(desde_date, hasta_date):
    """
    Llama al endpoint v1.0 con rango de fecha-time, devuelve lista de {'fecha', 'valor'}.
    """
    # Añadimos hora para cumplir formato DateTime de la API
    desde = f"{desde_date}T00:00:00"
    hasta = f"{hasta_date}T23:59:59"
    url   = f"{API_BASE}/datosvariable/{SERIE_ID}/{desde}/{hasta}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        print(f"WARNING: HTTP {code} al pedir {desde_date} → {hasta_date}, resultados omitidos.")
        return []
    except requests.RequestException as e:
        print(f"WARNING: Error de red: {e}")
        return []

    payload = resp.json()
    return payload.get("results", [])

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Rango: desde el día siguiente a la última fecha registrada
    if fechas:
        ult   = datetime.fromisoformat(fechas[-1]).date()
        inicio = (ult + timedelta(days=1)).isoformat()
    else:
        # Si no hay datos, arrancamos 30 días atrás
        inicio = (datetime.now().date() - timedelta(days=30)).isoformat()
    fin = datetime.now().date().isoformat()

    print(f"Buscando serie {SERIE_ID} desde {inicio} hasta {fin}...")
    obs = obtener_nuevos(inicio, fin)

    añadidos = 0
    for rec in obs:
        # La API v1 devuelve {"fecha":"YYYY-MM-DDT00:00:00","valor":"123.45"} o keys 'd'/'v'
        fecha = rec.get("fecha", rec.get("d", ""))[:10]
        valor = rec.get("valor", rec.get("v", None))
        try:
            v = float(valor)
        except Exception:
            continue
        if fecha not in data:
            data[fecha] = v
            añadidos += 1

    if añadidos:
        guardar_pasiva(data)
        print(f"✅ Añadidas {añadidos} observaciones a {ACTIVO_FILE}.")
    else:
        print("⚠️ No hubo nuevas observaciones para agregar.")

if __name__ == "__main__":
    main()
