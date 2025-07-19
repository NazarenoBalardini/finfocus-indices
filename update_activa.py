#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "indices/activa.json"

def obtener_soup():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def obtener_tna_pct():
    """Devuelve T.N.A. (30 días) como float, p.ej. 36.52"""
    soup = obtener_soup()
    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if "T.N.A." in txt:
            m = re.search(r'([\d]+,[\d]+)%', txt)
            if m:
                return float(m.group(1).replace(",", "."))
    raise RuntimeError("No encontré la T.N.A. en el HTML.")

def obtener_fecha_vigencia():
    """Extrae la fecha 'vigente desde el DD/MM/YYYY' de la cabecera."""
    soup = obtener_soup()
    header = soup.find(text=re.compile(r'vigente desde el', re.IGNORECASE))
    if not header:
        raise RuntimeError("No encontré la línea de 'vigente desde' en la página.")
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', header)
    if not m:
        raise RuntimeError("No pude parsear la fecha de vigencia.")
    d, mo, y = m.groups()
    fecha = datetime(year=int(y), month=int(mo), day=int(d)).date()
    return fecha.isoformat()  # "YYYY-MM-DD"

def cargar_activa():
    with open(ACTIVA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = cargar_activa()

    fecha = obtener_fecha_vigencia()      # e.g. "2025-07-18"
    if fecha in data:
        print(f"Ya existe entrada para {fecha}, nada que hacer.")
        return

    # buscamos la última fecha anterior en el JSON
    fechas = sorted(data.keys())
    # todas las fechas < fecha, y tomamos la mayor
    prevs = [f for f in fechas if f < fecha]
    if not prevs:
        raise RuntimeError("No hay fecha anterior en el JSON para tomar índice.")
    prev_date = prevs[-1]
    prev_val  = float(data[prev_date])    # e.g. 102.679

    tna_pct    = obtener_tna_pct()        # e.g. 36.52
    # calcula el interés para 30 días
    tasa_periodica = (tna_pct/100) * 30/365  
    nuevo_valor    = round(prev_val * (1 + tasa_periodica), 6)

    data[fecha] = nuevo_valor
    guardar_activa(data)

    print(f"[{fecha}] {prev_date}→{fecha}: {prev_val} → {nuevo_valor} "
          f"(+{tasa_periodica*100:.4f}% en 30 días) guardado en {ACTIVA_FILE}")

if __name__ == "__main__":
    main()
