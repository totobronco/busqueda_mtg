#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import time
import sys
import unicodedata
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------
# CONFIGURACIÓN (ajustable)
# ---------------------------
BASE_URL = "https://bloodmoongames.cl/singles-magic-the-gathering/?product-page={}"
CSV_DIR = "Ficheros"
PAGES_PER_SAVE = 10               # Guardado parcial acumulativo cada N páginas
MAX_WORKERS = 6                   # Concurrency (ventana de páginas a procesar)
REQUEST_TIMEOUT = 15              # Timeout para request (segundos)
RETRY_WAIT = 20                   # Espera entre reintentos (segundos)
RETRY_CYCLE = 10                  # Reintentos por ciclo (p.ej. 10)
MAX_CYCLES = 3                    # Máximo de ciclos (p.ej. 3) -> máximo reintentos = RETRY_CYCLE * MAX_CYCLES
SPINNER_INTERVAL = 0.08           # Velocidad del spinner
USER_AGENT = "Mozilla/5.0 (compatible; BloodMoonScraper/1.0; +https://example.local)"


# ---------------------------
# ANSI COLORS & ART
# ---------------------------
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"

CASTLE_ART = f"""
{MAGENTA}{BOLD}
                 |>>>                    |>>>
                 |                        |
              _  _|_  _                _  _|_  _
             |;|_|;|_|;|              |;|_|;|_|;|
             \\\\.    .  /              \\\\.    .  /
              \\\:  .  /                \\\:  .  /
               ||:   |                  ||:   |
               ||:.  |                  ||:.  |
               ||:  .|                  ||:  .|
               ||:   |       {YELLOW}BloodMoon Games Scraper{MAGENTA}      ||:   |
               ||: , |   {CYAN}¡Al servicio del Conde!{MAGENTA}     ||: , |
               ||:   |                  ||:   |
               ||: . |                  ||: . |
              /||:   |\\                /||:   |\\
             /_||:___|_\\              /_||:___|_\\
{RESET}
"""

# ---------------------------
# UTIL: Spinner para análisis
# ---------------------------
class Spinner:
    def __init__(self, texto="Analizando"):
        self._stop = threading.Event()
        self._thread = None
        self.texto = texto
        self.frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def start(self):
        def run():
            i = 0
            sys.stdout.write(f"{CYAN}{self.texto}... {RESET}")
            sys.stdout.flush()
            while not self._stop.is_set():
                sys.stdout.write(self.frames[i % len(self.frames)])
                sys.stdout.flush()
                time.sleep(SPINNER_INTERVAL)
                sys.stdout.write("\b")
                i += 1
            # clear spinner char
            sys.stdout.write(" \n")
            sys.stdout.flush()
        self._thread = threading.Thread(target=run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)


# ---------------------------
# PREGUNTA INICIAL CON TIMEOUT
# ---------------------------
def preguntar_pagina_inicio(timeout=5):
    respuesta = [None]
    def hilo_input():
        try:
            r = input(f"{CYAN}¿Desde qué página quieres empezar? (número) [1]: {RESET}")
            respuesta[0] = r
        except Exception:
            pass

    t = threading.Thread(target=hilo_input)
    t.daemon = True
    t.start()
    t.join(timeout)

    if respuesta[0] is None or respuesta[0].strip() == "":
        print(f"{YELLOW}⏱ Tiempo expirado. Iniciando desde la página 1.{RESET}")
        return 1
    try:
        val = int(respuesta[0].strip())
        if val < 1:
            print(f"{YELLOW}⚠ Número inválido. Iniciando desde la página 1.{RESET}")
            return 1
        return val
    except ValueError:
        print(f"{YELLOW}⚠ Entrada no es número. Iniciando desde la página 1.{RESET}")
        return 1


