import requests
import csv
import os
import time
import random
from datetime import datetime

# ==================== ANSI COLORS ====================
RESET = "\033[0m"
BOLD = "\033[1m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"

# ==================== DUNE THEMATIC MESSAGES ====================
mensajes_dune = [
    "🌵 Las arenas se mueven... los gusanos acechan bajo la superficie.",
    "🔥 ‘El que controla la especia controla el universo.’",
    "💨 El viento del desierto trae nuevos productos...",
    "🌞 Shai-Hulud despierta, los precios tiemblan.",
    "💫 ‘Fear is the mind-killer...’ pero este scraper no teme.",
    "🌀 Atravesando las dunas... buscando más tesoros.",
    "🐍 El gran gusano del desierto avanza hacia la próxima página..."
]

# ==================== GUSANO ANIMADO ====================
def animar_gusano():
    frames = [
        "        🐍        ",
        "          🐍      ",
        "            🐍    ",
        "              🐍  ",
        "                🐍",
        "              🐍  ",
        "            🐍    ",
        "          🐍      ",
        "        🐍        ",
        "      🐍          ",
    ]
    for frame in frames:
        print(f"\r{YELLOW}{frame}{RESET}", end="", flush=True)
        time.sleep(0.03)  # 🔹 más rápido que antes
    print("\n")

# ==================== URL BASE ====================
BASE_URL = "https://www.oasisgames.cl/collections/mtg-singles-instock/products.json?page="

# ==================== OBTENER PRODUCTOS ====================
def obtener_productos():
    print(f"{BOLD}{YELLOW}🔥 Iniciando extracción de productos desde el desierto de Arrakis... 🔥{RESET}\n")

    session = requests.Session()
    page = 1
    total_global = 0
    all_products = []

    while True:
        print(f"{BOLD}{CYAN}Procesando página {page}...{RESET}\n")
        animar_gusano()

        url = f"{BASE_URL}{page}"
        productos_pagina = None

        # ==================== REINTENTOS ====================
        for intento in range(3):
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    productos_pagina = data.get("products", [])
                    break
                else:
                    print(f"{RED}Error {response.status_code} en página {page}, intento {intento+1}/3...{RESET}")
            except Exception as e:
                print(f"{RED}Fallo conexión ({e}). Reintentando en 20 segundos...{RESET}")
                time.sleep(20)

        if productos_pagina is None:
            print(f"{RED}No se pudo recuperar la página {page} tras 3 intentos. Terminando proceso.{RESET}")
            break

        cantidad = len(productos_pagina)
        if cantidad == 0:
            print(f"{RED}No se encontraron más productos. Finalizando.{RESET}")
            break

        total_global += cantidad
        print(f"{GREEN}Productos encontrados en página {page}: {cantidad}{RESET}\n")

        for product in productos_pagina:
            title = product.get("title", "Sin nombre")
            price_str = product.get("variants", [{}])[0].get("price", "0")
            try:
                price = float(price_str) / 1000
            except ValueError:
                price = 0.0
            all_products.append({
                "Nombre": title,
                "Precio": price
            })

        print(f"{YELLOW}{random.choice(mensajes_dune)}{RESET}")
        print(f"{BOLD}{MAGENTA}Total acumulado: {total_global}{RESET}\n")

        # 🔹 Guardado parcial cada 100 páginas
        if page % 100 == 0:
            guardar_csv(all_products, parcial=True, pagina=page)

        # 🔹 Pequeña pausa cada 10 páginas para no saturar el servidor
        if page % 10 == 0:
            time.sleep(2)

        page += 1

    return all_products, total_global

# ==================== GUARDAR CSV ====================
def guardar_csv(productos, parcial=False, pagina=None):
    carpeta = "Ficheros"
    os.makedirs(carpeta, exist_ok=True)
    fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if parcial:
        filename = f"{carpeta}/List_Oasis_Single_PARCIAL_p{pagina}_{fecha_hora}.csv"
        print(f"{CYAN}💾 Guardado parcial en página {pagina}: {filename}{RESET}")
    else:
        filename = f"{carpeta}/List_Oasis_Single_{fecha_hora}.csv"
        print(f"{GREEN}💾 Guardado final: {filename}{RESET}")

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Nombre", "Precio"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(productos)

# ==================== MAIN ====================
if __name__ == "__main__":
    productos, total = obtener_productos()
    print(f"{BOLD}{CYAN}Total de productos encontrados: {total}{RESET}")
    guardar_csv(productos)
    print(f"{BOLD}{MAGENTA}\nEl gusano duerme... pero la especia sigue fluyendo.{RESET}")
