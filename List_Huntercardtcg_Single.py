import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import os
import re

BASE_START = "https://www.huntercardtcg.com/categoria-producto/mtg/mtg-singles/page/{}/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; scraping-script/1.0; +https://example.com)"
}

def preguntar_si_no(pregunta):
    """Pide confirmación S/N hasta recibir una respuesta válida"""
    while True:
        try:
            r = input(f"{pregunta} (S/N): ").strip().lower()
        except EOFError:
            return False
        if r in ("s", "n"):
            return r == "s"
        print("❌ Opción no válida. Por favor, ingresa 'S' para sí o 'N' para no.")

def formatear_moneda_clp(valor_int):
    """Convierte un número entero a formato $xx.xxx CLP"""
    if valor_int is None:
        return ""
    return f"${valor_int:,}".replace(",", ".")

def limpiar_nombre(titulo):
    """
    Limpia el título:
    - Detecta si contiene 'foil' (case-insensitive)
    - Elimina paréntesis y su contenido
    - Toma la parte antes de '–' o '-' si existe
    - Devuelve nombre limpio y booleano foil
    """
    if not titulo:
        return "", False

    # Detectar foil en cualquier parte
    foil = bool(re.search(r"\bfoil\b", titulo, flags=re.I))

    # Eliminar contenido entre paréntesis
    s = re.sub(r"\s*\([^)]*\)", "", titulo)

    # Si hay guion largo '–' o guion normal '-', separar y tomar la primera parte
    s = re.split(r"\s+[–-]\s+", s)[0]

    # Limpiar espacios sobrantes y caracteres raros al inicio/final
    s = s.strip()

    # Opcional: eliminar etiquetas extra como #75, Common, Inglés si quedaron con comas o guiones
    # Tomamos sólo la primera parte por si aún quedan ' – ' u otros separadores
    return s, foil

def extraer_precio(texto_precio):
    if not texto_precio:
        return None

    # Extraer todos los números (ignora puntos y comas)
    precios = re.findall(r"\d[\d\.]*", texto_precio)
    if not precios:
        return None

    precios_int = []
    for p in precios:
        try:
            precios_int.append(int(p.replace(".", "")))
        except ValueError:
            continue

    if not precios_int:
        return None

    # Tomar el precio más bajo en caso de rango
    return min(precios_int)

def obtener_productos_por_pagina(numero_pagina):
    url = BASE_START.format(numero_pagina)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        # Si página no existe o problema, devolvemos lista vacía
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    contenedores = soup.find_all("div", class_="thunk-product")
    resultados = []

    for cont in contenedores:
        # Elemento link con título
        a_tag = cont.find("a", class_="woocommerce-LoopProduct-link")
        titulo_tag = cont.find("h2", class_="woocommerce-loop-product__title")
        if not a_tag or not titulo_tag:
            continue

        titulo_raw = titulo_tag.get_text(strip=True)
        url_producto = a_tag.get("href")
        if url_producto and url_producto.startswith("/"):
            url_producto = "https://www.huntercardtcg.com" + url_producto

        # Imagen: buscar <img> dentro del a_tag o dentro de thunk-product-image
        img_tag = cont.find("img")
        img_url = None
        if img_tag:
            img_url = img_tag.get("data-src") or img_tag.get("src")
            if img_url and img_url.startswith("//"):
                img_url = "https:" + img_url

        # Precio: buscar span con clase 'woocommerce-Price-amount' o 'price'
        precio_text = ""
        price_span = cont.find("span", class_="woocommerce-Price-amount")
        if price_span:
            precio_text = price_span.get_text(strip=True)
        else:
            # fallback: buscar .price
            price_wrapper = cont.find("span", class_="price")
            if price_wrapper:
                precio_text = price_wrapper.get_text(strip=True)

        precio_int = extraer_precio(precio_text)
        precio_fmt = formatear_moneda_clp(precio_int) if precio_int is not None else ""

        nombre_limpio, es_foil = limpiar_nombre(titulo_raw)

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
        # Crear nombre de archivo seguro
        safe_name = re.sub(r"[^A-Za-z0-9 _-]", "", p["nombre"]).strip()
        safe_name = re.sub(r"\s+", "_", safe_name)[:80]
        ext = os.path.splitext(url_img)[1].split("?")[0]
        if not ext:
            ext = ".jpg"
        filename = f"{safe_name}{ext}"
        ruta = os.path.join(carpeta, filename)
        try:
            r = requests.get(url_img, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                with open(ruta, "wb") as f:
                    f.write(r.content)
                descargadas += 1
                print(f"📸 ({i}/{total}) Guardada: {filename}")
            else:
                print(f"⚠️ ({i}/{total}) No se pudo bajar imagen (status {r.status_code}): {url_img}")
        except Exception as e:
            print(f"⚠️ ({i}/{total}) Error al bajar imagen: {e}")
        time.sleep(0.2)
    print(f"✅ Imágenes descargadas: {descargadas}/{total}")

def main():
    pagina = 1
    todos = []
    print("🔎 Iniciando scraping...")

    while True:
        print(f"➡️ Procesando página {pagina} ...")
        productos = obtener_productos_por_pagina(pagina)
        if not productos:
            print("ℹ️ No se encontraron productos en esta página — deteniendo.")
            break
        todos.extend(productos)
        pagina += 1
        time.sleep(1)  # pausa para no sobrecargar

    # Crear carpeta y archivo CSV
    os.makedirs("Ficheros", exist_ok=True)
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_archivo = f"Ficheros/List_HunterCard_{fecha}.csv"

    with open(nombre_archivo, "w", newline="", encoding="utf-8") as csvfile:
        campos = ["nombre_original", "nombre", "foil", "precio", "url", "imagen"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todos)

    print(f"\n🟢 Proceso completado. Se guardaron {len(todos)} productos.")
    print(f"📁 Archivo CSV: {nombre_archivo}\n")

    # Preguntar si desea descargar imágenes
    if preguntar_si_no("¿Deseas descargar las imágenes ahora?"):
        carpeta_img = "Ficheros/imagenes_hunter"
        descargar_imagenes(todos, carpeta_img)
    else:
        print("🚫 Descarga de imágenes omitida por el usuario.")

if __name__ == "__main__":
    main()
