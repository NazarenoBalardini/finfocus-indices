import json
import re
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# 1) Página que lista todas las fichas de resolución
INDEX_URL = "https://trivia.consejo.org.ar/listado/pisos_minimos_en_las_prestaciones_por_incapacidad_permanente"

# 2) Mapeo de texto de columna → sufijo de archivo
ART_MAP = {
    "Art. 11A":    "11A",
    "Art. 11B":    "11B",
    "Art. 11C":    "11C",
    "Art. 14.2 A": "14A",
    "Art. 14.2 B": "14B",
    "Art. 15.2":   "15",
    "Art. 3":      "3",        # si en la tabla figura solo "Art. 3" para el adicional
}

async def fetch_latest_resolution_url(page):
    # 1) vamos a la página de listado
    await page.goto(INDEX_URL, wait_until="networkidle")

    # 2) espero a que aparezca la tabla de fichas
    await page.wait_for_selector("table.listado-fichas tbody tr", timeout=60000)

    # 3) clickeo el link de la última fila
    ultima_fila = page.locator("table.listado-fichas tbody tr").last
    await ultima_fila.locator("a[href*='/ficha/']").click()

    # 4) espero a que cargue la ficha concreta
    await page.wait_for_selector("article.resolucion, .ficha-detalle", timeout=60000)

    return page.url

async def fetch_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1) obtenemos dinámicamente la URL de la última resolución
        latest_url = await fetch_latest_resolution_url(page)

        # 2) visitamos esa ficha
        await page.goto(latest_url)
        # desplegamos la sección "Pisos mínimos"
        await page.click("text=Pisos mínimos")
        await page.wait_for_selector("table", timeout=60000)

        html = await page.content()
        await browser.close()

    # 3) parseo con BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table")
    resultados = {art: [] for art in ART_MAP.values()}

    for row in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        art_txt, desde, hasta, monto_txt = cols
        key = ART_MAP.get(art_txt)
        if not key:
            continue

        d1 = datetime.strptime(desde, "%d/%m/%Y").date().isoformat()
        d2 = datetime.strptime(hasta, "%d/%m/%Y").date().isoformat()
        monto = float(re.sub(r"[^\d]", "", monto_txt))

        resultados[key].append({
            "res": art_txt.replace("Art.", "Res.").strip(),
            "desde": d1,
            "hasta": d2,
            "monto": monto
        })

    # 4) reescribimos cada JSON
    for art, items in resultados.items():
        filename = f"{art}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(fetch_data())
