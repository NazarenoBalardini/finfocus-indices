#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL         = "https://www.argentina.gob.ar/trabajo/consejodelsalario"
SMVM_FILE   = "indices/smvm.json"

def cargar_smvm():
    with open(SMVM_FILE, encoding="utf-8") as f:
        return json.load(f)

def guardar_smvm(data):
    with open(SMVM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_smvm():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Encuentra el bloque que contenga exactamente ese texto
    tarjeta = soup.find(lambda tag:
        tag.name in ("div","section") and
        "Salario Mínimo Vital y Móvil" in tag.get_text()
    )
    if not tarjeta:
        raise RuntimeError("No encontré el bloque de SMVM en la página")

    texto = tarjeta.get_text(separator=" ", strip=True)
    # 2) Regex para extraer valor y mes/año
    m = re.search(r"\$\s*([\d\.\,]+).*\((\w+)\s+(\d{4})\)", texto)
    if not m:
        raise RuntimeError("No pude extraer valor + mes/año de SMVM")
    valor_str, mes_txt, anio = m.groups()
    # convertir "317.800" a float
    valor = float(valor_str.replace(".", "").replace(",", "."))
    # normalizar mes abreviado en minúscula
    mes = mes_txt[:3].lower()
    clave = f"{mes}-{anio[-2:]}"
    return clave, valor

def main():
    data = cargar_smvm()
    clave, valor = obtener_smvm()
    if clave in data:
        print(f"'{clave}' ya existe en {SMVM_FILE}, nada que hacer.")
    else:
        data[clave] = valor
        guardar_smvm(data)
        print(f"Añadido '{clave}': {valor} a {SMVM_FILE}")

if __name__ == "__main__":
    main()
