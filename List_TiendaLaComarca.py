import requests
import csv
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
BASE_URL = "https://www.tiendalacomarca.cl/collections/mtg-singles/products.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10
REINTENTOS = 5

# Carpeta y nombre de archivo
os.makedirs("Ficheros", exist_ok=True)
fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_FILE = os.path.join("Ficheros", f"List_TiendaLaComarca_{fecha_hora}.csv")

# =========================================
# ASCII Art y bienvenida
# =========================================
BIENVENIDA = f"""
{MAGENTA}{BOLD}
╔════════════════════════════════════════════╗
║    🃏 Bienvenido al Cosechador de Cartas 🃏   ║
║        Tienda La Comarca - Edición Terminal ║
╚════════════════════════════════════════════╝
{RESET}
"""
print(BIENVENIDA)

# =========================================
# Funciones auxiliares
# =========================================
def limpiar_precio(precio):
    """Convierte precio de Shopify a entero"""
    try:
        return int(precio)
    except:
        return 0

def obtener_productos(pagina):
    """Obtiene productos de la página JSON de Shopify"""
    url = f"{BASE_URL}?page={pagina}"
    intentos = 0
    while intentos < REINTENTOS:
        try:
            print(f"{CYAN}🌾 Explorando página {pagina}...{RESET}")
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            productos = data.get("products", [])
            print(f"{BLUE}🔹 Encontrados {len(productos)} productos en la página {pagina}{RESET}")
            return productos
        except requests.exceptions.RequestException as e:
            intentos += 1
            print(f"{RED}⚠️ Error al acceder a la página {pagina}: {e}{RESET}")
            print(f"{YELLOW}⏱ Reintentando en 5 segundos...{RESET}")
            time.sleep(5)
    print(f"{RED}❌ Página {pagina} fallida {REINTENTOS} veces. Saltando...{RESET}")
    return []

def extraer_datos(productos):
    """Extrae nombre, precio y URL de cada producto"""
    lista = []
    for prod in productos:
        nombre = prod.get("title", "SIN NOMBRE")
        handle = prod.get("handle", "")
        url = f"https://www.tiendalacomarca.cl/products/{handle}" if handle else ""
        
        variantes = prod.get("variants", [])
        precio_mas_bajo = min([int(v.get("price", 0)) for v in variantes]) if variantes else 0
        precio_formateado = limpiar_precio(precio_mas_bajo)
        
        lista.append({
            "nombre": nombre,
            "precio": precio_formateado,
            "url": url
        })
    return lista

def guardar_csv(productos):
    """Guarda los productos en CSV dentro de Ficheros con fecha-hora"""
    if not productos:
        print(f"{RED}❌ No hay productos para guardar.{RESET}")
        return
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        campos = ["nombre", "precio", "url"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(productos)
    print(f"{GREEN}{BOLD}💾 Se han guardado {len(productos)} productos en {OUTPUT_FILE}{RESET}")

# =========================================
# Scraper principal
# =========================================
def scrapear_tienda():
    todos_productos = []
    pagina = 1
    while True:
        productos_json = obtener_productos(pagina)
        if not productos_json:
            print(f"{GREEN}✅ No hay más productos en la página {pagina}. Finalizando.{RESET}")
            break
        
        productos_extraidos = extraer_datos(productos_json)
        todos_productos.extend(productos_extraidos)
        print(f"{MAGENTA}📦 Capturadas {len(productos_extraidos)} cartas en la página {pagina}{RESET}")
        
        # Mensaje divertido aleatorio
        mensajes = [
            "✨ Cartas mágicas volando al CSV...",
            "🃏 Tesoros encontrados y guardados...",
            "🌵 Más cartas cosechadas del desierto...",
            "💨 Polvo de cartas por todas partes..."
        ]
        print(f"{MAGENTA}{random.choice(mensajes)}{RESET}")
        
        pagina += 1
        time.sleep(random.uniform(1, 2))
    
    guardar_csv(todos_productos)
    print(f"\n{MAGENTA}{BOLD}🏆 ¡Cosecha completa! Gracias por usar el Scraper Mágico 🌵🃏{RESET}\n")

# =========================================
# Ejecutar scraper
# =========================================
if __name__ == "__main__":
    scrapear_tienda()
