#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

URL = "https://www.bna.com.ar/home/informacionalusuariofinanciero"
ACTIVA_FILE = "indices/activa.json"
DATE_FMT = "%d/%m/%Y"

def obtener_tna_y_vigencia():
    """
    Extrae del HTML:
      - el porcentaje T.N.A.
      - la fecha 'Vigente desde DD/MM/YYYY'
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

    # 2) Buscar "Vigente desde DD/MM/YYYY"
    texto = soup.get_text(" ", strip=True)
    m2 = re.search(r'Vigente desde\s+(\d{2}/\d{2}/\d{4})', texto)
    if m2:
        fecha_vigencia = datetime.strptime(m2.group(1), DATE_FMT).date()
    else:
        # Si no existe el texto, asumimos inicio hoy
        fecha_vigencia = datetime.utcnow().date()

    return tna_pct, fecha_vigencia

def cargar_activa():
    """
    Lee el archivo activa.json, limpia los trailing commas
    y devuelve el dict resultante.
    """
    with open(ACTIVA_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    # Eliminar comas antes de } o ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    return json.loads(text)

def guardar_activa(data):
    with open(ACTIVA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = cargar_activa()
    # Ordenar y obtener la última fecha guardada
    fechas = sorted(datetime.fromisoformat(d).date() for d in data.keys())
    ultimo_guardado = fechas[-1]

    tna_pct, fecha_vigencia = obtener_tna_y_vigencia()
    tasa_diaria = (tna_pct / 100) / 365

    # Determinar desde cuándo reescribir:
    if fecha_vigencia <= ultimo_guardado:
        inicio = fecha_vigencia
    else:
        inicio = ultimo_guardado + timedelta(days=1)

    hoy = datetime.utcnow().date()
    if inicio > hoy:
        print("No hay nuevos días para procesar.")
        return

    # Valor del día anterior a 'inicio'
    prev_date = inicio - timedelta(days=1)
    prev_val = float(data[prev_date.isoformat()])

    # Eliminar fechas >= inicio para reescritura limpia
    for d in list(data.keys()):
        if datetime.fromisoformat(d).date() >= inicio:
            del data[d]

    # Generar nuevos valores desde 'inicio' hasta hoy
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
