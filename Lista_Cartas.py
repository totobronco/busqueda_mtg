import requests
from bs4 import BeautifulSoup
import csv
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== ANSI COLORS ====================
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"

# ==================== FUNCIONES ====================

def limpiar_texto(texto):
    return " ".join(texto.strip().split())

def obtener_detalle_carta(session, nombre, url):
    """Visita la página de la carta y obtiene detalles"""
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"{RED}❌ Error con {nombre}: {e}{RESET}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Nombre
    nombre_det = soup.select_one(".card-text-card-name")
    nombre_det = limpiar_texto(nombre_det.text) if nombre_det else nombre

    # Coste
    mana_cost_span = soup.select_one(".card-text-mana-cost")
    mana_cost = "".join([abbr.text for abbr in mana_cost_span.find_all("abbr")]) if mana_cost_span else ""

    # Tipo
    tipo = soup.select_one(".card-text-type-line")
    tipo = limpiar_texto(tipo.text) if tipo else ""

    # Descripción
    oracle_div = soup.select_one(".card-text-oracle")
    descripcion = ""
    if oracle_div:
        descripcion = "\n".join([limpiar_texto(p.text) for p in oracle_div.find_all("p")])

    # Ataque/Vida
    stats = soup.select_one(".card-text-stats")
    stats = limpiar_texto(stats.text) if stats else ""

    # Artista
    artista = soup.select_one(".card-text-artist a")
    artista = limpiar_texto(artista.text) if artista else ""

    # Legalidades
    legalidades = {}
    for row in soup.select(".card-legality-item"):
        formato = row.select_one("dt")
        estado = row.select_one("dd")
        if formato and estado:
            legalidades[formato.text.strip()] = estado.text.strip()

    print(f"{GREEN}✅ {nombre} completada{RESET}")
    return {
        "Nombre": nombre_det,
        "URL": url,
        "Coste": mana_cost,
        "Tipo": tipo,
        "Descripcion": descripcion,
        "Ataque/Vida": stats,
        "Artista": artista,
        "Legalidades": legalidades
    }

def obtener_nombre_set(soup):
    """Extrae el nombre del set (ej: 'Final Fantasy (FIN)')"""
    set_title = soup.select_one(".set-header-title-h1")
    if set_title:
        return limpiar_texto(set_title.text)
    return "Scryfall_Set_Desconocido"

def scrapear_lista(url_lista, max_workers=8):
    """Extrae las cartas desde la lista de Scryfall con multihilos"""
    session = requests.Session()

    try:
        resp = session.get(url_lista, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"{RED}❌ Error al acceder a la lista: {e}{RESET}")
        return [], "Set_Desconocido"

    soup = BeautifulSoup(resp.text, "html.parser")
    set_name = obtener_nombre_set(soup)
    items = soup.select(".card-grid-item a.card-grid-item-card")

    print(f"{CYAN}🔍 Set detectado: {set_name}{RESET}")
    print(f"{CYAN}🔍 Cartas encontradas en la lista: {len(items)}{RESET}")

    cartas = []
    tareas = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for item in items:
            nombre = item.select_one(".card-grid-item-invisible-label")
            nombre = limpiar_texto(nombre.text) if nombre else "Desconocido"
            enlace = item.get("href")
            if enlace and not enlace.startswith("http"):
                enlace = "https://scryfall.com" + enlace

            print(f"{YELLOW}➡️ Encolando {nombre}{RESET}")
            tareas.append(executor.submit(obtener_detalle_carta, session, nombre, enlace))

        for future in as_completed(tareas):
            result = future.result()
            if result:
                cartas.append(result)

    return cartas, set_name

def guardar_csv(cartas, set_name):
    """Guarda los datos en un archivo CSV dentro de DB_Carta"""
    os.makedirs("DB_Carta", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Limpieza del nombre del set para el archivo
    nombre_limpio = "".join(c for c in set_name if c.isalnum() or c in (" ", "-", "_")).strip()
    nombre_archivo = f"DB_Carta/{nombre_limpio}_{timestamp}.csv"

    with open(nombre_archivo, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        encabezado = ["Nombre", "URL", "Coste", "Tipo", "Descripcion", "Ataque/Vida", "Artista", "Legalidades"]
        writer.writerow(encabezado)
        for c in cartas:
            writer.writerow([
                c["Nombre"],
                c["URL"],
                c["Coste"],
                c["Tipo"],
                c["Descripcion"],
                c["Ataque/Vida"],
                c["Artista"],
                ", ".join([f"{k}:{v}" for k, v in c["Legalidades"].items()])
            ])

    print(f"\n{GREEN}💾 Archivo guardado en: {nombre_archivo}{RESET}")

# ==================== MAIN ====================

if __name__ == "__main__":
    print(f"{BOLD}=== SCRAPER DE LISTAS DE SCRYFALL (DB Edition) ==={RESET}")
    url_lista = input("👉 Ingresa la URL de la lista de Scryfall: ").strip()

    if not url_lista:
        print(f"{RED}❌ No se ingresó una URL válida.{RESET}")
        exit()

    print(f"{CYAN}🚀 Iniciando descarga en paralelo...{RESET}")
    inicio = time.time()
    cartas, set_name = scrapear_lista(url_lista, max_workers=8)
    duracion = time.time() - inicio

    if cartas:
        guardar_csv(cartas, set_name)
        print(f"{GREEN}✨ Proceso completado: {len(cartas)} cartas en {duracion:.2f} segundos.{RESET}")
    else:
        print(f"{RED}⚠️ No se encontraron cartas o hubo un error.{RESET}")
