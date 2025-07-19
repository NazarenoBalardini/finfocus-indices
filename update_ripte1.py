#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Rutas de los JSON
RIPTE_FILE  = "indices/ripte.json"
RIPTE1_FILE = "indices/ripte1.json"

# Abreviaturas de meses en español
ABBR_MONTHS = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 1) Carga ambos JSON
    ripte  = cargar(RIPTE_FILE)
    ripte1 = cargar(RIPTE1_FILE)

    if not ripte:
        print(f"No hay datos en {RIPTE_FILE}.")
        return

    # 2) Extrae la última clave de ripte.json
    #    Ordenamos lexicográficamente porque 'ene-25' < 'feb-25' < ... < 'dic-25'
    last_key = sorted(ripte.keys())[-1]
    last_val = ripte[last_key]

    # 3) Parseamos mes y año
    mon_abbr, yy = last_key.split("-")
    m = ABBR_MONTHS.index(mon_abbr) + 1
    y = 2000 + int(yy)

    # 4) Sumamos un mes
    dt_next = datetime(y, m, 1) + relativedelta(months=1)
    new_key = f"{ABBR_MONTHS[dt_next.month-1]}-{str(dt_next.year)[2:]}"
    new_val = last_val

    # 5) Añadimos si no existe
    if new_key in ripte1:
        print(f"{new_key} ya existe en {RIPTE1_FILE}, nada que hacer.")
    else:
        ripte1[new_key] = new_val
        guardar(ripte1, RIPTE1_FILE)
        print(f"✅ Agregado '{new_key}': {new_val} a {RIPTE1_FILE}")

if __name__ == "__main__":
    main()
