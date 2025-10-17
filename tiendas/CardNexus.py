import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para CardNexus ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "CardNexus",
        "url": "https://cardnexus.cl/?s={}"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.select("ul.products li.product")

        encontrado = False
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto in productos:
            titulo_tag = producto.select_one("h2.woocommerce-loop-product__title")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # Extraer precio
                precio_tag = producto.select_one("span.woocommerce-Price-amount bdi")
                if precio_tag:
                    precio = precio_tag.get_text(strip=True)
                else:
                    precio = "-"

                # Extraer URL
                url_tag = producto.select_one("a.woocommerce-LoopProduct-link")
                if url_tag:
                    url_producto = url_tag['href']
                else:
                    url_producto = url_busqueda

                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": "Sí",  # CardNexus no indica agotado en el listado
                    "Producto": nombre,
                    "Precio": precio,
                    "URL": url_producto
                }
                encontrado = True
                break

        if not encontrado:
            resultado = {
                "Tienda": tienda['nombre'],
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        resultado = {
            "Tienda": tienda['nombre'],
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado


# --- Metadata de la tienda ---
metadata = {
    "nombre": "CardNexus",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Adric, Mathematical Genius"
    info = buscar(producto)
    print(info)
