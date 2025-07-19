#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta, date

# Desactivar warnings de SSL inseguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERIE_ID    = "43"
API_BASE    = "https://api.bcra.gob.ar/estadisticas/v2.0"
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

def _call_api(desde: str, hasta: str):
    url = f"{API_BASE}/datosvariable/{SERIE_ID}/{desde}/{hasta}"
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()
    return resp.json().get("results", [])

def obtener_nuevos(desde: str, hasta: str):
    """
    Solicita al API oficial v2.0 el rango dado.
    Si falla con 500 y era un solo día, reintenta incluyendo el día anterior.
    """
    try:
        results = _call_api(desde, hasta)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        # Solo fallback si es un 500 y pedimos un solo día
        if code == 500 and desde == hasta:
            prev = (date.fromisoformat(desde) - timedelta(days=1)).isoformat()
            print(f"WARNING: HTTP 500 en {desde}, reintentando rango {prev}→{hasta}")
            try:
                results = _call_api(prev, hasta)
            except Exception as e2:
                print(f"ERROR: fallback también falló: {e2}")
                return []
        else:
            print(f"WARNING: HTTP {code} al llamar {desde}→{hasta}, omitiendo.")
            return []
    except requests.RequestException as e:
        print(f"WARNING: Error de red al llamar {desde}→{hasta}: {e}")
        return []

    # Si reintentamos con prev→hasta, results incluye dos días; filtramos solo el date original
    if desde != hasta:
        return results

    # inicio == fin: filtramos la única fecha que nos importa
    return [r for r in results if r.get("fecha", "").startswith(desde)]

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Rango a consultar: día siguiente a la última fecha guardada
    if fechas:
        ultima = datetime.fromisoformat(fechas[-1]).date()
        desde  = (ultima + timedelta(days=1)).isoformat()
    else:
        # Si no hay datos, arrancamos hace 30 días
        desde  = (datetime.now().date() - timedelta(days=30)).isoformat()
    hasta = datetime.now().date().isoformat()

    print(f"Buscando datos de la serie {SERIE_ID} desde {desde} hasta {hasta}...")
    obs = obtener_nuevos(desde, hasta)

    añadidos = 0
    for x in obs:
        d = x.get("fecha", "")[:10]
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
