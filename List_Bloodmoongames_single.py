import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import time
from datetime import datetime

BASE_URL = "https://bloodmoongames.cl/singles-magic-the-gathering/?product-page={}"

def preguntar_si_no(pregunta):
    while True:
        r = input(f"{pregunta} (S/N): ").strip().lower()
        if r in ("s","n"):
            return r == "s"
        print("❌ Opción no válida. Ingresa 'S' para sí o 'N' para no.")

def formatear_moneda(valor_int):
    """Convierte un número entero a formato $xx.xxx CLP"""
    if valor_int is None:
        return ""
    s = f"{valor_int:,}".replace(",", ".")
    return f"${s} CLP"

def limpiar_nombre(titulo):
    """
    Limpia el título:
    - Detecta si contiene 'foil' (case-insensitive)
    - Elimina paréntesis y su contenido
    - Devuelve nombre limpio y booleano foil
    """
    foil = bool(re.search(r"\bfoil\b", titulo, flags=re.I))
    s = re.sub(r"\s*\([^)]*\)", "", titulo)
    s = s.split("–")[0].split("-")[0].strip()
    return s, foil

def extraer_precio(span_price):
    """Toma solo el precio más bajo si hay rango"""
    precios = re.findall(r"\d[\d\.]*", span_price)
    if not precios:
        return None
    # Convertir a int, quitando puntos
    precios_int = [int(p.replace(".","")) for p in precios]
    return min(precios_int)

def obtener_productos_pagina(pagina):
    url = BASE_URL.format(pagina)
    resp = requests.get(url)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.find_all("li", class_="product")
    resultados = []

    for item in items:
        # Nombre y URL
        a_tag = item.find("a", class_="woocommerce-LoopProduct-link")
        if not a_tag:
            continue
        url_producto = a_tag.get("href")
        h2 = a_tag.find("h2", class_="woocommerce-loop-product__title")
        if not h2:
            continue
        titulo_raw = h2.get_text(strip=True)
        nombre_limpio, es_foil = limpiar_nombre(titulo_raw)

        # Imagen
        img_tag = a_tag.find("img")
        img_url = None
        if img_tag:
            img_url = img_tag.get("src")

        # Precio
        span_price = a_tag.find("span", class_="price")
        precio_int = None
        if span_price:
            precio_int = extraer_precio(span_price.get_text())

        precio_fmt = formatear_moneda(precio_int) if precio_int else ""

        resultados.append({
            "nombre_original": titulo_raw,
            "nombre": nombre_limpio,
            "foil": "Sí" if es_foil else "No",
            "precio": precio_fmt,
            "url": url_producto,
            "imagen": img_url
        })

    return resultados

def descargar_imagenes(productos, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    total = len(productos)
    descargadas = 0
    for i, p in enumerate(productos, start=1):
        url_img = p.get("imagen")
        if not url_img:
            continue
        nombre_archivo = re.sub(r"[^a-zA-Z0-9_-]", "_", p["nombre"])[:80] + ".jpg"
        ruta = os.path.join(carpeta, nombre_archivo)
        try:
            img_data = requests.get(url_img, timeout=10).content
            with open(ruta, "wb") as f:
                f.write(img_data)
            descargadas += 1
            print(f"📸 ({i}/{total}) Imagen guardada: {nombre_archivo}")
        except Exception as e:
            print(f"⚠️ Error descargando {p['nombre']}: {e}")
        time.sleep(0.2)
    print(f"✅ Imágenes descargadas: {descargadas}/{total}")

def main():
    if not preguntar_si_no("¿Deseas iniciar el scraping de BloodMoonGames?"):
        print("✋ Operación cancelada.")
        return

    pagina = 1
    todos = []

    while True:
        print(f"➡️ Procesando página {pagina}...")
        productos = obtener_productos_pagina(pagina)
        if not productos:
            print("✅ No hay más productos. Fin del scraping.")
            break
        todos.extend(productos)
        pagina += 1
        time.sleep(1)

    # Guardar CSV
    os.makedirs("Ficheros", exist_ok=True)
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_archivo = f"Ficheros/List_BloodMoon_{fecha}.csv"

    with open(nombre_archivo, "w", newline="", encoding="utf-8") as f:
        campos = ["nombre_original", "nombre", "foil", "precio", "url", "imagen"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todos)

    print(f"\n🟢 Scraping completado. Total de productos: {len(todos)}")
    print(f"📁 Archivo CSV guardado en: {nombre_archivo}\n")

    if preguntar_si_no("¿Deseas descargar las imágenes?"):
        descargar_imagenes(todos, "Ficheros/imagenes_bloodmoon")
    else:
        print("🚫 Descarga de imágenes cancelada.")

if __name__ == "__main__":
    main()
