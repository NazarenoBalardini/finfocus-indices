#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL     = "https://www.indec.gob.ar/indec/web/Nivel3-Tema-3-5"
DATA    = "indices/inflacion.json"
ABBR    = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def cargar():
    if os.path.exists(DATA):
        return json.load(open(DATA, encoding="utf-8"))
    return {}

def guardar(d):
    json.dump(d, open(DATA,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def obtener_indec():
    """
    Scrapea el card de 'Precios al consumidor' y devuelve (clave, pct).
    """
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Localizar el título "Precios al consumidor"
    title_node = soup.find(lambda tag: tag.name in ("h2","h3") 
                          and "Precios al consumidor" in tag.get_text())
    if not title_node:
        raise RuntimeError("No encontré 'Precios al consumidor' en la página")

    # 2) Ir al contenedor del card (subimos dos niveles asumiendo estructura)
    card = title_node.find_parent().find_parent()

    # 3) Dentro del card, buscar el porcentaje (%)
    pct_text = card.find(text=lambda t: "%" in t)
    pct_str  = pct_text.strip().replace("%","")  # e.g. "1,6"

    # 4) Y también dentro del card, buscar la fecha "Junio 2025"
    date_text = card.find(text=lambda t: any(m in t for m in ("2025","2024")))
    # suele estar justo debajo o en el mismo contenedor
    parts = date_text.strip().split()
    # buscamos mes y año
    mes_full = parts[0].lower()   # "junio"
    año      = parts[1]           # "2025"

    mes_abbr = mes_full[:3]
    if mes_abbr not in ABBR:
        raise RuntimeError(f"Mes inesperado: {mes_full}")

    clave = f"{mes_abbr}-{año[-2:]}"
    pct   = float(pct_str.replace(",", "."))

    return clave, pct

def main():
    data = cargar()
    clave, pct = obtener_indec()
    print(f"INDEC: {clave} → {pct}%")

    if clave in data:
        print(f"{clave!r} ya existe en inflacion.json, nada que hacer.")
        return

    # mes anterior para calcular
    ABBR_LIST = ABBR
    mon, yy = clave.split("-")
    idx      = ABBR_LIST.index(mon)
    if idx == 0:
        prev_mon = ABBR_LIST[-1]
        prev_yy  = f"{int(yy)-1:02d}"
    else:
        prev_mon = ABBR_LIST[idx-1]
        prev_yy  = yy
    prev_key = f"{prev_mon}-{prev_yy}"

    if prev_key not in data:
        raise RuntimeError(f"Falta el valor de {prev_key} en inflacion.json")

    prev_val = float(data[prev_key])
    new_val  = round(prev_val * (1 + pct/100), 4)

    data[clave] = new_val
    guardar(data)
    print(f"✅ Agregado {clave}: {new_val} (previo {prev_key}={prev_val})")

if __name__ == "__main__":
    main()
