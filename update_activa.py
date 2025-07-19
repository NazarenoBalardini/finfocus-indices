#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

URL         = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "indices/activa.json"

def obtener_tna_pct():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if "T.N.A." in txt:
            m = re.search(r'([\d]+,[\d]+)%', txt)
            if m:
                return float(m.group(1).replace(",", "."))
    raise RuntimeError("No encontré la T.N.A. en el HTML.")

def cargar_activa():
    print(f"DEBUG: ¿Existe {ACTIVA_FILE}? → {os.path.exists(ACTIVA_FILE)}")
    data = json.load(open(ACTIVA_FILE, "r", encoding="utf-8"))
    print("DEBUG: Contenido actual de activa.json:")
    print(json.dumps(data, indent=2))
    return data

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("DEBUG: Se ha escrito el JSON con las fechas:")
    print(json.dumps(data, indent=2))

def main():
    data = cargar_activa()

    fechas = sorted(data.keys())
    print("DEBUG: Fechas ordenadas:", fechas)

    ult_fecha = datetime.fromisoformat(fechas[-1]).date()
    ult_valor = float(data[fechas[-1]])
    print(f"DEBUG: Última fecha → {ult_fecha}, valor → {ult_valor}")

    sig_fecha = (ult_fecha + timedelta(days=1)).isoformat()
    print("DEBUG: Fecha siguiente a añadir:", sig_fecha)

    tna_pct     = obtener_tna_pct()
    tasa_diaria = (tna_pct/100) / 365
    print(f"DEBUG: TNA_pct={tna_pct}%, tasa_diaria={tasa_diaria}")

    nuevo_valor = round(ult_valor * (1 + tasa_diaria), 6)
    print("DEBUG: Nuevo valor calculado:", nuevo_valor)

    data[sig_fecha] = nuevo_valor
    guardar_activa(data)

if __name__ == "__main__":
    main()
