#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime, timedelta

# Desactivar warnings SSL inseguro
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

def obtener_nuevos(desde_date, hasta_date):
    """
    Llama al endpoint v1.0 con rango de fecha-time, devuelve lista de {'fecha','valor'}.
    Se usa verify=False para evitar errores de certificado.
    """
    desde = f"{desde_date}T00:00:00"
    hasta = f"{hasta_date}T23:59:59"
    url   = f"{API_BASE}/datosvariable/{SERIE_ID}/{desde}/{hasta}"
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
    except requests.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        print(f"WARNING: HTTP {code} al pedir {desde_date} → {hasta_date}, omitido.")
        return []
    except requests.RequestException as e:
        print(f"WARNING: Error de red al pedir {desde_date} → {hasta_date}: {e}")
        return []

    payload = resp.json()
    return payload.get("results", [])

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Calcula rango a pedir: desde día siguiente a última fecha guardada
    if fechas:
        ultima = datetime.fromisoformat(fechas[-1]).date()
        inicio = (ultima + timedelta(days=1)).isoformat()
    else:
        inicio = (datetime.now().date() - timedelta(days=30)).isoformat()
    fin = datetime.now().date().isoformat()

    print(f"Buscando serie {SERIE_ID} desde {inicio} hasta {fin}...")
    obs = obtener_nuevos(inicio, fin)

    añadidos = 0
    for rec in obs:
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
