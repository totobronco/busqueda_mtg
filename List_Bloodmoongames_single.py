#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper BloodMoonGames - Versión final consolidada
- Guardados parciales acumulativos a Ficheros/List_BloodMoon.csv
- Respeta orden de páginas, usa prefetch para acelerar
- Respalda archivo antiguo al iniciar (timestamp)
- Si todo finaliza con éxito: crea archivo final timestamped y borra backups antiguos
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import time
import sys
import glob
import shutil
import unicodedata
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# CONFIGURACIÓN
# ----------------------------
BASE_URL = "https://bloodmoongames.cl/singles-magic-the-gathering/?product-page={}"
FOLDER = "Ficheros"
FINAL_NAME = "List_BloodMoon.csv"                # nombre fijo para guardados parciales
BACKUP_PREFIX = "List_BloodMoon"                # prefijo para backups timestamped
PAGES_PER_SAVE = 10                              # guardado parcial cada N páginas
WINDOW_SIZE = 5                                  # ventana de prefetch (n páginas adelantadas)
REQUEST_TIMEOUT = 15                             # timeout de requests
RETRY_WAIT = 20                                  # segundos a esperar entre reintentos
RETRY_CYCLE = 10                                 # intentos por ciclo
MAX_CYCLES = 2                                   # ciclos (max attempts = RETRY_CYCLE * MAX_CYCLES)
SPINNER_INTERVAL = 0.08
USER_AGENT = "Mozilla/5.0 (compatible; BloodMoonScraper/1.0)"

# ----------------------------
# ANSI colors & art
# ----------------------------
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"

CASTLE_ART = f"""
{MAGENTA}{BOLD}
  ██████╗ ██╗      ██████╗  ██████╗ ██████╗ ███╗   ███╗ ██████╗
  ██╔══██╗██║     ██╔═══██╗██╔════╝ ██╔══██╗████╗ ████║██╔═══██╗
  ██████╔╝██║     ██║   ██║██║  ███╗██████╔╝██╔████╔██║██║   ██║
  ██╔══██╗██║     ██║   ██║██║   ██║██╔═══╝ ██║╚██╔╝██║██║   ██║
  ██████╔╝███████╗╚██████╔╝╚██████╔╝██║     ██║ ╚═╝ ██║╚██████╔╝
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝     ╚═╝ ╚═════╝
           ⚔️  BloodMoon Games Scraper - Castlevania Theme  ⚔️
{RESET}
"""

# ----------------------------
# Spinner (simple)
# ----------------------------
class Spinner:
    def __init__(self, text="Procesando"):
        self._stop = threading.Event()
        self.thread = None
        self.text = text
        self.frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def start(self):
        def run():
            i = 0
            sys.stdout.write(f"{CYAN}{self.text}... {RESET}")
            sys.stdout.flush()
            while not self._stop.is_set():
                sys.stdout.write(self.frames[i % len(self.frames)])
                sys.stdout.flush()
                time.sleep(SPINNER_INTERVAL)
                sys.stdout.write("\b")
                i += 1
            sys.stdout.write(" \n")
            sys.stdout.flush()
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=0.5)

# ----------------------------
# Utilities: precios y nombres
# ----------------------------
def limpiar_nombre(titulo):
    """Limpia el título, elimina paréntesis y normaliza espacios."""
    foil = bool(re.search(r"\bfoil\b", titulo, flags=re.I))
    s = titulo.strip()
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = s.split("–")[0].split("-")[0].strip()
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = re.sub(r"\s+", " ", s)
    return s, foil

def extraer_precio(texto_precio):
    """
    Extrae todos los grupos númericos y considera separadores de miles (.,)
    Convierte a entero eliminando puntos/comas y devuelve el menor encontrado.
    Ej: '$9.000 – $12.000' -> 9000
    """
    if not texto_precio:
        return None
    grupos = re.findall(r"[\d\.,]+", texto_precio)
    valores = []
    for g in grupos:
        limpio = g.replace(".", "").replace(",", "")
        if limpio.isdigit():
            valores.append(int(limpio))
    if not valores:
        return None
    return min(valores)

# ----------------------------
# Manejo backup: mover final existente a backup con timestamp
# ----------------------------
def mover_actual_a_backup(folder=FOLDER, final_name=FINAL_NAME, prefix=BACKUP_PREFIX):
    path_final = os.path.join(folder, final_name)
    if os.path.exists(path_final):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{prefix}_{ts}.csv"
        backup_path = os.path.join(folder, backup_name)
        try:
            shutil.move(path_final, backup_path)
            print(f"{YELLOW}⚠ Se encontró {final_name}. Movido a backup: {backup_name}{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error moviendo archivo previo a backup: {e}{RESET}")

