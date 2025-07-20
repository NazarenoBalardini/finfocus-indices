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
DATE_FMT    = "%d/%m/%Y"  # para parsear “vigente desde”

def obtener_tna_y_vigencia():
    """
    Extrae del HTML:
      - el porcentaje T.N.A.
      - la fecha 'Vigente desde dd/mm/yyyy'
    """
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Buscar T.N.A.
    tna_pct = None
    for li in soup.find_all("li"):
        txt = li.get_text(strip=True)
        if "T.N.A." in txt:
            m = re.search(r'([\d]+,[\d]+)%', txt)
            if m:
                tna_pct = float(m.group(1).replace(",", "."))
                break
    if tna_pct is None:
        raise RuntimeError("No encontré la T.N.A. en el HTML.")

    # 2) Buscar “Vigente desde DD/MM/YYYY”
    fecha_vig = None
    texto = soup.get_text(" ", strip=True)
    m2 = re.search(r'Vigente desde\s+(\d{2}/\d{2}/\d{4})', texto)
    if m2:
        fecha_vig = datetime.strptime(m2.group(1), DATE_FMT).date()
    else:
        # Si no existe el texto, asumimos inicio hoy
        fecha_vig = datetime.utcnow().date()

    return tna_pct, fecha_vig

def cargar_activa():
    with open(ACTIVA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = cargar_activa()
    # convertir claves a fechas
    fechas = sorted(datetime.fromisoformat(d).date() for d in data.keys())
    ultimo_guardado = fechas[-1]
    
    tna_pct, fecha_vigencia = obtener_tna_y_vigencia()
    tasa_diaria = (tna_pct / 100) / 365

    # determinamos desde cuándo reescribir:
    # si la vigencia es anterior o igual al último guardado, 
    #   arrancamos desde fecha_vigencia para reescribir ese tramo.
    # si es posterior (cambio normal futuro), 
    #   arrancamos un día después del último guardado.
    if fecha_vigencia <= ultimo_guardado:
        inicio = fecha_vigencia
    else:
        inicio = ultimo_guardado + timedelta(days=1)

    hoy = datetime.utcnow().date()
    if inicio > hoy:
        print("No hay nuevos días para procesar.")
        return

    # tomo el valor del día anterior a 'inicio'
    prev_date = inicio - timedelta(days=1)
    prev_val = float(data[prev_date.isoformat()])

    # elimino cualquier fecha >= inicio (para reescritura limpia)
    for d in list(data.keys()):
        if datetime.fromisoformat(d).date() >= inicio:
            del data[d]

    # genero valores día a día desde 'inicio' hasta hoy
    date = inicio
    while date <= hoy:
        nueva = round(prev_val * (1 + tasa_diaria), 6)
        data[date.isoformat()] = nueva
        prev_val = nueva
        date += timedelta(days=1)

    guardar_activa(data)
    print(f"Actualizado desde {inicio.isoformat()} hasta {hoy.isoformat()}.")

if __name__ == "__main__":
    main()
