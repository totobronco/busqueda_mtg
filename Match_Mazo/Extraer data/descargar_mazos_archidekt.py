import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.prompt import Prompt

console = Console()

def obtener_nombre_unico(ruta_archivo):
    if not os.path.exists(ruta_archivo):
        return ruta_archivo
    base, extension = os.path.splitext(ruta_archivo)
    contador = 1
    nuevo_nombre = f"{base} ({contador}){extension}"
    while os.path.exists(nuevo_nombre):
        contador += 1
        nuevo_nombre = f"{base} ({contador}){extension}"
    return nuevo_nombre

def esperar_y_renombrar_descarga(ruta_dir, lista_archivos_antes):
    tiempo_inicio = time.time()
    while time.time() - tiempo_inicio < 25:
        archivos_ahora = os.listdir(ruta_dir)
        nuevos = [f for f in archivos_ahora if f not in lista_archivos_antes and not f.endswith('.crdownload')]
        if nuevos:
            archivo_final = nuevos[0]
            ruta_original = os.path.join(ruta_dir, archivo_final)
            ruta_unica = obtener_nombre_unico(ruta_original)
            if ruta_original != ruta_unica:
                os.rename(ruta_original, ruta_unica)
                return os.path.basename(ruta_unica)
            return archivo_final
        time.sleep(0.5)
    return None

def ejecutar_extractor():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    console.print(Panel.fit(
        "[bold magenta]MAGIC: THE GATHERING[/bold magenta]\n[bold white]Archidekt Deck Downloader v2.3[/bold white]",
        border_style="orange3",
        subtitle="[italic]Grand Archive Edition - 2s Delay[/italic]",
        padding=(1, 2)
    ))

    url_busqueda = Prompt.ask("[bold cyan]➤ Pega la URL de búsqueda[/bold cyan]").strip()
    
    ruta_descarga = os.getcwd()
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    prefs = {"download.default_directory": ruta_descarga, "download.prompt_for_download": False}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ruta_descarga})
    wait = WebDriverWait(driver, 15)

    try:
        # Spinner estándar: 'dots'
        with console.status("[bold yellow]Invocando la lista de mazos...", spinner="dots"):
            driver.get(url_busqueda)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "deckLink_deckNameContainer__Uk1q8")))
            links = driver.find_elements(By.CSS_SELECTOR, ".deckLink_deckNameContainer__Uk1q8 a")
            urls_mazos = [link.get_attribute('href') for link in links]

        console.print(f"[bold green]✔[/bold green] Conexión establecida. [bold white]{len(urls_mazos)}[/bold white] mazos localizados.\n")

        # Columnas de progreso corregidas
        with Progress(
            SpinnerColumn("dots"), # Nombre de animación real
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, pulse_style="bright_magenta"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task_total = progress.add_task("[cyan]Extrayendo datos...", total=len(urls_mazos))

            for i, url in enumerate(urls_mazos, 1):
                exito = False
                intentos_max = 2 
                
                for intento in range(intentos_max):
                    try:
                        progress.update(task_total, description=f"[cyan]Mazo {i}/{len(urls_mazos)}")
                        driver.get(url)
                        time.sleep(2) # Pausa inicial de 2 segundos

                        archivos_antes = os.listdir(ruta_descarga)

                        # 1. Extras
                        btn_extras = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Extras')]")))
                        driver.execute_script("arguments[0].click();", btn_extras)
                        time.sleep(2) # Pausa de 2 segundos

                        # 2. Export
                        btn_export = wait.until(EC.presence_of_element_located((By.ID, "dropdown-index-0")))
                        driver.execute_script("arguments[0].click();", btn_export)
                        time.sleep(2) # Pausa de 2 segundos

                        # 3. Download
                        xpath_download = "//button[contains(., 'Download') and contains(@class, 'phatButton_green')]"
                        btn_download = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_download)))
                        driver.execute_script("arguments[0].click();", btn_download)
                        
                        nombre_final = esperar_y_renombrar_descarga(ruta_descarga, archivos_antes)
                        
                        if nombre_final:
                            console.print(f"   [bold green]✓[/bold green] [italic]{nombre_final}[/italic]")
                            exito = True
                            break 
                        
                    except Exception:
                        if intento < intentos_max - 1:
                            console.print(f"   [bold yellow]↻[/bold yellow] Interferencia detectada. Reintentando mazo {i}...")
                            time.sleep(3)
                        else:
                            console.print(f"   [bold red]⚠[/bold red] Mazo {i} perdido en el vacío multiversal.")
                
                progress.advance(task_total)
                time.sleep(1)

        console.print("\n[bold green]✨ MISIÓN CUMPLIDA ✨[/bold green]\n[white]Todos los grimorios han sido archivados correctamente.[/white]")

    finally:
        driver.quit()

if __name__ == "__main__":
    ejecutar_extractor()