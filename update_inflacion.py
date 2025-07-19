#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# JSON oficial de variables
CATALOGO = (
    "https://www.bcra.gob.ar/Catalogo/Content/files/json/"
    "principales-variables-v3.json"
)
DATA         = "indices/inflacion.json"
ID_INFLACION = "27"  # idVariable de Inflación mensual
ABBR = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def obtener_indec():
    """
    Descarga el JSON de principales-variables-v3 y
    extrae la última observación de idVariable=27.
    """
    resp = requests.get(CATALOGO, timeout=10, verify=False)
    resp.raise_for_status()
    catalogo = resp.json()  # lista de dicts o strings

    obs = []
    for item in catalogo:
        # Si el item es str, parsearlo
        entry = json.loads(item) if isinstance(item, str) else item
        if str(entry.get("c")) != ID_INFLACION:
            continue
        fch   = entry.get("fch")    # '30/06/2025'
        val_s = entry.get("valor")  # '1,6'
        if not fch or not val_s:
            continue
        # convertir porcentaje
        pct = float(val_s.replace(".", "").replace(",", "."))
        obs.append((fch, pct))

    if not obs:
        raise RuntimeError("No encontré datos de inflación mensual en el catálogo")

    # tomar la última fecha
    def parse_fch(f): 
        return datetime.strptime(f, "%d/%m/%Y")
    fch_str, pct = max(obs, key=lambda x: parse_fch(x[0]))

    dt    = parse_fch(fch_str)
    clave = f"{ABBR[dt.month-1]}-{str(dt.year)[2:]}"
    return clave, pct

def main():
    data = cargar()
    clave, pct = obtener_indec()
    print(f"BCRA IPC mensual: {clave} → {pct}%")

    if clave in data:
        print(f"{clave!r} ya existe en {DATA}, nada que hacer.")
        return

    # mes anterior
    mon, yy = clave.split("-")
    idx      = ABBR.index(mon)
    if idx == 0:
       	prev_mon = ABBR[-1]
       	prev_yy  = f"{int(yy)-1:02d}"
    else:
       	prev_mon = ABBR[idx-1]
       	prev_yy  = yy
    prev_key = f"{prev_mon}-{prev_yy}"

    if prev_key not in data:
        raise RuntimeError(f"Falta {prev_key} en {DATA}")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val * (1 + pct/100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__ == "__main__":
    main()
