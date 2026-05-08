import re
import pandas as pd
import os
import time
from datetime import datetime
from colorama import Fore, Style, init

# Inicializar colorama para terminales
init(autoreset=True)

def animacion_carga(mensaje):
    print(f"{Fore.CYAN}{mensaje}", end="")
    for _ in range(3):
        time.sleep(0.3)
        print(".", end="", flush=True)
    print(Style.RESET_ALL)

def limpiar_nombre_estricto(linea):
    if "[Maybeboard" in linea:
        return None
    # Limpieza de metadatos de MTG
    linea = re.sub(r'^\d+x\s+', '', linea)
    linea = re.sub(r'\(.*?\)', '', linea)
    linea = re.sub(r'\[.*?\]', '', linea)
    linea = re.sub(r'\^.*?\^', '', linea)
    linea = linea.replace('*F*', '')
    # Eliminar códigos de set y números al final (ej: 139 o LRW-167)
    linea = re.sub(r'\s+([A-Z0-9]+-\d+|\d+)\s*$', '', linea)
    return linea.strip()

def obtener_nombre_comandante(lineas):
    """Extrae el nombre de la línea que contiene [Commander{top}]."""
    for linea in lineas:
        if "[Commander{top}]" in linea:
            nombre = limpiar_nombre_estricto(linea)
            # Eliminar caracteres prohibidos en nombres de archivos
            nombre = re.sub(r'[\\/*?:"<>|]', '', nombre)
            return nombre
    return "Mazo_Commander"

def procesar_archivo_mtg(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        nombres_limpios = []
        comandante = obtener_nombre_comandante(lineas)
        
        for l in lineas:
            n = limpiar_nombre_estricto(l)
            if n: nombres_limpios.append(n)
            
        # Sobreescribir el TXT con los nombres limpios
        with open(ruta, 'w', encoding='utf-8') as f:
            for n in nombres_limpios: f.write(n + '\n')
            
        return nombres_limpios, comandante
    except Exception as e:
        print(f"{Fore.RED}Error al procesar {ruta}: {e}")
        return [], None

def mostrar_tabla_resultados(df):
    if df.empty: return
    print(f"\n{Fore.MAGENTA}{'='*45}")
    print(f"{Fore.WHITE}{'CARTA MÁS JUGADA':<35} | {'MATCH'}")
    print(f"{Fore.MAGENTA}{'='*45}")
    # Ordenar para la consola
    top = df[df['match'] > 0].sort_values(by='match', ascending=False).head(15)
    for _, row in top.iterrows():
        color = Fore.GREEN if row['match'] > 1 else Fore.WHITE
        print(f"{color}{row['Nombre']:<35} | {row['match']}")
    print(f"{Fore.MAGENTA}{'='*45}\n")

def main():
    print(f"{Fore.GREEN}╔════════════════════════════════════════════╗")
    print(f"{Fore.GREEN}║    MTG COMMANDER - ANALIZADOR DE MAZOS     ║")
    print(f"{Fore.GREEN}╚════════════════════════════════════════════╝")
    
    while True:
        modo = input(f"{Fore.YELLOW}¿Quieres hacer una comparación de 1 a 1? (Y/N): ").strip().upper()
        if modo in ['Y', 'N']: break
        print(f"{Fore.RED}Opción inválida.")

    # Formato de fecha y hora solicitado: (DD-MM-YYYY - HH mm)
    fecha_formateada = datetime.now().strftime("%d-%m-%Y - %H %M")
    nombre_csv_final = ""
    primer_ciclo = True

    if modo == 'N':
        # --- MODO BATCH (Carpeta Listas) ---
        ruta_folder = "Listas"
        if not os.path.exists(ruta_folder):
            print(f"{Fore.RED}La carpeta 'Listas' no existe."); return
        
        archivos = [f for f in os.listdir(ruta_folder) if f.endswith('.txt')]
        if not archivos:
            print(f"{Fore.RED}No hay archivos .txt en la carpeta."); return

        animacion_carga("Iniciando escaneo de la carpeta Listas")
        resultados = {}
        cmd_name = "Global_Match"

        for i, arc in enumerate(archivos):
            nombres, cmd = procesar_archivo_mtg(os.path.join(ruta_folder, arc))
            if i == 0:
                cmd_name = cmd if cmd else cmd_name
                resultados = {n: 0 for n in nombres}
            else:
                for n in nombres:
                    if n in resultados: resultados[n] += 1
                    else: resultados[n] = 0
            print(f"{Fore.BLUE}✔ Analizado: {arc}")

        nombre_csv_final = f"{cmd_name} ({fecha_formateada}).csv"
        df = pd.DataFrame(list(resultados.items()), columns=['Nombre', 'match'])
        df.to_csv(nombre_csv_final, index=False, encoding='utf-8-sig')
        
        mostrar_tabla_resultados(df)
        print(f"{Fore.CYAN}Proceso completo. Archivo guardado: {nombre_csv_final}")

    else:
        # --- MODO 1 A 1 ---
        while True:
            animacion_carga("Comparando cartas actuales")
            nombres_alfa, cmd_alfa = procesar_archivo_mtg('Lista_Alfa.txt')
            nombres_data, _ = procesar_archivo_mtg('Lista_Data.txt')

            if primer_ciclo:
                nombre_csv_final = f"{cmd_alfa} ({fecha_formateada}).csv"
                resultados = {n: 0 for n in nombres_alfa}
                primer_ciclo = False
            else:
                df_prev = pd.read_csv(nombre_csv_final)
                resultados = dict(zip(df_prev['Nombre'], df_prev['match']))

            for n in nombres_data:
                if n in resultados: resultados[n] += 1
                else: resultados[n] = 0

            df_final = pd.DataFrame(list(resultados.items()), columns=['Nombre', 'match'])
            df_final.to_csv(nombre_csv_final, index=False, encoding='utf-8-sig')
            
            mostrar_tabla_resultados(df_final)
            print(f"{Fore.CYAN}Sobreescrito en: {nombre_csv_final}")

            while True:
                resp = input(f"{Fore.YELLOW}¿Realizar otra comparación manual? (Y/N): ").strip().upper()
                if resp == 'Y': break
                elif resp == 'N':
                    print(f"{Fore.GREEN}¡Proceso finalizado con éxito!")
                    return
                else: print("Usa Y o N.")

if __name__ == "__main__":
    main()