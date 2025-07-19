#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL de BCRA para “Principales Variables”
URL       = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
DATA      = "indices/inflacion.json"
ABBR      = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
TARGET_TXT = "Inflación mensual"  # texto exacto a buscar en la primera celda

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
    Scrapea la tabla de Principales Variables del BCRA,
    busca la fila donde la primera celda contiene TARGET_TXT,
    extrae la fecha (DD/MM/YYYY) y el porcentaje (X,X),
    y retorna (clave, pct) donde clave es 'jun-25'.
    """
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("No encontré la tabla de Principales Variables.")
    for tr in table.select("tbody tr"):
        cols = [td.get_text(strip=True) for td in tr.select("td")]
        if len(cols) < 3:
            continue
        if TARGET_TXT.lower() in cols[0].lower():
            # cols[1] = '30/06/2025', cols[2] = '1,6'
            fecha_str = cols[1]
            pct_str   = cols[2]
            # parsear fecha
            try:
                dt = datetime.strptime(fecha_str, "%d/%m/%Y")
            except ValueError:
                raise RuntimeError(f"Formato inesperado de fecha: {fecha_str}")
            clave = f"{ABBR[dt.month-1]}-{str(dt.year)[2:]}"
            # parsear porcentaje
            pct = float(pct_str.replace(".", "").replace(",", "."))
            return clave, pct

    raise RuntimeError(f"No encontré ninguna fila con '{TARGET_TXT}'")

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
        raise RuntimeError(f"Falta el valor de {prev_key} en {DATA}")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val * (1 + pct/100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__ == "__main__":
    main()
