import re
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

# Carpeta para guardar CSV
carpeta_salida = "Mazo"
os.makedirs(carpeta_salida, exist_ok=True)

def limpiar_linea_quitar_paren(linea):
    """
    Mantiene todo hasta justo antes del primer '(' (si existe).
    Ej: "1 Nahiri (CMM) 45" -> "1 Nahiri"
    """
    linea = linea.rstrip("\n\r")
    if "(" in linea:
        linea = linea.split("(", 1)[0]
    return linea.rstrip()

def nombre_para_busqueda(linea_limpia):
    """
    Quita el número inicial para formar el nombre usado en la búsqueda.
    Ej: "1 Nahiri" -> "Nahiri"
    """
    return re.sub(r'^\d+\s*', '', linea_limpia).strip()

# Buscar carta en Scryfall
def buscar_carta(nombre_carta):
    nombre_query = nombre_carta.replace(" ", "+")
    url_busqueda = f"https://scryfall.com/search?q=!\"{nombre_query}\"&unique=prints"

    print(f"\n🔍 Buscando carta: {nombre_carta}")
    try:
        respuesta = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con Scryfall: {e}")
        return None

    sopa = BeautifulSoup(respuesta.text, "html.parser")
    carta_principal = sopa.find("a", class_="card-grid-item-card")

    if carta_principal and "href" in carta_principal.attrs:
        href = carta_principal["href"]
        enlace_carta = href if href.startswith("http") else "https://scryfall.com" + href
        print(f"✅ Encontrada: {nombre_carta}")
        return enlace_carta

    print("⚠️ No se encontró coincidencia exacta.")
    return None

# Obtener datos de la carta
def obtener_datos_carta(url_carta):
    try:
        respuesta = requests.get(url_carta, headers={"User-Agent": "Mozilla/5.0"})
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener datos de la carta: {e}")
        return None

    sopa = BeautifulSoup(respuesta.text, "html.parser")

    nombre_tag = sopa.find("h1", class_="card-text-title")
    nombre = nombre_tag.text.strip() if nombre_tag else ""

    costo_tag = sopa.find("span", class_="card-text-mana-cost")
    costo = costo_tag.text.strip() if costo_tag else ""

    tipo_tag = sopa.find("p", class_="card-text-type-line")
    tipo = tipo_tag.text.strip() if tipo_tag else ""

    texto_tag = sopa.find("div", class_="card-text-oracle")
    texto = texto_tag.text.strip() if texto_tag else ""

    return {
        "Nombre": nombre,
        "Costo": costo,
        "Tipo": tipo,
        "Texto": texto,
        "URL": url_carta
    }

def main():
    # Leer cartas desde el archivo original
    input_path = "Lista_mazo.txt"
    with open(input_path, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Limpiar cada línea quitando desde '(' en adelante (pero manteniendo el "1 ")
    lineas_limpiadas = [limpiar_linea_quitar_paren(l) for l in lineas]

    # Guardar versión limpia del archivo (opcional)
    cleaned_path = "Lista_mazo_clean.txt"
    with open(cleaned_path, "w", encoding="utf-8") as f:
        for ln in lineas_limpiadas:
            f.write(ln + "\n")
    print(f"✅ Archivo limpio guardado en '{cleaned_path}'")

    # Preparar nombres para búsqueda (sin el número inicial)
    nombres_busqueda = [nombre_para_busqueda(ln) for ln in lineas_limpiadas]

    print("📜 Cartas a buscar (nombre):")
    for nb in nombres_busqueda:
        print(f"  - {nb}")

    resultados = []
    for nombre in nombres_busqueda:
        if not nombre:
            continue
        url = buscar_carta(nombre)
        if url:
            datos = obtener_datos_carta(url)
            if datos:
                resultados.append(datos)

    # Nombre del archivo CSV con fecha y hora
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_csv = os.path.join(carpeta_salida, f"Mazo_{fecha_hora}.csv")

    # Guardar CSV
    with open(archivo_csv, "w", newline="", encoding="utf-8") as f:
        campos = ["Nombre", "Costo", "Tipo", "Texto", "URL"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\n✅ Datos guardados en '{archivo_csv}'")

if __name__ == "__main__":
    main()
