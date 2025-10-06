import requests
from bs4 import BeautifulSoup
import json
import csv
import time

BASE_URL = "https://www.oasisgames.cl/collections/mtg-singles-instock?page={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def detectar_foil(nombre):
    """Devuelve 'Sí' si contiene Foil y no 'Non-Foil'."""
    nombre_lower = nombre.lower()
    if "foil" in nombre_lower and "non-foil" not in nombre_lower:
        return "Sí"
    return "No"

def limpiar_nombre(nombre):
    """Elimina paréntesis y detalles adicionales."""
    if "(" in nombre:
        nombre = nombre.split("(")[0].strip()
    return nombre.strip()

def obtener_cartas_de_pagina(pagina):
    """Obtiene todas las cartas de una página, con su precio más bajo."""
    url = BASE_URL.format(pagina)
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"❌ Error {resp.status_code} al acceder a {url}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    productos = soup.select("div.grid-view-item")

    if not productos:
        return []

    cartas = []
    for prod in productos:
        nombre_tag = prod.select_one(".grid-view-item__title")
        if not nombre_tag:
            continue

        nombre_original = nombre_tag.get_text(strip=True)
        enlace_tag = prod.select_one("a.full-unstyled-link")
        enlace = ""
        if enlace_tag:
            enlace = enlace_tag.get("href", "")
            if enlace.startswith("/"):
                enlace = "https://www.oasisgames.cl" + enlace

        # Extraer precios desde el JSON del atributo "variants"
        price_div = prod.select_one("div.product-price")
        min_precio = None
        if price_div and price_div.has_attr("variants"):
            try:
                data = json.loads(price_div["variants"])
                precios = [int(v["price"]) / 100 for v in data.values()]
                if precios:
                    min_precio = min(precios)
            except Exception:
                pass

        if not min_precio:
            continue

        foil = detectar_foil(nombre_original)
        nombre = limpiar_nombre(nombre_original)

        cartas.append({
            "nombre_original": nombre_original,
            "nombre": nombre,
            "foil": foil,
            "precio": f"${min_precio:,.0f}".replace(",", "."),
            "url": enlace
        })

    return cartas

def scrapear_todas_las_paginas(archivo_salida="oasis_minimo.csv"):
    """Recorre todas las páginas y guarda solo el precio más bajo por carta."""
    todas = []
    pagina = 1

    while True:
        print(f"📄 Procesando página {pagina}...")
        cartas = obtener_cartas_de_pagina(pagina)
        if not cartas:
            print("✅ No hay más productos. Fin del scraping.")
            break

        todas.extend(cartas)
        print(f"   ➕ {len(cartas)} cartas agregadas (Total: {len(todas)})")
        pagina += 1
        time.sleep(1)

    if not todas:
        print("❌ No se encontraron cartas para guardar.")
        return

    with open(archivo_salida, "w", newline="", encoding="utf-8") as f:
        campos = ["nombre_original", "nombre", "foil", "precio", "url"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todas)

    print(f"\n💾 {len(todas)} cartas guardadas en {archivo_salida}")

if __name__ == "__main__":
    scrapear_todas_las_paginas()
