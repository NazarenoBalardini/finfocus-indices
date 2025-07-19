#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime

# Desactivar warnings SSL (por si acaso)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL estática con todas las variables
CATALOGO_URL = (
    "https://www.bcra.gob.ar/Catalogo/Content/files/json/"
    "principales-variables-v3.json"
)
ACTIVO_FILE = "indices/pasiva.json"
ID_VARIABLE = "43"  # Tasa de uso de la Justicia

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
    Descarga el JSON de catálogo y devuelve el par (fecha_iso, valor)
    para la serie ID_VARIABLE.
    """
    resp = requests.get(CATALOGO_URL, timeout=10, verify=False)
    resp.raise_for_status()
    catalogo = resp.json()
    for item in catalogo:
        # 'c' es el código, 'fch' la fecha en 'DD/MM/YYYY', 'valor' el número
        if str(item.get("c")) == ID_VARIABLE:
            fch = item.get("fch")  # ej. '19/07/2025'
            valor = item.get("valor")
            # Parseo la fecha a ISO
            fecha_iso = datetime.strptime(fch, "%d/%m/%Y").date().isoformat()
            return fecha_iso, float(valor)
    raise RuntimeError(f"No encontré la variable {ID_VARIABLE} en catálogo.")

def main():
    data = cargar_pasiva()
    fecha, valor = obtener_ultimo()

    print(f"Último dato BCRA serie {ID_VARIABLE}: {fecha} → {valor}")

    if fecha in data:
        print(f"Ya registrado {fecha} en {ACTIVO_FILE}, nada que hacer.")
        return

    data[fecha] = valor
    guardar_pasiva(data)
    print(f"✅ Agregado {fecha}: {valor} a {ACTIVO_FILE}")

if __name__ == "__main__":
    main()
