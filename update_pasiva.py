#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests
import urllib3
from datetime import datetime

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CATALOGO_URL = (
    "https://www.bcra.gob.ar/Catalogo/Content/files/json/"
    "principales-variables-v3.json"
)
ACTIVO_FILE = "indices/pasiva.json"
ID_VARIABLE = "43"  # Tasa de uso de la Justicia

def cargar_pasiva():
    """Carga el JSON existente o devuelve {} si no existe."""
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_pasiva(data):
    """Guarda el dict en pasiva.json con indentado."""
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_ultimo():
    """
    Descarga el JSON de catálogo y devuelve (fecha_iso, valor) para ID_VARIABLE.
    """
    resp = requests.get(CATALOGO_URL, timeout=10, verify=False)
    resp.raise_for_status()
    catalogo = resp.json()  # debería ser una lista de dicts

    for item in catalogo:
        # Cada item es dict con claves 'c', 'fch', 'valor', etc.
        if str(item.get("c")) == ID_VARIABLE:
            fch = item.get("fch")    # formato 'DD/MM/YYYY'
            valor = item.get("valor")
            # Parsear fecha a ISO
            try:
                fecha_iso = datetime.strptime(fch, "%d/%m/%Y").date().isoformat()
            except Exception:
                raise RuntimeError(f"Formato de fecha inesperado: {fch}")
            # Convertir valor a float
            try:
                v = float(valor)
            except Exception:
                raise RuntimeError(f"Valor numérico inválido: {valor}")
            return fecha_iso, v

    raise RuntimeError(f"Variable {ID_VARIABLE} no encontrada en catálogo")

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
