import requests
import csv
import os
from datetime import datetime
import time
import random

# === Colores ANSI ===
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

# === URL base (API JSON de Shopify) ===
BASE_URL = "https://www.oasisgames.cl/collections/mtg-singles-instock/products.json?page="

# === Carpeta de salida ===
output_dir = "Ficheros"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = os.path.join(output_dir, f"List_Oasis_{timestamp}.csv")

def obtener_productos(page):
    """Obtiene los productos desde la API JSON de Oasis Games."""
    url = f"{BASE_URL}{page}"
    print(f"\n{CYAN}Procesando página {page}...{RESET}")
    print(f"{YELLOW}URL: {url}{RESET}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{RED}Error HTTP {response.status_code}{RESET}")
            return []

        data = response.json()
        productos = data.get("products", [])
        print(f"{GREEN}Productos encontrados en página {page}: {len(productos)}{RESET}")

        resultado = []
        for idx, prod in enumerate(productos, start=1):
            try:
                nombre = prod.get("title", "Sin nombre").strip()
                handle = prod.get("handle", "")
                url_producto = f"https://www.oasisgames.cl/products/{handle}"

                # Buscar precio más bajo entre variantes
                variantes = prod.get("variants", [])
                precios = []

                for v in variantes:
                    precio_raw = v.get("price")
                    if precio_raw is None:
                        continue
                    # Convertir string a número
                    try:
                        precio_float = float(precio_raw)
                        precios.append(precio_float)
                    except ValueError:
                        print(f"{YELLOW}[DEBUG] Precio inválido en variante: {precio_raw}{RESET}")

                if not precios:
                    print(f"{YELLOW}[DEBUG] No hay precios válidos para: {nombre}{RESET}")
                    continue

                precio_min = min(precios)
                # Shopify usa centavos → dividir por 100 si el valor es alto
                if precio_min > 1000:
                    precio_min = precio_min / 100.0

                precio_formateado = f"${precio_min:,.0f}".replace(",", ".")

                resultado.append({
                    "Nombre": nombre,
                    "Precio": precio_formateado,
                    "URL": url_producto
                })

                print(f"{GREEN}✔ Producto OK:{RESET} {nombre} - {precio_formateado}")

            except Exception as e:
                print(f"{RED}[ERROR] Fallo procesando producto #{idx}: {e}{RESET}")

        return resultado

    except Exception as e:
        print(f"{RED}Error procesando página {page}: {e}{RESET}")
        return []


# === Bucle principal ===
todos_productos = []
pagina = 1

while True:
    productos = obtener_productos(pagina)
    if not productos:
        print(f"{MAGENTA}No se encontraron más productos. Finalizando.{RESET}")
        break

    todos_productos.extend(productos)
    pagina += 1
    time.sleep(random.uniform(1, 2))  # pequeña pausa anti-baneo

# === Guardar CSV ===
if todos_productos:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Nombre", "Precio", "URL"])
        writer.writeheader()
        writer.writerows(todos_productos)

    print(f"\n{BOLD}{GREEN}✅ Archivo guardado correctamente en:{RESET} {CYAN}{filename}{RESET}")
    print(f"{YELLOW}Total de productos capturados: {len(todos_productos)}{RESET}")
else:
    print(f"{RED}No se capturaron productos.{RESET}")
