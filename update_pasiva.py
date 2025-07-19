#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL          = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
ACTIVO_FILE  = "indices/pasiva.json"
BUSCAR_TEXTO = "uso de la Justicia"  # parte del texto que identifica la fila

def cargar_pasiva():
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_pasiva(data):
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_ultimo():
    """
    Scrapea la tabla de Principales Variables y devuelve
    (fecha_iso, valor) de la fila que contiene BUSCAR_TEXTO.
    """
    # note el verify=False para evitar errores SSL
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("No encontré ninguna <table> en la página.")

    for row in table.select("tr"):
        cols = [td.get_text(strip=True) for td in row.select("td")]
        if len(cols) >= 3 and BUSCAR_TEXTO.lower() in cols[0].lower():
            fch, val = cols[1], cols[2]
            # Normalizar fecha: soporta 'DD/MM/YYYY' o 'DD-MM-YYYY'
            fch_norm = fch.replace("-", "/")
            try:
                fecha_iso = datetime.strptime(fch_norm, "%d/%m/%Y").date().isoformat()
            except ValueError:
                raise RuntimeError(f"Formato de fecha inesperado: {fch}")
            # Convertir valor: quitar separador de miles y coma decimal
            val_n = val.replace(".", "").replace(",", ".")
            try:
                v = float(val_n)
            except ValueError:
                raise RuntimeError(f"Valor numérico inválido: {val}")
            return fecha_iso, v

    raise RuntimeError(f"No encontré ninguna fila con '{BUSCAR_TEXTO}'")

def main():
    data = cargar_pasiva()
    fecha, valor = obtener_ultimo()
    print(f"Último dato scraped: {fecha} → {valor}")

    if fecha in data:
        print(f"Ya existe {fecha} en {ACTIVO_FILE}, nada que hacer.")
        return

    data[fecha] = valor
    guardar_pasiva(data)
    print(f"✅ Agregado {fecha}: {valor} a {ACTIVO_FILE}")

if __name__ == "__main__":
    main()
