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
    Scrapea INDEC y devuelve (clave, pct) donde:
      - clave: 'jun-25'
      - pct: 1.6 (float)
    """
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # buscamos el bloque de "Precios al consumidor"
    # suele haber un <h2> o <h3> con ese texto y vecino un <p> con "junio 2025: 1,6%"
    nodo = soup.find(lambda tag: tag.name in ("h2","h3") 
                     and "Precios al consumidor" in tag.get_text())
    if not nodo:
        raise RuntimeError("No encontré el título 'Precios al consumidor'")

    # el siguiente <p> contiene el mes y la variación
    p = nodo.find_next_sibling("p")
    texto = p.get_text(strip=True)  # ej. "junio 2025: 1,6%"

    # extraer mes y año
    mes_str, resto = texto.split(":",1)
    mes_str = mes_str.strip().lower()   # "junio 2025"
    pct_str = resto.strip().replace("%","")  # "1,6"

    # parsear mes/año
    nombre, año = mes_str.split()
    m = ABBR.index(nombre[:3]) + 1
    yy = año[-2:]
    clave = f"{nombre[:3]}-{yy}"

    # parsear porcentaje a float
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
    # extraemos el mes anterior:
    # si clave="jun-25", mes_ant = may-25
    mon, yy = clave.split("-")
    idx = ABBR.index(mon)
    # obtenemos abreviatura mes anterior
    if idx == 0:
        # de ene-XX a dic-(XX-1)
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
