import csv
import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

CARPETA_DB = "DB_Carta"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# ==========================
# FUNCIONES BASE DE DATOS
# ==========================

def listar_archivos(carpeta, extension):
    return [f for f in os.listdir(carpeta) if f.lower().endswith(extension.lower())]

def elegir_archivo(carpeta, extension, mensaje):
    archivos = listar_archivos(carpeta, extension)
    if not archivos:
        print(f"❌ No hay archivos {extension} en '{carpeta}'")
        return None

    print(f"\n📂 Archivos disponibles en '{carpeta}':")
    for i, archivo in enumerate(archivos, 1):
        print(f"  {i}. {archivo}")

    entrada = input(f"\n{mensaje} (puedes dejar vacío para elegir automáticamente): ").strip()

    if entrada == "":
        if len(archivos) == 1:
            print(f"👉 Se seleccionó automáticamente: {archivos[0]}")
            return archivos[0]
        else:
            num = input("Número del archivo: ").strip()
            if num.isdigit() and 1 <= int(num) <= len(archivos):
                return archivos[int(num) - 1]
            return None

    if entrada.isdigit() and 1 <= int(entrada) <= len(archivos):
        return archivos[int(entrada) - 1]

    coincidencias = [a for a in archivos if entrada.lower() in a.lower()]
    if len(coincidencias) == 1:
        print(f"👉 Se encontró coincidencia: {coincidencias[0]}")
        return coincidencias[0]
    elif len(coincidencias) > 1:
        print("⚠️ Varias coincidencias, elige por número:")
        for i, a in enumerate(coincidencias, 1):
            print(f"  {i}. {a}")
        num = input("Número del archivo: ").strip()
        if num.isdigit() and 1 <= int(num) <= len(coincidencias):
            return coincidencias[int(num) - 1]
    else:
        print("❌ No se encontró coincidencia.")
    return None

def extraer_nombre_carta(linea):
    """
    Extrae el nombre de la carta de una línea del TXT.
    Ejemplo de línea: '2 Overkill (FIN) 109' -> 'Overkill'
    """
    try:
        partes = linea.strip().split(' ', 1)
        if len(partes) < 2:
            raise ValueError("No hay nombre")
        nombre = partes[1].split('(')[0].strip()
        if not nombre:
            raise ValueError("Nombre vacío")
        return nombre
    except:
        # Fallback: extraer usando regex, busca la primera palabra con letras
        match = re.search(r'\b([A-Za-z][A-Za-z0-9\'\-]*)\b', linea)
        return match.group(1) if match else None

def cargar_cartas_txt(nombre_txt):
    cartas = set()
    with open(nombre_txt, "r", encoding="utf-8") as f:
        for linea in f:
            nombre = extraer_nombre_carta(linea)
            if nombre:
                cartas.add(nombre)
    return cartas

def actualizar_csv(nombre_csv, cartas_usuario):
    ruta_csv = os.path.join(CARPETA_DB, nombre_csv)

    with open(ruta_csv, "r", encoding="utf-8", newline='') as f:
        lector = csv.reader(f)
        filas = list(lector)

    encabezado = filas[0]

    # Buscar columna 'Nombre' (mayúscula/minúscula)
    col_nombre = None
    for i, h in enumerate(encabezado):
        if h.lower() == "nombre":
            col_nombre = i
            break
    if col_nombre is None:
        print("❌ No se encontró la columna 'Nombre' en el CSV")
        return

    # Agregar columna "Tengo" si no existe
    if "Tengo" not in encabezado:
        encabezado.append("Tengo")
    idx_tengo = encabezado.index("Tengo")

    nuevas_filas = [encabezado]
    for fila in filas[1:]:
        if len(fila) == 0:
            continue

        # Asegurar que la fila tenga suficiente longitud
        while len(fila) <= idx_tengo:
            fila.append("")

        nombre_carta = fila[col_nombre].strip()
        fila[idx_tengo] = "Sí" if nombre_carta in cartas_usuario else "No"

        nuevas_filas.append(fila)

    with open(ruta_csv, "w", encoding="utf-8", newline='') as f:
        escritor = csv.writer(f)
        escritor.writerows(nuevas_filas)

    print(f"\n✅ Base de datos actualizada correctamente en '{ruta_csv}'.")
    return ruta_csv


# ==========================
# FUNCIONES GOOGLE DRIVE
# ==========================

def autenticar_drive():
    try:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Error autenticando con Google Drive: {e}")
        return None

def extraer_id_carpeta(url):
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def subir_a_drive(nombre_archivo, carpeta_url):
    print("\n☁️ Subiendo archivo a Google Drive...")

    carpeta_id = extraer_id_carpeta(carpeta_url)
    if not carpeta_id:
        print("❌ No se pudo extraer el ID de la carpeta. Asegúrate de usar una URL válida de Drive.")
        return

    servicio = autenticar_drive()
    if not servicio:
        print("❌ No se pudo establecer conexión con Google Drive.")
        return

    metadata = {"name": os.path.basename(nombre_archivo), "parents": [carpeta_id]}
    media = MediaFileUpload(nombre_archivo, mimetype="text/csv")

    try:
        archivo = servicio.files().create(body=metadata, media_body=media, fields="id").execute()
        archivo_id = archivo.get("id")
        url_final = f"https://drive.google.com/file/d/{archivo_id}/view"
        print(f"✅ Archivo subido correctamente: {url_final}")
        os.startfile(url_final) if os.name == "nt" else os.system(f"open {url_final}")
    except HttpError as e:
        print(f"❌ Error de Google Drive ({e.resp.status}): {e.error_details}")
    except Exception as e:
        print(f"❌ Error al subir archivo: {e}")

# ==========================
# PROGRAMA PRINCIPAL
# ==========================

def main():
    print("=== ACTUALIZADOR DE BASE DE DATOS DE CARTAS + DRIVE ===")

    nombre_txt = elegir_archivo(".", ".txt", "📘 Ingresa el nombre o número del archivo TXT con tus cartas")
    if not nombre_txt:
        return

    nombre_csv = elegir_archivo(CARPETA_DB, ".csv", "📗 Ingresa el nombre o número del archivo CSV a actualizar")
    if not nombre_csv:
        return

    # Cargar cartas del TXT
    cartas_usuario = cargar_cartas_txt(nombre_txt)
    print(f"\n📜 Cartas detectadas en TXT: {len(cartas_usuario)}")

    # Actualizar CSV
    ruta_csv = actualizar_csv(nombre_csv, cartas_usuario)
    if not ruta_csv:
        return

    # Preguntar si subir a Drive
    subir = input("\n☁️ ¿Deseas subir el archivo actualizado a Google Drive? (s/n): ").strip().lower()
    if subir == "s":
        carpeta_url = input("📂 Ingresa la URL de la carpeta en Drive: ").strip()
        subir_a_drive(ruta_csv, carpeta_url)

if __name__ == "__main__":
    main()
