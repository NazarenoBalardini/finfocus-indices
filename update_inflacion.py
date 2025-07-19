#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import requests
import urllib3
from datetime import datetime
from dateutil.relativedelta import relativedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL  = "https://www.indec.gob.ar/indec/web/Nivel3-Tema-3-5"
DATA = "indices/inflacion.json"

MESES = ("enero|febrero|marzo|abril|mayo|junio|julio|"
         "agosto|septiembre|octubre|noviembre|diciembre")
ABBR  = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar():
    if os.path.exists(DATA):
        return json.load(open(DATA, encoding="utf-8"))
    return {}

def guardar(d):
    json.dump(d, open(DATA,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def obtener_indec():
    html = requests.get(URL, verify=False, timeout=10).text.replace("\n"," ")
    # Captura en orden: título, porcentaje, variación mensual, mes año
    pat = re.compile(
        rf"Precios\s+al\s+consumidor.*?([\d]+,[\d]+)%.*?Variación\s+mensual.*?({MESES})\s+(\d{{4}})",
        re.IGNORECASE|re.DOTALL
    )
    m = pat.search(html)
    if not m:
        raise RuntimeError("No pude extraer IPC (valor+mes) con el regex simplificado")
    pct_str, mes_full, año = m.group(1), m.group(2).lower(), m.group(3)
    mes_abbr = mes_full[:3]
    if mes_abbr not in ABBR:
        raise RuntimeError(f"Mes inesperado: {mes_full}")
    clave = f"{mes_abbr}-{año[-2:]}"
    pct   = float(pct_str.replace(",", "."))
    return clave, pct

def main():
    data  = cargar()
    clave, pct = obtener_indec()
    print(f"INDEC: {clave} → {pct}%")

    if clave in data:
        print(f"{clave!r} ya existe en inflacion.json, nada que hacer.")
        return

    # Mes anterior
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
        raise RuntimeError(f"Falta el valor de {prev_key} en inflacion.json")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val*(1 + pct/100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__=="__main__":
    main()
