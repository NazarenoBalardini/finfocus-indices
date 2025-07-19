#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

# Desactivar warnings SSL (certificados autofirmados)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL         = "https://www.argentina.gob.ar/trabajo/seguridadsocial/ripte"
ACTIVO_FILE = "indices/ripte.json"
# Mapeo meses en español
MONTHS = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,
    "mayo":5,"junio":6,"julio":7,"agosto":8,
    "septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
}

def cargar_ripte():
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_ripte(data):
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_ripte():
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("No encontré la tabla de RIPTE.")

    body = table.find("tbody")
    row  = body.find("tr")
    cols = [td.get_text(strip=True) for td in row.find_all("td")]

    # cols[0] = 'Mayo/2025', cols[-1] = '163.299,84'
    mes_str, val_str = cols[0], cols[-1]
    nombre, año = mes_str.split("/")
    nombre = nombre.lower()
    mes_num = MONTHS[nombre]

    # clave 'may-25'
    clave = f"{nombre[:3]}-{año[-2:]}"

    # limpiamos valor y convertimos
    limpio = val_str.replace(".", "").replace(",", ".")
    valor  = round(float(limpio), 2)

    return clave, valor

def main():
    data  = cargar_ripte()
    clave, valor = obtener_ripte()
    print(f"Último RIPTE: {clave} → {valor}")

    if clave in data:
        print(f"Ya existe '{clave}', nada que hacer.")
        return

    data[clave] = valor
    guardar_ripte(data)
    print(f"✅ Agregado '{clave}': {valor} a {ACTIVO_FILE}")

if __name__ == "__main__":
    main()
