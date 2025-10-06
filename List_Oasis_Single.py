import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import os
from datetime import datetime

# =========================================
# ANSI colors
# =========================================
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

# =========================================
# Configuración
# =========================================
BASE_URL = "https://www.oasisgames.cl/collections/mtg-singles-instock?page={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10
REINTENTOS = 5

# Frases divertidas por página
PAGINA_FRASES = [
    "Arena movediza para los incautos",
    "Gusanos de arena acechan en la oscuridad",
    "El Spice fluye, los precios suben",
    "Mentats calculando cada carta",
    "Shai-Hulud sonríe desde el desierto",
    "Fremen encuentran tesoros ocultos",
    "El Imperio observa, los jugadores saquean",
    "Cuidado con los Harkonnen",
    "Atreides aseguran sus cartas",
    "Sietch secreto revela nuevas cartas",
    "Tormenta de arena en la colección",
    "El desierto siempre recuerda",
    "Gusanos y cartas, la mezcla perfecta",
    "Prueba de resistencia: carta vs Spice",
    "Cosecha de cartas en el Duneverse",
    "El desierto guarda secretos valiosos",
    "Arrakis ofrece su botín",
    "Sable láser y cartas en mano",
    "El futuro depende de cada página",
    "Ritual de Spice completado"
]

# =========================================
# Cabecera divertida
# =========================================
CABECERA = f"""
{RED}{BOLD}
      ⬤ ⚪ 🔵 🔴 ⚫ 🔶 
   __  __ _____ _____   ____  _   _    _    _   _ _____ __  __ 
  |  \/  | ____|_   _| |  _ \| | | |  / \  | \ | | ____|  \/  |
  | |\/| |  _|   | |   | |_) | | | | / _ \ |  \| |  _| | |\/| |
  | |  | | |___  | |   |  __/| |_| |/ ___ \| |\  | |___| |  | |
  |_|  |_|_____| |_|   |_|    \___//_/   \_\_| \_|_____|_|  |_| 
{RESET}
{CYAN}🪄 Magic Scraper: Cosechando cartas como planeswalkers 🪄{RESET}
"""
print(CABECERA)

# =========================================
# Funciones auxiliares
# =========================================
def detectar_foil(nombre):
    nombre_lower = nombre.lower()
    return "Sí" if "foil" in nombre_lower and "non-foil" not in nombre_lower else "No"

def limpiar_nombre(nombre):
    if "(" in nombre:
        nombre = nombre.split("(")[0].strip()
    return nombre.strip()

def obtener_cartas_de_pagina(pagina):
    url = BASE_URL.format(pagina)
    intentos = 0

    while intentos < REINTENTOS:
        try:
            print(f"{CYAN}🌾 Explorando página {pagina}... {PAGINA_FRASES[(pagina-1) % len(PAGINA_FRASES)]}{RESET}")
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
    productos = soup.select("div.grid-view-item")
    if not productos:
        return []

    cartas = []
    for prod in productos:
        nombre_tag = prod.select_one(".grid-view-item__title")
        if not nombre_tag:
            continue

        nombre_original = nombre_tag.get_text(strip=True)

        enlace_tag = prod.select_one("a[href*='/products/']")
        enlace = ""
        if enlace_tag:
            enlace = enlace_tag.get("href", "")
            if enlace.startswith("/"):
                enlace = "https://www.oasisgames.cl" + enlace

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

    time.sleep(random.uniform(1, 2))
    return cartas

# =========================================
# Función principal para recorrer todas las páginas
# =========================================
if __name__ == "__main__":
    carpeta_salida = "Ficheros"
    os.makedirs(carpeta_salida, exist_ok=True)
    fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
    archivo_salida = os.path.join(carpeta_salida, f"List_Oasis_{fecha_hora}.csv")

    todas_cartas = []
    pagina = 1

    while True:
        cartas = obtener_cartas_de_pagina(pagina)
        if not cartas:
            print(f"{YELLOW}⚠️ No se encontraron cartas en la página {pagina}. Fin del scraping.{RESET}")
            break

        todas_cartas.extend(cartas)
        print(f"{GREEN}✅ {len(cartas)} cartas capturadas en la página {pagina}.{RESET}")
        pagina += 1

    # Guardar en CSV
    if todas_cartas:
        with open(archivo_salida, "w", newline="", encoding="utf-8") as f:
            campos = ["nombre_original", "nombre", "foil", "precio", "url"]
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(todas_cartas)

        print(f"{CYAN}💾 Total de cartas capturadas: {len(todas_cartas)}{RESET}")
        print(f"{CYAN}💾 Datos guardados en {archivo_salida}{RESET}")
    else:
        print(f"{RED}❌ No se capturaron cartas.{RESET}")
