import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import os
import re

BASE_URL = "https://www.paytowin.cl"
URL_TEMPLATE = BASE_URL + "/collections/foil?page={}"

def formatear_moneda(valor):
    """Convierte un número entero a formato $xx.xxx CLP"""
    if valor is None:
        return ""
    # Formatea con separador de miles y agrega el signo $
    return f"${valor:,}".replace(",", ".")


def obtener_productos(pagina):
    url = URL_TEMPLATE.format(pagina)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"⚠️ No se pudo acceder a la página {pagina}. Código: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    productos = soup.find_all("div", class_="productCard__card")
    resultados = []

    for producto in productos:
        # Nombre y URL
        titulo_tag = producto.find("p", class_="productCard__title")
        if not titulo_tag:
            continue
        enlace = titulo_tag.find("a")
        nombre = enlace.text.strip()
        url_producto = BASE_URL + enlace["href"]

        # Imagen
        img_tag = producto.find("img", class_="productCard__img")
        if img_tag:
            img_url = img_tag.get("data-src") or img_tag.get("src")
            if img_url.startswith("//"):
                img_url = "https:" + img_url
        else:
            img_url = None

        # Precio (data-price corregido)
        li_chip = producto.find("li", class_="productChip__active")
        if not li_chip or not li_chip.has_attr("data-price"):
            continue
        precio_raw = li_chip["data-price"].strip()
        try:
            # 🔧 Corregido: dividir entre 100 para obtener CLP real
            precio_int = int(precio_raw) // 100
            precio = formatear_moneda(precio_int)
        except ValueError:
            precio = ""

        resultados.append({
            "nombre": nombre,
            "precio": precio,
            "url": url_producto,
            "imagen": img_url
        })

    return resultados

def preguntar_si_no(pregunta):
    """Pide confirmación S/N hasta recibir una respuesta válida"""
    while True:
        respuesta = input(f"{pregunta} (S/N): ").strip().lower()
        if respuesta in ("s", "n"):
            return respuesta == "s"
        print("❌ Opción no válida. Ingresa 'S' para sí o 'N' para no.")

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
    pagina = 1
    todos_los_productos = []

    print("🔍 Iniciando scraping de todas las páginas...")

    while True:
        print(f"➡️ Procesando página {pagina}...")
        productos = obtener_productos(pagina)
        if not productos:
            print("✅ No se encontraron más productos. Fin del scraping.")
            break
        todos_los_productos.extend(productos)
        pagina += 1
        time.sleep(1)  # pausa leve para no saturar servidor

    # Crear carpeta y archivo CSV
    os.makedirs("Ficheros", exist_ok=True)
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_archivo = f"Ficheros/List_PayToWin_{fecha_actual}.csv"

    with open(nombre_archivo, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["nombre", "precio", "url", "imagen"])
        writer.writeheader()
        writer.writerows(todos_los_productos)

    print(f"\n🟢 Scraping completado. Total de productos: {len(todos_los_productos)}")
    print(f"📁 Archivo guardado en: {nombre_archivo}\n")

    # Preguntar si desea descargar las imágenes
    if preguntar_si_no("¿Deseas descargar las imágenes?"):
        descargar_imagenes(todos_los_productos, "Ficheros/imagenes")
    else:
        print("🚫 Descarga de imágenes cancelada por el usuario.")

if __name__ == "__main__":
    main()
