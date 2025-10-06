import requests
import csv
import time

BASE_URL = "https://www.tiendalacomarca.cl/collections/mtg-singles/products.json"
CSV_FILE = "productos.csv"

def obtener_productos(pagina):
    """
    Obtiene los productos de la página JSON de Shopify.
    """
    url = f"{BASE_URL}?page={pagina}"
    print(f"\n===== Procesando página {pagina} =====")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error al obtener la página {pagina}: {response.status_code}")
        return []

    data = response.json()
    productos = data.get("products", [])
    print(f"Encontrados {len(productos)} productos en la página {pagina}")
    return productos

def extraer_datos(productos):
    """
    Extrae nombre, precio y URL de cada producto.
    """
    lista = []
    for prod in productos:
        nombre = prod.get("title", "SIN NOMBRE")
        url = f"https://www.tiendalacomarca.cl/products/{prod.get('handle')}"
        
        # Extraer el precio más bajo de las variantes
        variantes = prod.get("variants", [])
        precio_mas_bajo = min([int(v.get("price", 0)) for v in variantes]) if variantes else 0
        precio_formateado = precio_mas_bajo // 100  # dividir por 100 como pediste
        
        lista.append({
            "nombre": nombre,
            "precio": precio_formateado,
            "url": url
        })
    return lista

def guardar_csv(productos):
    """
    Guarda los productos en CSV.
    """
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nombre", "precio", "url"])
        writer.writeheader()
        writer.writerows(productos)
    print(f"\nSe guardaron {len(productos)} productos en {CSV_FILE}")

def main():
    todos_productos = []
    pagina = 1

    while True:
        productos_json = obtener_productos(pagina)
        if not productos_json:
            break
        
        productos_extraidos = extraer_datos(productos_json)
        todos_productos.extend(productos_extraidos)
        print(f"Capturadas {len(productos_extraidos)} cartas en la página {pagina}")
        
        pagina += 1
        time.sleep(1)  # para no saturar el servidor

    guardar_csv(todos_productos)

if __name__ == "__main__":
    main()
