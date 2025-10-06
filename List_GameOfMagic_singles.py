import requests
from bs4 import BeautifulSoup
import csv
import re
import os
from datetime import datetime
import time
import random

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

BASE_URL = "https://gameofmagicsingles.cl/collections/mtg-todas-las-singles?page={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10
REINTENTOS = 5

# Crear carpeta Ficheros si no existe
os.makedirs("Ficheros", exist_ok=True)

# Nombre del archivo con fecha y hora
fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_FILE = os.path.join("Ficheros", f"List-gameofmagicsingles_{fecha_hora}.csv")

# Cabecera MTG
CABECERA = f"""
{CYAN}{BOLD}
 __  __ _____ _____   ____  _   _    _    _   _ _____ __  __ 
|  \/  | ____|_   _| |  _ \| | | |  / \  | \ | | ____|  \/  |
| |\/| |  _|   | |   | |_) | | | | / _ \ |  \| |  _| | |\/| |
| |  | | |___  | |   |  __/| |_| |/ ___ \| |\  | |___| |  | |
|_|  |_|_____| |_|   |_|    \___//_/   \_\_| \_|_____|_|  |_|
{RESET}
🪄 Scraper MTG: Cosechando cartas como planeswalkers 🪄
"""

print(CABECERA)

# Frases divertidas MTG por página
FRASES_PAGINA = [
    "¡El planar se sacude con nuevas cartas!",
    "Invocando criaturas y hechizos en tu colección...",
    "Explorando la biblioteca arcana de Magic...",
    "¡Tesoros y planeswalker atrapados!",
    "El grimorio revela secretos preciosos...",
    "¡Hechizos en acción, artefactos capturados!",
    "Planos cruzados y cartas recolectadas...",
    "¡Tap, untap y a guardar cartas!",
    "Conjurando rarezas y tesoros...",
    "¡La mesa está llena de hechizos y criaturas!"
]

def limpiar_precio(precio_texto):
    """Convierte '$6,400 CLP' en 6400"""
    if not precio_texto:
        return 0
    precio = re.sub(r"[^\d]", "", precio_texto)
    try:
        return int(precio)
    except ValueError:
        return 0

def limpiar_nombre(nombre):
    """Limpia el nombre de la carta"""
    return nombre.strip()

def obtener_cartas_de_pagina(pagina):
    url = BASE_URL.format(pagina)
    intentos = 0

    while intentos < REINTENTOS:
        try:
            print(f"{CYAN}🌿 Explorando página {pagina}...{RESET}")
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            intentos += 1
            print(f"{RED}⚠️ Error al acceder a la página {pagina}: {e}{RESET}")
            print(f"{YELLOW}⏱ Esperando 20 segundos antes de reintentar...{RESET}")
            time.sleep(20)
    else:
        print(f"{RED}❌ La página {pagina} falló {REINTENTOS} veces. Saltando...{RESET}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    productos = soup.select("div.productCard__card")
    if not productos:
        return []

    cartas = []
    for prod in productos:
        # Nombre de la carta
        nombre_tag = prod.select_one(".productCard__title a")
        if not nombre_tag:
            continue
        nombre_original = nombre_tag.get_text(strip=True)
        nombre = limpiar_nombre(nombre_original)

        # URL de la carta
        enlace = nombre_tag.get("href", "")
        if enlace.startswith("/"):
            enlace = "https://gameofmagicsingles.cl" + enlace

        # Precio más bajo
        precio_tag = prod.select_one(".productCard__price")
        precio = limpiar_precio(precio_tag.get_text(strip=True)) if precio_tag else 0

        cartas.append({
            "nombre_original": nombre_original,
            "nombre": nombre,
            "precio": precio,
            "url": enlace
        })

    # Mensaje divertido MTG
    frase = random.choice(FRASES_PAGINA)
    print(f"{MAGENTA}🎴 Página {pagina}: Capturadas {len(cartas)} cartas. {frase}{RESET}")
    time.sleep(random.uniform(1, 2))
    return cartas

def scrapear_todas_las_paginas():
    todas = []
    pagina = 1

    while True:
        cartas = obtener_cartas_de_pagina(pagina)
        if not cartas:
            print(f"{GREEN}✅ No hay más productos. Fin del scraping.{RESET}")
            break

        todas.extend(cartas)
        print(f"{YELLOW}🗃️ Total acumulado hasta ahora: {len(todas)} cartas{RESET}\n")
        pagina += 1

    if not todas:
        print(f"{RED}❌ No se encontraron cartas para guardar.{RESET}")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        campos = ["nombre_original", "nombre", "precio", "url"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todas)

    print(f"\n{GREEN}💾 {len(todas)} cartas guardadas en {CYAN}{OUTPUT_FILE}{RESET}")
    print(f"{YELLOW}🪄 La cosecha de cartas MTG ha terminado. ¡Que los hechizos te acompañen!{RESET}")

if __name__ == "__main__":
    scrapear_todas_las_paginas()
