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
    """Descarga la página y extrae la T.N.A. (30d) como float (p.ej. 36.52)."""
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
    with open(ACTIVA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = cargar_activa()
    # 1) Última fecha y valor
    fechas = sorted(data.keys())
    ult_fecha = datetime.fromisoformat(fechas[-1]).date()
    ult_valor = float(data[fechas[-1]])

    # 2) Fecha siguiente
    sig_fecha = (ult_fecha + timedelta(days=1)).isoformat()

    # 3) Obtener TNA y calcular tasa diaria decimal
    tna_pct     = obtener_tna_pct()    # 36.52
    tasa_diaria = (tna_pct/100) / 365   # ~0.001001

    # 4) Calcular nuevo valor
    nuevo_valor = round(ult_valor * (1 + tasa_diaria), 6)

    # 5) Insertar y guardar
    data[sig_fecha] = nuevo_valor
    guardar_activa(data)

    print(f"[{sig_fecha}] {ult_valor} → {nuevo_valor} "
          f"(+{tasa_diaria*100:.4f}% diario) en {ACTIVA_FILE}")

if __name__ == "__main__":
    main()
