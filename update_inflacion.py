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

CATALOGO      = (
    "https://www.bcra.gob.ar/Catalogo/Content/files/json/"
    "principales-variables-v3.json"
)
DATA          = "indices/inflacion.json"
ID_INFLACION  = 27  # idVariable de Inflación mensual (como entero)
ABBR          = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def obtener_indec():
    resp = requests.get(CATALOGO, timeout=10, verify=False)
    resp.raise_for_status()
    catalogo = resp.json()

    obs = []
    for entry in catalogo:
        # si viene como string, skip
        if not isinstance(entry, dict):
            continue
        # Puede venir en 'c' (string) o en 'idVariable' (int)
        idvar = entry.get("idVariable", entry.get("c"))
        try:
            idvar = int(idvar)
        except Exception:
            continue
        if idvar != ID_INFLACION:
            continue

        fch = entry.get("fch")     # ej. '30/06/2025'
        val = entry.get("valor")   # ej. '1,6'
        if not fch or not val:
            continue
        # convertimos '1,6' → 1.6
        pct = float(val.replace(".", "").replace(",", "."))
        obs.append((fch, pct))

    if not obs:
        raise RuntimeError("No encontré datos de inflación mensual (ID 27).")

    # tomamos la última fecha
    def parse_fch(s):
        return datetime.strptime(s, "%d/%m/%Y")
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

    # calcular mes anterior
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
        raise RuntimeError(f"Falta el valor de {prev_key} en {DATA}")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val * (1 + pct / 100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__ == "__main__":
    main()
