import os
import csv
from datetime import datetime
from tiendas import tiendas

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    GRIS = '\033[90m'
    RESET = '\033[0m'

# --- Función para mostrar resultados ---
def mostrar_resultados(resultados):
    if not resultados:
        print("No se encontraron resultados.")
        return

    disponibles = [r for r in resultados if r['Disponible'] == "Sí"]
    no_disponibles = [r for r in resultados if r['Disponible'] != "Sí"]

    # Mostrar disponibles
    if disponibles:
        print("\n✅ Disponibles:")

        # Buscar precio mínimo
        precios = []
        for r in disponibles:
            precio_num = int(''.join(filter(str.isdigit, r['Precio']))) if r['Precio'] != "-" else float('inf')
            precios.append(precio_num)
        precio_min = min(precios)

        # Mostrar disponibles, resaltando el más económico
        for r in disponibles:
            precio_num = int(''.join(filter(str.isdigit, r['Precio']))) if r['Precio'] != "-" else float('inf')
            color = Colores.VERDE if precio_num == precio_min else Colores.GRIS
            simbolo = "💰" if precio_num == precio_min else "  "
            print(f"{color}{simbolo} {r['Tienda']} | {r['Producto']} | {r['Precio']} | {r['URL']}{Colores.RESET}")

    # Mostrar no disponibles
    if no_disponibles:
        print("\n❌ No disponibles:")
        for r in no_disponibles:
            print(f"   {r['Tienda']} | {r['Producto']} | {r['Precio']} | {r['URL']}")

# --- Función para obtener mejor opción por precio ---
def obtener_mejor_precio(resultados):
    disponibles = [r for r in resultados if r['Disponible'] == "Sí" and r['Precio'] != "-"]
    if not disponibles:
        return None
    mejor = min(disponibles, key=lambda r: int(''.join(filter(str.isdigit, r['Precio']))))
    return mejor

# --- Preguntar si desea buscar 1 carta o varias ---
while True:
    opcion = input("¿Desea buscar 1 carta o varias? (1/+): ").strip()
    if opcion in ("1", "+"):
        break
    else:
        print("Por favor ingrese '1' para una carta o '+' para varias cartas.")

# --- Buscar 1 carta ---
if opcion == "1":
    carta = input("Ingrese el nombre de la carta: ").strip()
    resultados = []
    for tienda in tiendas:
        resultado = tienda["func"](carta)
        resultados.append(resultado)
    mostrar_resultados(resultados)

# --- Buscar varias cartas desde buscar.txt ---
else:
    try:
        with open("buscar.txt", "r", encoding="utf-8") as f:
            cartas = [line.strip() for line in f if line.strip()]

        # Preguntar cada cuántas cartas pausar
        while True:
            pausa = input("¿Cada cuántas cartas desea pausar? (Ingrese un número >0 o '-' para todas): ").strip()
            if pausa == "-":
                batch_size = len(cartas)
                break
            elif pausa.isdigit() and int(pausa) > 0:
                batch_size = int(pausa)
                break
            else:
                print("Entrada inválida. Ingrese un número mayor que 0 o '-'.")

        # Crear carpeta Ficheros si no existe
        os.makedirs("Ficheros", exist_ok=True)

        # Preparar datos para CSV
        datos_csv = []

        for i in range(0, len(cartas), batch_size):
            batch = cartas[i:i+batch_size]
            for carta in batch:
                print(f"\nBuscando: {carta}")
                resultados = []
                for tienda in tiendas:
                    resultado = tienda["func"](carta)
                    resultados.append(resultado)
                mostrar_resultados(resultados)

                mejor = obtener_mejor_precio(resultados)
                if mejor:
                    datos_csv.append({
                        "Nombre de la carta": carta,
                        "Tienda": mejor["Tienda"],
                        "Precio": mejor["Precio"],
                        "URL": mejor["URL"]
                    })

            # Pausar después de cada batch si hay más cartas y la opción no es "-"
            if batch_size != len(cartas) and i + batch_size < len(cartas):
                while True:
                    continuar = input("\nDesea continuar con el siguiente batch de cartas? [S/N]: ").strip().upper()
                    if continuar == "S":
                        break
                    elif continuar == "N":
                        # Guardar CSV antes de salir
                        if datos_csv:
                            now = datetime.now()
                            fecha = now.strftime("%Y-%m-%d")
                            hora = now.strftime("%H-%M")
                            nombre_archivo = f"Ficheros/Ficha_Cartas_{len(datos_csv)}____{fecha}___{hora}.csv"

                            with open(nombre_archivo, "w", newline="", encoding="utf-8") as f:
                                writer = csv.DictWriter(f, fieldnames=["Nombre de la carta", "Tienda", "Precio", "URL"])
                                writer.writeheader()
                                writer.writerows(datos_csv)

                            print(f"\n✅ Datos guardados en: {nombre_archivo}")
                        exit()
                    else:
                        print("Ingrese 'S' para continuar o 'N' para detener y guardar.")

        # Guardar CSV al final si llegó al último batch
        if datos_csv:
            now = datetime.now()
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H-%M")
            nombre_archivo = f"Ficheros/Ficha_Cartas_{len(datos_csv)}____{fecha}___{hora}.csv"

            with open(nombre_archivo, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Nombre de la carta", "Tienda", "Precio", "URL"])
                writer.writeheader()
                writer.writerows(datos_csv)

            print(f"\n✅ Datos guardados en: {nombre_archivo}")

    except FileNotFoundError:
        print("No se encontró el archivo 'buscar.txt'. Asegúrese de que exista en el mismo directorio.")