def eliminar_backups_anteriores(folder=FOLDER, prefix=BACKUP_PREFIX, keep_this_timestamp=None):
    """Elimina backups que coincidan con el prefix, excepto opcionalmente one to keep."""
    patron = os.path.join(folder, f"{prefix}_*.csv")
    archivos = sorted(glob.glob(patron))
    for a in archivos:
        # si se indica uno a mantener, saltarlo
        if keep_this_timestamp and keep_this_timestamp in a:
            continue
        try:
            os.remove(a)
            print(f"{YELLOW}🗑️ Backup eliminado: {os.path.basename(a)}{RESET}")
        except Exception as e:
            print(f"{RED}⚠ No se pudo eliminar backup {a}: {e}{RESET}")

# ----------------------------
# Obtener y parsear página con reintentos
# ----------------------------
def obtener_productos_pagina(session, pagina):
    url = BASE_URL.format(pagina)
    headers = {"User-Agent": USER_AGENT}
    for cycle in range(1, MAX_CYCLES + 1):
        for intento in range(1, RETRY_CYCLE + 1):
            spinner = Spinner(text=f"Analizando página {pagina}")
            try:
                spinner.start()
                resp = session.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
                spinner.stop()
                resp.raise_for_status()
                # parseo
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
                spinner.stop()
                print(f"{YELLOW}⚠ Error req página {pagina} (ciclo {cycle}/{MAX_CYCLES}, intento {intento}/{RETRY_CYCLE}): {e}{RESET}")
                # espera antes de reintentar
                time.sleep(RETRY_WAIT)
                continue
            except Exception as e:
                spinner.stop()
                print(f"{RED}❌ Error parsing página {pagina}: {e}{RESET}")
                return None
        # fin retry cycle
        print(f"{MAGENTA}⏳ Ciclo {cycle} completo sin éxito para página {pagina}. Esperando 60s antes del siguiente ciclo...{RESET}")
        time.sleep(60)
    # agotados ciclos
    print(f"{RED}✖ Agotados reintentos para página {pagina}. Se omitirá.{RESET}")
    return None

# ----------------------------
# Guardado parcial (sobrescribe FINAL_NAME)
# ----------------------------
def guardar_parcial_acumulativo(productos, folder=FOLDER, final_name=FINAL_NAME):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, final_name)
    campos = ["nombre_original", "nombre", "foil", "precio", "url"]
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(productos)
        # animación corta
        spinner = Spinner(text=f"Guardando parcial ({len(productos)} items)")
        spinner.start()
        time.sleep(0.8)
        spinner.stop()
        print(f"{GREEN}💾 Guardado parcial: {path}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}❌ Error guardando parcial: {e}{RESET}")
        return False

