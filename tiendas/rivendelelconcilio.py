import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para Rivendel El Concilio ---
def buscar(nombre_producto):
    base_url = "https://www.rivendelelconcilio.cl"
    url_busqueda = base_url + "/search?q={}".format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en Rivendel El Concilio...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.select("div.product-block")

        encontrado = False

        for producto_tag in productos:
            nombre_tag = producto_tag.select_one("div.brand-name h3 a")
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else ""
            
            # Verificar si coincide con lo que buscamos
            if nombre_producto.lower() in nombre.lower():
                # URL del producto
                url_producto = nombre_tag['href'] if nombre_tag else url_busqueda
                if url_producto.startswith("/"):
                    url_producto = base_url + url_producto

                # Entrar a la página del producto para analizar variantes
                resp_prod = requests.get(url_producto, headers={"User-Agent": "Mozilla/5.0"})
                soup_prod = BeautifulSoup(resp_prod.content, 'html.parser')

                opciones = soup_prod.select("select.prod-options option")
                stock_opciones = []

                for op in opciones:
                    nombre_op = op.get_text(strip=True).lower()
                    stock = int(op.get("data-variant-stock", "0"))
                    precio_tag = soup_prod.select_one("span.product-form_price")
                    precio = precio_tag.get_text(strip=True).replace("$","").replace("CLP","").replace(".","").strip() if precio_tag else "0"
                    try:
                        precio = int(precio)
                    except:
                        precio = 0
                    stock_opciones.append({
                        "nombre_op": nombre_op,
                        "stock": stock,
                        "precio": precio
                    })

                # Priorizar Inglés Foil > Inglés
                seleccion = None
                for op_name in ["ingles foil", "ingles"]:
                    disponibles = [o for o in stock_opciones if o["nombre_op"] == op_name and o["stock"] > 0]
                    if disponibles:
                        # Elegir la opción con menor precio
                        seleccion = min(disponibles, key=lambda x: x["precio"])
                        break

                if seleccion:
                    resultado = {
                        "Tienda": "Rivendel El Concilio",
                        "Disponible": "Sí",
                        "Producto": nombre,
                        "Opcion": seleccion["nombre_op"],
                        "Precio": f"${seleccion['precio']}",
                        "URL": url_producto
                    }
                else:
                    resultado = {
                        "Tienda": "Rivendel El Concilio",
                        "Disponible": "No",
                        "Producto": nombre,
                        "Opcion": "-",
                        "Precio": "-",
                        "URL": url_producto
                    }

                encontrado = True
                break

        if not encontrado:
            resultado = {
                "Tienda": "Rivendel El Concilio",
                "Disponible": "No",
                "Producto": nombre_producto,
                "Opcion": "-",
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        resultado = {
            "Tienda": "Rivendel El Concilio",
            "Disponible": "No",
            "Producto": nombre_producto,
            "Opcion": "-",
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "Rivendel El Concilio",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Overzealous Muscle"
    info = buscar(producto)
    print(info)
