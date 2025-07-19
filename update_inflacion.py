#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import requests
import urllib3
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL de Precios al consumidor en INDEC
URL     = "https://www.indec.gob.ar/indec/web/Nivel3-Tema-3-5"
DATA    = "indices/inflacion.json"

# Meses abreviados
ABBR = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar():
    if os.path.exists(DATA):
        with open(DATA, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar(d):
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def obtener_indec():
    """
    Usa regex directamente sobre el HTML para extraer:
      - mes (p.ej. 'junio'), año ('2025') y pct ('1,6')
    tras la cadena 'Precios al consumidor' y 'Variación mensual'.
    Devuelve ('jun-25', 1.6)
    """
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    txt = resp.text.replace("\n"," ")

    # Busca: Precios al consumidor ... Variación mensual ... Junio 2025 ... 1,6%
    m = re.search(
        r"Precios\s+al\s+consumidor.*?Variación\s+mensual.*?([A-Za-z]+)\s+(\d{4}).*?([\d]+,[\d]+)%",
        txt, re.IGNORECASE|re.DOTALL
    )
    if not m:
        raise RuntimeError("No pude extraer Precios al consumidor/Variación mensual con regex")

    mes_full, año, pct_str = m.group(1).lower(), m.group(2), m.group(3)
    mes_abbr = mes_full[:3]
    if mes_abbr not in ABBR:
        raise RuntimeError(f"Mes inesperado: {mes_full}")

    clave = f"{mes_abbr}-{año[-2:]}"
    pct = float(pct_str.replace(",", "."))

    return clave, pct

def main():
    data = cargar()
    clave, pct = obtener_indec()
    print(f"INDEC: {clave} → {pct}%")

    if clave in data:
        print(f"{clave!r} ya existe en {DATA}, nada que hacer.")
        return

    # calcular valor nuevo: valor_mes_anterior * (1 + pct/100)
    mon, yy = clave.split("-")
    idx = ABBR.index(mon)
    # mes anterior
    if idx == 0:
        prev_mon = ABBR[-1]
        prev_yy = f"{int(yy)-1:02d}"
    else:
        prev_mon = ABBR[idx-1]
        prev_yy = yy
    prev_key = f"{prev_mon}-{prev_yy}"

    if prev_key not in data:
        raise RuntimeError(f"Falta el valor de {prev_key} en {DATA}")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val * (1 + pct/100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__ == "__main__":
    main()
