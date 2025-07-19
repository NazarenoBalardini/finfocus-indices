#!/usr/bin/env python3
# coding: utf-8

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import urllib3

# Desactivar warnings de SSL no verificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    # Solicitud sin verificación SSL
    r = requests.get(BCRA_URL, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for tr in soup.select("table tr"):
        td = tr.find("td")
        if not td:
            continue
        texto = td.get_text(strip=True)
        if "REM próximos 12 meses" in texto and "MEDIANA" in texto:
            cols = [c.get_text(strip=True) for c in tr.find_all("td")]
            # cols = ["Título", "dd/mm/aaaa", "valor"]
            fecha_str = cols[1]
            valor_str = cols[2]
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

    # Carga el JSON existente (un dict mes-aa → valor)
    with open(LOCAL_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Actualiza o añade la clave
    data[clave] = valor

    # Guarda con indentación legible
    with open(LOCAL_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Actualizado {clave}: {valor}% en {LOCAL_JSON}")

if __name__ == "__main__":
    main()
