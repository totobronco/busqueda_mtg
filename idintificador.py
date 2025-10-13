import csv
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def limpiar_linea(linea):
    """Elimina el número de carta (#...) y espacios extra."""
    return re.sub(r"#.*", "", linea).strip()

def obtener_datos_carta(nombre):
    """Busca los datos de una carta en Scryfall y devuelve (nombre, costo, tipo, url)."""
    print(f"🔍 Buscando carta: {nombre}...")
    
    # Prepara URL de búsqueda
    url_busqueda = f"https://scryfall.com/search?q={nombre.replace(' ', '+')}"
    resp_busqueda = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
    
    if resp_busqueda.status_code != 200:
        print(f"❌ Error al buscar {nombre}")
        return (nombre, "", "", "")
    
    soup = BeautifulSoup(resp_busqueda.text, "html.parser")

    # Encuentra el primer resultado que contenga /card/
    enlace = soup.find("a", href=re.compile(r"/card/"))
    if not enlace:
        print(f"⚠️ No se encontró la carta {nombre} en Scryfall.")
        return (nombre, "", "", "")
    
    # Corrige la URL (usa urljoin para evitar duplicados como scryfall.comhttps)
    url_carta = urljoin("https://scryfall.com", enlace["href"])
    print(f"📄 URL encontrada: {url_carta}")
    
    # Descarga la página de la carta
    resp_carta = requests.get(url_carta, headers={"User-Agent": "Mozilla/5.0"})
    if resp_carta.status_code != 200:
        print(f"❌ Error al abrir página de {nombre}")
        return (nombre, "", "", url_carta)
    
    soup_carta = BeautifulSoup(resp_carta.text, "html.parser")

    # Nombre (sin el prefijo de arena como A-)
    nombre_html = soup_carta.find("span", class_="card-text-card-name")
    if nombre_html:
        nombre_final = nombre_html.get_text(strip=True)
        nombre_final = re.sub(r"^A-", "", nombre_final)  # elimina prefijo A-
    else:
        nombre_final = nombre

    # Costo de maná
    costo_html = soup_carta.find("span", class_="card-text-mana-cost")
    costo = ""
    if costo_html:
        costo = "".join(abbr.get_text(strip=True) for abbr in costo_html.find_all("abbr"))

    # Tipo de carta
    tipo_html = soup_carta.find("p", class_="card-text-type-line")
    tipo = tipo_html.get_text(strip=True) if tipo_html else ""

    print(f"✅ Obtenido: {nombre_final} | {costo} | {tipo}\n")

    return (nombre_final, costo, tipo, url_carta)

def main():
    nombre_archivo = "cartas.txt"  # tu archivo de entrada
    salida_csv = "Inf_carta.csv"

    if not os.path.exists(nombre_archivo):
        print(f"❌ No se encontró el archivo {nombre_archivo}")
        return

    print("📂 Leyendo archivo...")
    with open(nombre_archivo, "r", encoding="utf-8") as f:
        lineas = [limpiar_linea(l) for l in f if l.strip()]

    print(f"📜 {len(lineas)} cartas encontradas en el archivo.\n")

    resultados = []
    for nombre in lineas:
        datos = obtener_datos_carta(nombre)
        resultados.append(datos)

    # Guardar CSV
    print("💾 Guardando resultados en Inf_carta.csv...")
    with open(salida_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Nombre", "Costo", "Tipo", "URL"])
        writer.writerows(resultados)

    print("\n✅ Proceso completado. Archivo generado:", salida_csv)

if __name__ == "__main__":
    main()
