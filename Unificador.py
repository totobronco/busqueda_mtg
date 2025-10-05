import os
import csv
import re
from datetime import datetime

CARPETA = "Ficheros"

def detectar_foil(nombre_original):
    """Detecta si el nombre tiene 'Foil' entre paréntesis (case-insensitive)"""
    if not nombre_original:
        return "No"
    match = re.search(r"\(([^)]*foil[^)]*)\)", nombre_original, flags=re.I)
    return "Sí" if match else "No"

def unificar_csv():
    archivos = [f for f in os.listdir(CARPETA) if f.startswith("List_") and f.endswith(".csv")]
    todos_los_registros = []
    columnas_final = ["archivo_origen", "nombre_original", "nombre", "foil", "precio", "url"]

    for archivo in archivos:
        print(f"📂 Leyendo archivo: {archivo}...")
        ruta = os.path.join(CARPETA, archivo)
        with open(ruta, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for fila in reader:
                registro = {}
                registro["archivo_origen"] = archivo
                registro["nombre_original"] = fila.get("nombre_original") or fila.get("nombre") or ""
                registro["nombre"] = fila.get("nombre") or registro["nombre_original"]

                # Detectar foil si no existe la columna
                if "foil" in fila:
                    registro["foil"] = fila["foil"] or detectar_foil(registro["nombre_original"])
                else:
                    registro["foil"] = detectar_foil(registro["nombre_original"])

                registro["precio"] = fila.get("precio", "")
                registro["url"] = fila.get("url", "")

                todos_los_registros.append(registro)
        print(f"✅ Archivo leído: {archivo}\n")

    # Guardar CSV unificado
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    archivo_unificado = os.path.join(CARPETA, f"List-Unificado_{fecha}.csv")
    with open(archivo_unificado, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas_final)
        writer.writeheader()
        writer.writerows(todos_los_registros)

    print(f"🟢 CSV unificado creado: {archivo_unificado}")
    print(f"📌 Total de registros: {len(todos_los_registros)}")

if __name__ == "__main__":
    unificar_csv()
