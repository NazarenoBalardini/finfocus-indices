def obtener_indec():
    """
    Usa regex sobre el HTML para extraer:
      - pct: (\d+,\d+)% justo antes de 'Variación mensual'
      - mes/año aparecen justo después de esa frase.
    Devuelve (clave, pct).
    """
    resp = requests.get(URL, timeout=10, verify=False)
    resp.raise_for_status()
    txt = resp.text.replace("\n", " ")

    # 1) Capturamos "% <Variación mensual>" y luego "Mes Año"
    m = re.search(
        r"(\d+,\d+)%\s*<[^>]*>Variación mensual</",
        txt, re.IGNORECASE
    )
    if not m:
        raise RuntimeError("No pude extraer el porcentaje con regex")
    pct_str = m.group(1)

    # 2) Tras esa aparición, buscamos el Mes Año: p.ej. "Junio 2025"
    #    Limitamos el lookahead para no pasar de 200 caracteres.
    tail = txt[m.end():m.end()+200]
    m2 = re.search(r"([A-Za-z]+)\s+(\d{4})", tail)
    if not m2:
        raise RuntimeError("No pude extraer mes/año tras el %")
    mes_full, año = m2.group(1).lower(), m2.group(2)

    mes_abbr = mes_full[:3]
    if mes_abbr not in ABBR:
        raise RuntimeError(f"Mes inesperado: {mes_full}")

    clave = f"{mes_abbr}-{año[-2:]}"
    pct = float(pct_str.replace(",", "."))

    return clave, pct
