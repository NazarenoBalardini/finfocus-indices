#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "activa.json"

def obtener_tna_pct():
    """Devuelve la T.N.A. (30 días) como float (p.ej. 36.52)."""
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Busca en todos los <li> aquel que mencione "T.N.A."
    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if "T.N.A." in txt:
            # Extrae el número antes del "%" (maneja coma decimal)
            m = re.search(r'([\d]+,[\d]+)%', txt)
            if m:
                # "36,52" → "36.52"
                return float(m.group(1).replace(",", "."))
    raise RuntimeError("No encontré la T.N.A. en el HTML del BNA.")

def cargar_activa():
    if os.path.exists(ACTIVA_FILE):
        with open(ACTIVA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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
    print(f"[{proxima}] T.N.A./365 = {diaria}% añadido a {ACTIVA_FILE}")

if __name__ == "__main__":
    main()
