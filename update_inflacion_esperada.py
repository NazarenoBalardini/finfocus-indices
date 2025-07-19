#!/usr/bin/env python3
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# --- CONFIGURACIÓN ---
BCRA_URL = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
LOCAL_JSON = "indices/inflacion_esperada.json"

# Mapeo mes → abreviatura en español
SPAN_ABBR = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr",
    5: "may", 6: "jun", 7: "jul", 8: "ago",
    9: "sep", 10: "oct", 11: "nov", 12: "dic"
}

def fetch_rem_median():
    r = requests.get(BCRA_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Busca en todas las filas de tablas la etiqueta exacta
    for tr in soup.select("table tr"):
        td = tr.find("td")
        if not td: continue
        texto = td.get_text(strip=True)
        if "REM próximos 12 meses" in texto and "MEDIANA" in texto:
            cols = [c.get_text(strip=True) for c in tr.find_all("td")]
            # Ejemplo de cols: ["Inflación esperada - REM próximos 12 meses - MEDIANA (variación en % i.a)", "30/06/2025", "20,8"]
            fecha_str = cols[1]   # p.ej. "30/06/2025"
            valor_str = cols[2]   # p.ej. "20,8"
            return fecha_str, float(valor_str.replace(",", "."))
    raise RuntimeError("No encontré la fila REM MEDIANA en la tabla del BCRA")

def to_key(fecha_str):
    dt = datetime.strptime(fecha_str, "%d/%m/%Y")
    mes = SPAN_ABBR[dt.month]
    yy = dt.strftime("%y")
    return f"{mes}-{yy}"

def main():
    fecha, valor = fetch_rem_median()
    clave = to_key(fecha)

    # Carga JSON existente
    with open(LOCAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Si fuera lista de objetos, adaptá aquí; asumo un dict:
    data[clave] = valor

    # Guarda
    with open(LOCAL_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Actualizado {clave}: {valor}% en {LOCAL_JSON}")

if __name__ == "__main__":
    main()
