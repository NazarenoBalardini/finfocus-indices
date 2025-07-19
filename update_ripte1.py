#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Rutas de los JSON
RIPTE_FILE  = "indices/ripte.json"
RIPTE1_FILE = "indices/ripte1.json"

# Abreviaturas de meses en español en orden
ABBR_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

def cargar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_key(k: str) -> datetime:
    """Parsea claves tipo 'may-25' a datetime(year, month, 1) con siglo ajustado."""
    mon_abbr, yy = k.split("-")
    m = ABBR_MONTHS.index(mon_abbr) + 1
    yy_int = int(yy)
    current_yy = datetime.now().year % 100
    # si es mayor al actual, es del siglo XX
    if yy_int > current_yy:
        y = 1900 + yy_int
    else:
        y = 2000 + yy_int
    return datetime(y, m, 1)

def main():
    ripte  = cargar(RIPTE_FILE)
    ripte1 = cargar(RIPTE1_FILE)

    # debug opcional
    print("DEBUG ripte keys:", sorted(ripte.keys(), key=parse_key))
    print("DEBUG ripte1 keys:", sorted(ripte1.keys(), key=parse_key))

    if not ripte:
        print(f"No hay datos en {RIPTE_FILE}.")
        return

    # 1) Última clave real
    last_key = max(ripte.keys(), key=parse_key)
    last_val = ripte[last_key]
    print("DEBUG last_key:", last_key, "value:", last_val)

    # 2) Sumar un mes
    dt_last = parse_key(last_key)
    dt_next = dt_last + relativedelta(months=1)
    new_key = f"{ABBR_MONTHS[dt_next.month-1]}-{str(dt_next.year)[2:]}"
    new_val = last_val
    print("DEBUG new_key:", new_key, "new_val:", new_val)

    # 3) Insertar si no existe
    if new_key in ripte1:
        print(f"'{new_key}' ya existe en {RIPTE1_FILE}, nada que hacer.")
    else:
        ripte1[new_key] = new_val
        guardar(ripte1, RIPTE1_FILE)
        print(f"✅ Agregado '{new_key}': {new_val} a {RIPTE1_FILE}")

if __name__ == "__main__":
    main()
