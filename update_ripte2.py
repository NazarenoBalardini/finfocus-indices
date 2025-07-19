#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Rutas de los JSON
RIPTE_FILE   = "indices/ripte.json"
RIPTE2_FILE  = "indices/ripte2.json"

# Abreviaturas de meses en español en orden
ABBR_MONTHS = [
    "ene","feb","mar","abr","may","jun",
    "jul","ago","sep","oct","nov","dic"
]

def cargar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_key(k: str) -> datetime:
    """Parsea claves 'may-25' → datetime(2025,5,1), corrige siglo."""
    mon_abbr, yy = k.split("-")
    m = ABBR_MONTHS.index(mon_abbr) + 1
    yy_int = int(yy)
    current_yy = datetime.now().year % 100
    if yy_int > current_yy:
        y = 1900 + yy_int
    else:
        y = 2000 + yy_int
    return datetime(y, m, 1)

def main():
    ripte  = cargar(RIPTE_FILE)
    ripte2 = cargar(RIPTE2_FILE)

    if not ripte:
        print(f"No hay datos en {RIPTE_FILE}.")
        return

    # 1) Última clave según fecha real
    last_key = max(ripte.keys(), key=parse_key)
    last_val = ripte[last_key]

    # 2) Sumamos **2** meses
    dt_last = parse_key(last_key)
    dt_next = dt_last + relativedelta(months=2)

    new_key = f"{ABBR_MONTHS[dt_next.month-1]}-{str(dt_next.year)[2:]}"
    new_val = last_val

    print(f"Última: {last_key} → {last_val}")
    print(f"Nuevo 2 meses: {new_key} → {new_val}")

    # 3) Insertar solo si no existe
    if new_key in ripte2:
        print(f"'{new_key}' ya existe en {RIPTE2_FILE}, nada que hacer.")
    else:
        ripte2[new_key] = new_val
        guardar(ripte2, RIPTE2_FILE)
        print(f"✅ Agregado '{new_key}': {new_val} a {RIPTE2_FILE}")

if __name__ == "__main__":
    main()
