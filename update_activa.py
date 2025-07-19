#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, re, requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

URL         = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "indices/activa.json"   # ← ruta dentro de tu repo

def obtener_tna_pct():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if "T.N.A." in txt:
            m = re.search(r'([\d]+,[\d]+)%', txt)
            if m:
                # Ej: "36,52" → 36.52 (%)
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
    if not data:
        raise RuntimeError(f"No hay datos en {ACTIVA_FILE} para tomar el índice previo.")

    # 1) Determinar la última fecha y su valor
    fechas = sorted(data.keys())
    ult_fecha = datetime.fromisoformat(fechas[-1]).date()
    ult_valor = float(data[fechas[-1]])   # p.ej. 102.679

    # 2) Fecha siguiente a computar
    proxima = (ult_fecha + timedelta(days=1)).isoformat()  # "YYYY-MM-DD"

    # 3) Obtener la T.N.A. y calcular la tasa diaria decimal
    tna_pct      = obtener_tna_pct()           # e.g. 36.52
    tasa_diaria  = (tna_pct / 100) / 365       # 0.3652/365 → 0.001001... diario

    # 4) Calcular nuevo índice multiplicativo
    nuevo_valor = round(ult_valor * (1 + tasa_diaria), 6)

    # 5) Insertar y guardar
    data[proxima] = nuevo_valor
    guardar_activa(data)
    print(f"[{proxima}] {ult_valor} → {nuevo_valor} (+{tasa_diaria*100:.4f}% diario) guardado en {ACTIVA_FILE}")

if __name__ == "__main__":
    main()
