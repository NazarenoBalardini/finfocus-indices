#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime, timedelta

from bcraapi import estadisticas  # <— el wrapper oficial

SERIE_ID    = 43
ACTIVO_FILE = "indices/pasiva.json"

def cargar_pasiva():
    if os.path.exists(ACTIVO_FILE):
        with open(ACTIVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_pasiva(data):
    with open(ACTIVO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data   = cargar_pasiva()
    fechas = sorted(data.keys())

    # Rango a pedir: desde el día siguiente a la última fecha guardada
    if fechas:
        ultima = datetime.fromisoformat(fechas[-1]).date()
        desde  = (ultima + timedelta(days=1)).isoformat()
    else:
        # Si está vacío, traemos los últimos 30 días
        desde  = (datetime.now().date() - timedelta(days=30)).isoformat()
    hasta = datetime.now().date().isoformat()

    print(f"🗂️ Cargando serie {SERIE_ID} desde {desde} hasta {hasta}…")
    # Devuelve un DataFrame con columnas ['fecha','valor']
    df = estadisticas.monetarias(id_variable=SERIE_ID, desde=desde, hasta=hasta)

    añadidos = 0
    for _, row in df.iterrows():
        # row.fecha puede ser datetime.date o str; normalizamos a 'YYYY-MM-DD'
        d = row.fecha if isinstance(row.fecha, str) else row.fecha.date().isoformat()
        v = float(row.valor)
        if d not in data:
            data[d] = v
            añadidos += 1

    if añadidos:
        guardar_pasiva(data)
        print(f"✅ Añadidas {añadidos} observaciones a {ACTIVO_FILE}.")
    else:
        print("⚠️ No hubo nuevas observaciones para agregar.")

if __name__ == "__main__":
    main()
