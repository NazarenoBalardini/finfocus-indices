#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "activa.json"

def obtener_tna_pct():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tabla = soup.find("table", {"class": "tbl-azul"})
    for tr in tabla.select("tbody tr"):
        if "Cartera General" in tr.get_text():
            raw = tr.find_all("td")[2].get_text(strip=True)
            return float(raw.replace("%","").replace(",","."))
    raise RuntimeError("No encontré la T.N.A.")

def cargar_activa():
    if os.path.exists(ACTIVA_FILE):
        return json.load(open(ACTIVA_FILE, "r", encoding="utf-8"))
    return {}

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = cargar_activa()
    if data:
        ult_fecha = max(datetime.fromisoformat(d) for d in data.keys())
    else:
        ult_fecha = datetime.now().date() - timedelta(days=1)
    proxima = (ult_fecha + timedelta(days=1)).isoformat()
    tna = obtener_tna_pct()
    diaria = round(tna / 365, 6)
    data[proxima] = diaria
    guardar_activa(data)
    print(f"[{proxima}] T.N.A./365 = {diaria}% añadido")

if __name__ == "__main__":
    main()
