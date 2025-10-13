import requests
from bs4 import BeautifulSoup
import csv
import re
import os
from datetime import datetime
import time
import random

# =========================================
# ANSI colors y estilos
# =========================================
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"
UNDERLINE = "\033[4m"

# =========================================
# Configuración
# =========================================
BASE_URL = "https://www.rivendelelconcilio.cl/mtg-singles-{year}?filter%5Bcfv%5D%5B30145%5D%5B%5D=52073&filter%5Bcfv%5D%5B30145%5D%5B%5D=52069&min=&max=&page={page}"
            
            
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10
REINTENTOS = 5
os.makedirs("Ficheros", exist_ok=True)
fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_FILE = os.path.join("Ficheros", f"List_rivendelelconcilio_{fecha_hora}.csv")
AÑOS = [2012,2013,2017,2018,2019,2020,2021,2022,2023,2024,2025]

# =========================================
# ASCII Art y bienvenida
# =========================================
BIENVENIDA = f"""
{MAGENTA}{BOLD}
╔════════════════════════════════════════════╗
║    🌵 Bienvenido al Cosechador de Cartas 🌵   ║
║   Rivendel el Concilio - Edición Terminal   ║
╚════════════════════════════════════════════╝
{RESET}
"""
print(BIENVENIDA)
print(f"{CYAN}🃏 Vamos a cosechar cartas de los años: {AÑOS}{RESET}\n")

# =========================================
# Funciones auxiliares
# =========================================
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

def obtener_cartas_de_pagina(year, pagina):
    url = BASE_URL.format(year=year, page=pagina)
    intentos = 0
    while intentos < REINTENTOS:
        try:
            print(f"{CYAN}🌾 Explorando año {year}, página {pagina}...{RESET}")
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            intentos += 1
            print(f"{RED}⚠️ Error al acceder a la página {pagina} del año {year}: {e}{RESET}")
            print(f"{YELLOW}⏱ Reintentando en 20 segundos...{RESET}")
            time.sleep(20)
    else:
        print(f"{RED}❌ Página {pagina} del año {year} fallida {REINTENTOS} veces. Saltando...{RESET}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    productos = soup.select("div.product-block")
    if not productos:
        return []

    cartas = []
    for prod in productos:
        nombre_tag = prod.select_one(".caption h3 a")
        if not nombre_tag:
            continue
        nombre_original = nombre_tag.get_text(strip=True)
        nombre = limpiar_nombre(nombre_original)

        enlace = nombre_tag.get("href", "")
        if enlace.startswith("/"):
            enlace = "https://www.rivendelelconcilio.cl" + enlace

        precio_tag = prod.select_one(".price .block-price")
        precio = limpiar_precio(precio_tag.get_text(strip=True)) if precio_tag else 0

        cartas.append({
            "año": year,
            "nombre_original": nombre_original,
            "nombre": nombre,
            "precio": precio,
            "url": enlace
        })

    # Mensaje divertido aleatorio
    mensajes = [
        "✨ Ratas mágicas han encontrado tesoros...",
        "🃏 Cartas volando al CSV...",
        "🌵 Más cartas cosechadas del desierto...",
        "💨 ¡Polvo de cartas por todas partes!"
    ]
    print(f"{MAGENTA}{random.choice(mensajes)}{RESET}")
    time.sleep(random.uniform(1, 2))
    return cartas

# =========================================
# Scraper principal
# =========================================
def scrapear_años_especificos(años):
    todas = []
    resumen_por_año = {}
    for year in años:
        pagina = 1
        contador_por_año = 0
        print(f"\n{BOLD}{UNDERLINE}{YELLOW}🌟 Comenzando cosecha del año {year} 🌟{RESET}")
        while True:
            cartas = obtener_cartas_de_pagina(year, pagina)
            if not cartas:
                print(f"{GREEN}✅ Fin del año {year}. No hay más cartas.{RESET}")
                break
            todas.extend(cartas)
            contador_por_año += len(cartas)
            # Barra de progreso sencilla
            print(f"{BLUE}📦 {len(cartas)} cartas agregadas en esta página. Total hasta ahora: {contador_por_año}{RESET}")
            pagina += 1
        resumen_por_año[year] = contador_por_año
        print(f"{CYAN}🎉 Total de cartas capturadas en {year}: {contador_por_año}{RESET}")

    # Guardar CSV
    if todas:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            campos = ["año", "nombre_original", "nombre", "precio", "url"]
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(todas)
        print(f"\n{GREEN}{BOLD}💾 Se han guardado {len(todas)} cartas en {OUTPUT_FILE}{RESET}")
    else:
        print(f"{RED}❌ No se encontraron cartas para guardar.{RESET}")

    # Resumen final con emojis
    print(f"\n{YELLOW}{BOLD}📊 Resumen final por año:{RESET}")
    for year, total in resumen_por_año.items():
        print(f"{CYAN}- {year}: {total} cartas capturadas 🃏{RESET}")

# =========================================
# Ejecutar scraper
# =========================================
if __name__ == "__main__":
    scrapear_años_especificos(AÑOS)
    print(f"\n{MAGENTA}{BOLD}🏆 ¡Cosecha completa! Gracias por usar el Scraper Mágico 🌵🃏{RESET}\n")