# ----------------------------
# Guardado final: crear timestamped final y limpiar backups previos
# ----------------------------
def guardar_final_y_limpiar(productos, folder=FOLDER, prefix=BACKUP_PREFIX):
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_ts_name = f"{prefix}_{ts}.csv"
    final_ts_path = os.path.join(folder, final_ts_name)
    campos = ["nombre_original", "nombre", "foil", "precio", "url"]
    try:
        # escribir archivo timestamped final
        with open(final_ts_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(productos)
        print(f"{GREEN}📁 Guardado final con timestamp: {final_ts_path}{RESET}")
        # eliminar backups anteriores (dejamos solo el nuevo final como backup history cleared)
        eliminar_backups_anteriores(folder=folder, prefix=prefix, keep_this_timestamp=ts)
        # opcional: eliminar el archivo FINAL_NAME si existe (porque ya tenemos final timestamped)
        path_final_constant = os.path.join(folder, FINAL_NAME)
        if os.path.exists(path_final_constant):
            try:
                os.remove(path_final_constant)
            except:
                pass
        return True
    except Exception as e:
        print(f"{RED}❌ Error guardando final: {e}{RESET}")
        return False

# ----------------------------
# Input con timeout (5s)
# ----------------------------
def input_timeout(prompt, timeout=5, default="1"):
    print(f"{CYAN}{prompt}{RESET} (en {timeout}s presiona Enter para usar {default})")
    user_input = []
    ev = threading.Event()
    def read_input():
        try:
            v = input()
            user_input.append(v)
        except:
            pass
        finally:
            ev.set()
    t = threading.Thread(target=read_input)
    t.daemon = True
    t.start()
    ev.wait(timeout)
    if user_input:
        return user_input[0].strip() or default
    else:
        print(f"{YELLOW}⏱ Timeout. Usando {default}{RESET}")
        return default

# ----------------------------
# Scraper principal con ventana de prefetch (mantiene orden)
# ----------------------------
def scrapear_desde(pagina_inicio=1):
    os.makedirs(FOLDER, exist_ok=True)
    # Si existe FINAL_NAME movemos a backup para conservar versión vieja
    mover_actual_a_backup()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    pagina = pagina_inicio
    buffer_products = []        # acumulado de productos para guardado parcial
    buffer_pages = {}           # {page: [productos]} para mantener orden
    submitted = set()           # páginas ya enviadas al executor
    finished = False

    # Heurística para detectar final
    consecutive_empty = 0
    max_consecutive_empty = 5

    print(CASTLE_ART)
    print(f"{CYAN}Iniciando desde la página {pagina_inicio}. Ventana prefetch: {WINDOW_SIZE}. Guardado cada {PAGES_PER_SAVE} páginas.{RESET}")

    with ThreadPoolExecutor(max_workers=WINDOW_SIZE) as executor:
        futures = {}  # future -> page
        # submit initial window
        for p in range(pagina, pagina + WINDOW_SIZE):
            futures[executor.submit(obtener_productos_pagina, session, p)] = p
            submitted.add(p)

        next_to_write = pagina
        pages_processed = 0

        while futures:
            # wait for any future to complete
            for fut in as_completed(list(futures.keys())):
                page = futures.pop(fut)
                try:
                    result = fut.result()
                except Exception as e:
                    result = None
                    print(f"{RED}❌ Excepción en future página {page}: {e}{RESET}")

                # store result (None means omit; [] means empty page)
                buffer_pages[page] = result if result is not None else []
                pages_processed += 1

                # submit next page to keep window moving
                candidate = max(submitted) + 1 if submitted else pagina
                futures[executor.submit(obtener_productos_pagina, session, candidate)] = candidate
                submitted.add(candidate)

                # try to flush ordered pages
                while next_to_write in buffer_pages:
                    page_result = buffer_pages.pop(next_to_write)
                    # handle None/empty/list
                    if page_result is None:
                        # omitted due to fatal parse error -> treat as empty
                        print(f"{YELLOW}🚧 Página {next_to_write} omitida.{RESET}")
                        consecutive_empty += 1
                    elif isinstance(page_result, list) and len(page_result) == 0:
                        print(f"{YELLOW}🔎 Página {next_to_write} vacía.{RESET}")
                        consecutive_empty += 1
                    else:
                        # page has products
                        buffer_products.extend(page_result)
                        print(f"{GREEN}✅ Página {next_to_write} procesada: {len(page_result)} productos (Acumulado: {len(buffer_products)}){RESET}")
                        consecutive_empty = 0

                    # guardado parcial cada PAGES_PER_SAVE páginas (medido por número de páginas procesadas desde inicio)
                    processed_count = next_to_write - pagina_inicio + 1
                    if processed_count % PAGES_PER_SAVE == 0:
                        # guardar acumulativo en FINAL_NAME
                        saved = guardar_parcial_acumulativo(buffer_products)
                        if not saved:
                            print(f"{YELLOW}⚠ Falló guardado parcial para página {next_to_write}.{RESET}")
                        # continue (archivo FINAL_NAME es sobrescrito)
                    # si detectamos demasiadas páginas vacías consecutivas -> asumimos final
                    if consecutive_empty >= max_consecutive_empty:
                        print(f"{YELLOW}⚠ {consecutive_empty} páginas vacías consecutivas -> asumiendo fin.{RESET}")
                        finished = True
                        break
                    next_to_write += 1

                if finished:
                    break

            if finished:
                break

            # Stop condition safety: avoid infinite scheduling; cap candidate to a big number (ej 20000)
            if max(submitted) > 20000:
                print(f"{YELLOW}⚠ Límite de páginas alcanzado ({max(submitted)}). Deteniendo.{RESET}")
                break

        # end while futures

    # al terminar executor, guardar restantes
    if buffer_products:
        guardar_parcial_acumulativo(buffer_products)
    return buffer_products

# ----------------------------
# MAIN
# ----------------------------
def main():
    try:
        print(CASTLE_ART)
        print(f"{BOLD}Bienvenido, cazador. Preparando el ritual...{RESET}\n")
        inp = input_timeout("¿Desde qué página deseas comenzar? (número)", timeout=5, default="1")
        try:
            pagina_inicio = int(inp)
            if pagina_inicio < 1:
                raise ValueError()
        except:
            print(f"{YELLOW}⚠ Entrada inválida. Se usará página 1.{RESET}")
            pagina_inicio = 1

        productos = scrapear_desde(pagina_inicio)

        if not productos:
            print(f"{YELLOW}⚠ No se recolectaron productos. Abortando guardado final.{RESET}")
            return

        # Guardado final y limpieza de backups (solo si todo ok)
        ok_final = guardar_final_y_limpiar(productos)
        if ok_final:
            print(f"{GREEN}🏁 Proceso completado con éxito. Backups anteriores eliminados.{RESET}")
        else:
            print(f"{YELLOW}⚠ Se produjo un problema en el guardado final. Se conservan backups.{RESET}")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏸ Interrumpido por usuario. Los datos parciales permanecen en {os.path.join(FOLDER, FINAL_NAME)}{RESET}")
    except Exception as e:
        print(f"{RED}❌ Error crítico: {e}{RESET}")

if __name__ == "__main__":
    main()
