import requests
from bs4 import BeautifulSoup
import csv
import re
import os
from datetime import datetime
import time
import random
import sys

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

BASE_URL = "https://piedrabruja.cl/collections/single-mtg?page={}"

# Crear carpeta Ficheros si no existe
os.makedirs("Ficheros", exist_ok=True)

# Nombre del archivo con fecha y hora
fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_FILE = os.path.join("Ficheros", f"List-PiedraBruja_{fecha_hora}.csv")

# ASCII Art Skaven para la cabecera
CABECERA = f"""
{RED}{BOLD}
   ▄████▄   ▄▄▄      ▄▄▄  ███▄    █  ▄████▄   ▄▄▄       ██▀███  
  ▒██▀ ▀█  ▒████▄   ▄███▒ ██ ▀█   █ ▒██▀ ▀█  ▒████▄    ▓██ ▒ ██▒
  ▒▓█    ▄ ▒██  ▀█▄ ▓███░▓██  ▀█ ██▒▒▓█    ▄ ▒██  ▀█▄  ▓██ ░▄█ ▒
  ▒▓▓▄ ▄██▒░██▄▄▄▄██▓██ █▓██▒  ▐▌██▒▒▓▓▄ ▄██▒░██▄▄▄▄██ ▒██▀▀█▄  
  ▒ ▓███▀ ░ ▓█   ▓██▒██▒ ███▒ ▓▒█░▒ ▓███▀ ░ ▓█   ▓██▒░██▓ ▒██▒
  ░ ░▒ ▒  ░ ▒▒   ▓▒█░▒▒▒ ░██░▒░▒  ░ ░▒ ▒  ░ ▒▒   ▓▒█░░ ▒▓ ░▒▓░
    ░  ▒     ▒   ▒▒ ░░░░▒▒█░░░    ░  ▒     ▒   ▒▒ ░  ░▒ ░ ▒░
  ░          ░   ▒   ░ ░░░▒█░   ░       ░   ▒      ░░   ░ 
  ░ ░            ░  ░░   ░░░      ░ ░       ░  ░    ░     
{RESET}
Skaven Scraper: ¡Ratas husmeando por cartas!
"""

print(CABECERA)

# Frases estilo Skaven por página
PAGINA_FRASES = [
    "Página saqueada por el Clan Skryre",
    "Regalos para la Gran Rata Cornuda",
    "Túneles llenos de oro y cartas",
    "Ratas traviesas encuentran secretos",
    "El Gran Horned Rat sonríe",
    "Pólvora y caos por doquier",
    "Colmillos afilados y botín asegurado",
    "Ratas sobre ruedas husmean tesoros",
    "Bigotes y garras activan la pólvora",
    "Cada carta es un experimento Skryre",
    "El clan Moulder ruge con trampas",
    "Más runas, más caos, más diversión",
    "Túneles secretos llenos de sorpresas",
    "Husmeando cada esquina como un experto",
    "Ratas veloces encuentran el botín primero",
    "Chisporroteos de energía y cartas caen",
    "Gusanos y trampas protegen el oro",
    "La Gran Rata sonríe ante nuestro saqueo",
    "Colmillos y chispas guían nuestra misión",
    "Siempre listos para robar más cartas"
]

def limpiar_nombre(nombre):
    nombre = re.sub(r'\s*\(.*?\)\s*', '', nombre)
    nombre = re.sub(r'\s*\d+$', '', nombre).strip()
    return nombre

def es_foil(nombre):
    return "foil" in nombre.lower()

def limpiar_precio(precio_texto):
    if not precio_texto:
        return 0
    precio = re.sub(r"[^\d]", "", precio_texto)
    try:
        return int(precio)
    except ValueError:
        return 0

def spinner_husmeando():
    for c in "|/-\\":
        sys.stdout.write(f"\r{YELLOW}🐀 Husmeando... {c}{RESET}")
        sys.stdout.flush()
        time.sleep(0.15)

def obtener_datos_pagina(pagina):
    url = BASE_URL.format(pagina)
    spinner_husmeando()
    print(f"\r{CYAN}🐀 Skaven husmeando la página {pagina}... {url}{RESET}")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"{RED}❌ Error al acceder a la página.{RESET}")
        return [], False
    
    soup = BeautifulSoup(response.text, "html.parser")
    productos = soup.find_all("div", class_="product-item")
    if not productos:
        print(f"{GREEN}✅ No hay más productos. Las ratas descansan.{RESET}")
        return [], False
    
    data = []
    for prod in productos:
        link_tag = prod.find("a", class_="product-item__title")
        if not link_tag:
            continue
        
        nombre_original = link_tag.text.strip()
        url_producto = "https://piedrabruja.cl" + link_tag["href"]
        precio_tag = prod.find("span", class_="price")
        precio_texto = precio_tag.text.strip() if precio_tag else "0"
        precio = limpiar_precio(precio_texto)
        
        nombre_limpio = limpiar_nombre(nombre_original)
        foil = "Sí" if es_foil(nombre_original) else "No"
        
        data.append({
            "nombre_original": nombre_original,
            "nombre": nombre_limpio,
            "foil": foil,
            "precio": precio,
            "url": url_producto
        })
    
    # Frase divertida por página
    frase = PAGINA_FRASES[(pagina-1) % len(PAGINA_FRASES)]
    print(f"{MAGENTA}Página {pagina}: {frase}{RESET}")
    time.sleep(random.uniform(0.5, 1.5))  # Pausa dramática
    return data, True

def guardar_csv(data):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nombre_original", "nombre", "foil", "precio", "url"])
        writer.writeheader()
        writer.writerows(data)
    print(f"{GREEN}💾 Archivo CSV guardado como: {CYAN}{OUTPUT_FILE}{RESET}")

def main():
    print(f"{CYAN}🔎 Las ratas Skaven comienzan su saqueo de PiedraBruja.cl...{RESET}")
    pagina = 1
    all_data = []

    while True:
        datos, continuar = obtener_datos_pagina(pagina)
        if not continuar:
            break
        all_data.extend(datos)
        pagina += 1
    
    if all_data:
        guardar_csv(all_data)
        print(f"""
{RED}{BOLD}
  ╔════════════════════════════════╗
  ║ ¡El clan Skaven completó su botín! ║
  ║ {len(all_data)} cartas recopiladas con éxito. ║
  ╚════════════════════════════════╝
{RESET}
        """)
    else:
        print(f"{RED}❌ No se encontraron cartas para guardar. Las ratas vuelven a la madriguera.{RESET}")

if __name__ == "__main__":
    main()
