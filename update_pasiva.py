#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta, date

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def _llamada(desde: str, hasta: str):
    url = f"{API_BASE}/datosvariable/{SERIE_ID}/{desde}/{hasta}"
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()
    return resp.json().get("results", [])

def obtener_nuevos(desde: str, hasta: str):
    try:
        return _llamada(desde, hasta)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        # Si pide un solo día y da 500, reintenta con 2 días
        if code == 500 and desde == hasta:
            antes = (date.fromisoformat(desde) - timedelta(days=1)).isoformat()
            print(f"WARNING: 500 en {desde}, reintentando {antes}→{hasta}")
            try:
                return _llamada(antes, hasta)
            except Exception:
                print("ERROR: fallback falló también.")
                return []
        print(f"WARNING: HTTP {code} en {desde}→{hasta}")
        return []
    except requests.RequestException as e:
        print(f"WARNING: red fallida {desde}→{hasta}: {e}")
        return []

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    if fechas:
        ultima = datetime.fromisoformat(fechas[-1]).date()
        desde  = (ultima + timedelta(days=1)).isoformat()
    else:
        desde  = (datetime.now().date() - timedelta(days=30)).isoformat()
    hasta = datetime.now().date().isoformat()

    print(f"Buscando serie {SERIE_ID} desde {desde} hasta {hasta}...")
    obs = obtener_nuevos(desde, hasta)

    añadidos = 0
    for x in obs:
        d = x.get("d") or x.get("fecha", "")[:10]
        v = x.get("v") or x.get("valor")
        try:
            v = float(v)
        except Exception:
            continue
        if d not in data:
            data[d] = v
            añadidos += 1

    if añadidos:
        guardar_pasiva(data)
        print(f"Añadidas {añadidos} observaciones a {ACTIVO_FILE}.")
    else:
        print("No hubo nuevas observaciones.")

if __name__ == "__main__":
    main()
