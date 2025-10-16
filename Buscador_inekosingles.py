import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import urllib.parse
import time
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

# === CONFIGURACIÓN ===
BASE_URL = "https://inekosingles.com/search?q="
OUTPUT_FOLDER = "revisar_Precio"
INPUT_FILE = "Lista_inekosingles.txt"
RETRY_DELAY = 20  # segundos de espera si hay error 429
MAX_RETRIES = 3   # reintentos máximos

# Crear carpeta si no existe
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Crear nombre del archivo de salida
fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M")
output_file = os.path.join(OUTPUT_FOLDER, f"inekosingles_{fecha_actual}.csv")

# Leer cartas del archivo
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    cartas = [line.strip() for line in f if line.strip()]

total_cartas = len(cartas)
print(f"{Fore.CYAN}📘 Se cargaron {total_cartas} cartas desde {INPUT_FILE}{Style.RESET_ALL}\n")

# Crear sesión de requests
session = requests.Session()

resultados = []

for i, carta in enumerate(cartas, start=1):
    print(f"{Fore.YELLOW}🔍 [{i}/{total_cartas}] Buscando:{Style.RESET_ALL} {carta}")
    query = urllib.parse.quote(carta)
    url_busqueda = f"{BASE_URL}{query}"

    # === Reintento automático si hay error 429 ===
    intentos = 0
    while intentos < MAX_RETRIES:
        try:
            response = session.get(url_busqueda, timeout=15)
            if response.status_code == 429:
                intentos += 1
                print(f"{Fore.RED}⚠️  ERROR 429: demasiadas solicitudes para '{carta}'. Esperando {RETRY_DELAY}s...{Style.RESET_ALL}")
                time.sleep(RETRY_DELAY)
                continue
            response.raise_for_status()
            break  # éxito
        except requests.exceptions.RequestException as e:
            intentos += 1
            if intentos < MAX_RETRIES:
                print(f"{Fore.RED}⚠️  Error al obtener '{carta}': {e}")
                print(f"{Fore.YELLOW}⏳ Reintentando en {RETRY_DELAY}s...{Style.RESET_ALL}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"{Fore.RED}❌ Fallo permanente en '{carta}' después de {MAX_RETRIES} intentos.{Style.RESET_ALL}")
                resultados.append({
                    "Carta buscada": carta,
                    "Nombre encontrado": "",
                    "Precio": "Error",
                    "URL": url_busqueda,
                    "Estado": "Error"
                })
                break
    else:
        continue  # si falló los reintentos, pasar a la siguiente

    # === Procesar resultados ===
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        productos = soup.select("li.grid__item")

        if not productos:
            print(f"  {Fore.RED}❌ No encontrado{Style.RESET_ALL}")
            resultados.append({
                "Carta buscada": carta,
                "Nombre encontrado": "",
                "Precio": "No encontrado",
                "URL": url_busqueda,
                "Estado": "No encontrado"
            })
            continue

        coincidencias = []
        for producto in productos:
            nombre_tag = producto.select_one("h3.card__heading a")
            precio_tag = producto.select_one(".price-item--regular")
            agotado_tag = producto.select_one(".badge")

            if not nombre_tag:
                continue

            nombre = nombre_tag.get_text(strip=True)
            enlace = "https://inekosingles.com" + nombre_tag["href"]
            precio = precio_tag.get_text(strip=True) if precio_tag else "Sin precio"
            agotado = agotado_tag and "Agotado" in agotado_tag.get_text(strip=True)

            # El nombre debe contener completamente el texto de búsqueda
            if carta.lower() not in nombre.lower():
                continue

            coincidencias.append({
                "Carta buscada": carta,
                "Nombre encontrado": nombre,
                "Precio": "Agotado" if agotado else precio,
                "URL": enlace,
                "Estado": "Agotado" if agotado else "Disponible"
            })

        # Si no hay coincidencias exactas
        if not coincidencias:
            print(f"  {Fore.RED}❌ Sin coincidencias exactas{Style.RESET_ALL}")
            resultados.append({
                "Carta buscada": carta,
                "Nombre encontrado": "",
                "Precio": "No encontrado",
                "URL": url_busqueda,
                "Estado": "No encontrado"
            })
            continue

        # === Filtrado inteligente ===
        disponibles = [c for c in coincidencias if c["Estado"] == "Disponible"]
        agotados = [c for c in coincidencias if c["Estado"] == "Agotado"]

        if disponibles:
            for c in disponibles:
                resultados.append(c)
                print(f"  {Fore.GREEN}💰 {c['Nombre encontrado']} → {c['Precio']}{Style.RESET_ALL}")
        else:
            # todas agotadas → solo guardar una línea
            resultados.append({
                "Carta buscada": carta,
                "Nombre encontrado": agotados[0]["Nombre encontrado"],
                "Precio": "Agotado",
                "URL": agotados[0]["URL"],
                "Estado": "Todo agotado"
            })
            print(f"  {Fore.MAGENTA}💀 Todo agotado{Style.RESET_ALL}")

    except Exception as e:
        print(f"  {Fore.RED}⚠️ Error procesando '{carta}':{Style.RESET_ALL} {e}")
        resultados.append({
            "Carta buscada": carta,
            "Nombre encontrado": "",
            "Precio": "Error",
            "URL": url_busqueda,
            "Estado": "Error"
        })

# === Guardar CSV limpio ===
df = pd.DataFrame(resultados)
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n{Fore.CYAN}✅ Archivo guardado en:{Style.RESET_ALL} {output_file}")
print(f"{Fore.GREEN}🏁 Proceso completado. Total analizadas: {total_cartas}{Style.RESET_ALL}")