# ---------------------------
# UTIL: Extracción / normalización de precio
# ---------------------------
def extraer_precio(texto_precio):
    """
    Dado un texto con posibles precios (ej: "$9.000", "$4.000 – $12.000", "4.000 CLP", "$4000"),
    devuelve el entero más bajo sin separadores (ej 9000), o None si no encuentra ninguno.
    """
    if not texto_precio:
        return None
    # Normalizar: mantener dígitos, puntos y comas
    # Buscamos grupos de dígitos con puntos o comas
    matches = re.findall(r"[\d\.,]+", texto_precio)
    valores = []
    for m in matches:
        # eliminar puntos y comas (tratamos puntos/comas como separadores de miles)
        limpio = m.replace(".", "").replace(",", "")
        if limpio.isdigit():
            try:
                valores.append(int(limpio))
            except ValueError:
                continue
    if not valores:
        return None
    return min(valores)


# ---------------------------
# UTIL: limpiar nombre
# ---------------------------
def limpiar_nombre(titulo):
    """
    Quita paréntesis, subtítulos, normaliza espacios y acentos.
    Detecta 'foil'.
    """
    foil = bool(re.search(r"\bfoil\b", titulo, flags=re.I))
    s = re.sub(r"\s*\([^)]*\)", "", titulo)  # quitar paréntesis
    s = s.split("–")[0].split("-")[0].strip()
    # Normalizar acentos
    s_norm = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s_norm = re.sub(r"\s+", " ", s_norm).strip()
    return s_norm, foil


# ---------------------------
# OBTENER PRODUCTOS (con manejo de reintentos)
# ---------------------------
def obtener_productos_pagina(session, pagina, spinner_text=None):
    """
    Intenta obtener y parsear la página.
    Implementa reintentos en ciclos: RETRY_CYCLE intents -> esperar (ya hecho fuera) -> repetir hasta MAX_CYCLES.
    Retorna lista de productos o None si se decide saltar la página.
    """
    url = BASE_URL.format(pagina)
    headers = {"User-Agent": USER_AGENT}
    consecutive_failures = 0

    for cycle in range(1, MAX_CYCLES + 1):
        for intento in range(1, RETRY_CYCLE + 1):
            spinner = None
            try:
                if spinner_text:
                    spinner = Spinner(texto=f"{spinner_text} (p{pagina})")
                    spinner.start()
                resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
                if spinner:
                    spinner.stop()
                resp.raise_for_status()
                # parsear
                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.find_all("li", class_="product")
                resultados = []
                for item in items:
                    a_tag = item.find("a", class_="woocommerce-LoopProduct-link")
                    if not a_tag:
                        continue
                    url_producto = a_tag.get("href")
                    h2 = a_tag.find("h2", class_="woocommerce-loop-product__title")
                    if not h2:
                        continue
                    titulo_raw = h2.get_text(strip=True)
                    nombre_limpio, es_foil = limpiar_nombre(titulo_raw)
                    span_price = a_tag.find("span", class_="price")
                    precio_int = extraer_precio(span_price.get_text()) if span_price else None
                    resultados.append({
                        "nombre_original": titulo_raw,
                        "nombre": nombre_limpio,
                        "foil": "Sí" if es_foil else "No",
                        "precio": precio_int if precio_int is not None else "",
                        "url": url_producto
                    })
                return resultados
            except requests.RequestException as e:
                if spinner:
                    spinner.stop()
                consecutive_failures += 1
                print(f"{YELLOW}⚠ Error al solicitar página {pagina} (ciclo {cycle}/{MAX_CYCLES}, intento {intento}/{RETRY_CYCLE}): {e}{RESET}")
                # si fallo de conexión, esperar RETRY_WAIT antes de reintentar
                time.sleep(RETRY_WAIT)
            except Exception as e:
                if spinner:
                    spinner.stop()
                print(f"{RED}❌ Error inesperado al parsear página {pagina}: {e}{RESET}")
                # romper y saltar página
                return None
        # si llegamos aquí, un ciclo terminó sin éxito: avisar y esperar un poco antes del próximo ciclo
        print(f"{MAGENTA}⏳ Ciclo {cycle} de reintentos fallido para página {pagina}. Esperando 60s antes del siguiente ciclo...{RESET}")
        time.sleep(60)  # espera un poco más antes de reintentar otro ciclo

    # Si agotamos todos los ciclos sin éxito, registramos y saltamos la página
    print(f"{RED}✖️ Se agotaron los reintentos para la página {pagina}. Se omite esta página.{RESET}")
    return None


# ---------------------------
# GUARDADO CSV ACUMULATIVO (append)
# ---------------------------
def asegurar_csv_inicial(archivo_csv, campos):
    if not os.path.exists(archivo_csv):
        with open(archivo_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()

def guardar_acumulativo(archivo_csv, productos):
    campos = ["nombre_original", "nombre", "foil", "precio", "url"]
    asegurar_csv_inicial(archivo_csv, campos)
    with open(archivo_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writerows(productos)


# ---------------------------
# SCRAPER PRINCIPAL (con ventana y orden)
# ---------------------------
def scrapear_desde(pagina_inicio=1):
    os.makedirs(CSV_DIR, exist_ok=True)
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_csv = os.path.join(CSV_DIR, f"List_BloodMoon_{fecha}.csv")
    campos = ["nombre_original", "nombre", "foil", "precio", "url"]
    asegurar_csv_inicial(archivo_csv, campos)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # variables control
    pagina_actual = pagina_inicio
    buffer_productos = []      # productos acumulados para guardado parcial
    buffer_pages = {}          # resultados por página para mantener orden {pagina: [productos...]}
    max_consecutive_empty = 5  # to stop if many consecutive pages empty (heurística)
    consecutive_empty = 0

    print(CASTLE_ART)
    print(f"{GREEN}Inicio: {datetime.now().isoformat()}{RESET}")
    print(f"{CYAN}Ventana concurrente: {MAX_WORKERS} páginas. Guardando cada {PAGES_PER_SAVE} páginas.{RESET}")

    # Continuar hasta encontrar página vacía consecutiva suficiente (o hasta que se agote)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}  # page -> future
        # inicializar ventana
        for p in range(pagina_actual, pagina_actual + MAX_WORKERS):
            futures[p] = executor.submit(obtener_productos_pagina, session, p, spinner_text="Analizando página")

        next_page_to_write = pagina_actual
        pages_processed = 0

        while futures:
            # esperar a cualquier future completado
            done, _ = as_completed(list(futures.values()), timeout=None), None
            # as_completed returns generator; we'll iterate retrieving futures as they finish
            for fut in as_completed(list(futures.values())):
                # encontrar a qué página corresponde este future
                page = None
                for pg, f in list(futures.items()):
                    if f is fut:
                        page = pg
                        break
                if page is None:
                    continue

                try:
                    result = fut.result()
                except Exception as e:
                    result = None
                    print(f"{RED}❌ Excepción no controlada en future página {page}: {e}{RESET}")

                # remover de mapa de futures
                del futures[page]

                # si result is None -> saltamos y lo registramos como vacío
                if result is None:
                    # marcar como página omitida: la guardamos como vacía para mantener conteo de páginas
                    buffer_pages[page] = []
                    print(f"{YELLOW}🚧 Página {page} omitida o fallida.{RESET}")
                elif isinstance(result, list) and len(result) == 0:
                    # página sin productos -> puede indicar final
                    buffer_pages[page] = []
                    print(f"{YELLOW}🔎 Página {page} no contiene productos (vacía).{RESET}")
                else:
                    buffer_pages[page] = result
                    print(f"{GREEN}✅ Página {page} procesada: {len(result)} productos.{RESET}")

                pages_processed += 1

                # Encolar la siguiente página para mantener ventana
                next_enqueue = pagina_actual + MAX_WORKERS
                # find highest page currently scheduled/completed to decide next to submit
                # calcula el siguiente page that hasn't been scheduled yet
                scheduled_pages = set(list(futures.keys()) + list(buffer_pages.keys()))
                # determine candidate
                candidate = max(scheduled_pages) + 1 if scheduled_pages else pagina_actual
                # Submit one new page to keep window full (siempre avanzamos en orden)
                # but ensure we don't submit if earlier we found a long streak of empties (we'll still check writing)
                futures[candidate] = executor.submit(obtener_productos_pagina, session, candidate, spinner_text="Analizando página")
                # Now try to write ordered pages starting from next_page_to_write
                while next_page_to_write in buffer_pages:
                    productos_de_pagina = buffer_pages.pop(next_page_to_write)
                    # si la página no tiene productos -> incrementar contador de vacíos consecutivos
                    if not productos_de_pagina:
                        consecutive_empty += 1
                    else:
                        consecutive_empty = 0
                        buffer_productos.extend(productos_de_pagina)

                    # guardado acumulativo cada PAGES_PER_SAVE páginas (basado en conteo de páginas procesadas desde inicio)
                    processed_since_start = next_page_to_write - pagina_inicio + 1
                    if processed_since_start % PAGES_PER_SAVE == 0:
                        if buffer_productos:
                            guardar_acumulativo(archivo_csv, buffer_productos)
                            # animación de guardado
                            anim_guardado(processed_since_start, len(buffer_productos))
                            buffer_productos = []
                        else:
                            # aun asi mostramos animación/nota aunque no haya productos
                            anim_guardado(processed_since_start, 0)
                    # si consecutivas páginas vacías exceden el umbral -> asumimos final
                    if consecutive_empty >= max_consecutive_empty:
                        print(f"{YELLOW}⚠ Se detectaron {consecutive_empty} páginas vacías consecutivas. Asumiendo fin del listado.{RESET}")
                        # guardar restantes y terminar
                        if buffer_productos:
                            guardar_acumulativo(archivo_csv, buffer_productos)
                            anim_guardado("final", len(buffer_productos))
                        print(f"{GREEN}🟢 Scraping finalizado. Archivo: {archivo_csv}{RESET}")
                        return

                    next_page_to_write += 1

            # loop continues automatically

    # fuera del with ThreadPoolExecutor
    # guardar cualquier restante
    if buffer_productos:
        guardar_acumulativo(archivo_csv, buffer_productos)
        anim_guardado("final", len(buffer_productos))

    print(f"{GREEN}🟢 Scraping finalizado. Archivo: {archivo_csv}{RESET}")


# ---------------------------
# ANIMACIÓN DE GUARDADO (temática)
# ---------------------------
def anim_guardado(pages_info, count_products):
    # animación simple tipo barra gótica
    texto = f"Guardando acumulado después de {pages_info} páginas - {count_products} cartas"
    spinner = Spinner(texto=texto)
    spinner.start()
    # duración pequeña para visual; si quieres que espere más, aumentar tiempo
    time.sleep(1.2)
    spinner.stop()
    print(f"{MAGENTA}💀 Los escribas del castillo han sellado {count_products} almas en el CSV.{RESET}")


# ---------------------------
# MAIN
# ---------------------------
def main():
    try:
        print(CASTLE_ART)
        print(f"{BOLD}{CYAN}Bienvenido, cazador. Este script extrae singles de BloodMoonGames.{RESET}")
        pagina_inicio = preguntar_pagina_inicio(timeout=5)
        print(f"{CYAN}➡️ Iniciando desde la página {pagina_inicio}.{RESET}")
        scrapear_desde(pagina_inicio)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏸ Interrumpido por usuario. Saliendo...{RESET}")
    except Exception as e:
        print(f"{RED}❌ Error crítico: {e}{RESET}")


if __name__ == "__main__":
    main()
