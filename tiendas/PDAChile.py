import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para PDAChile ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "PDAChile",
        "url": "https://www.pdachile.cl/search?q={}"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.select("div.product-block")

        encontrado = False
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto in productos:
            titulo_tag = producto.select_one("div.post-prev-title a")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            # Verifica que todas las palabras del nombre buscado estén en el título
            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # Extraer precio
                precio_tag = producto.select_one("div.post-prev-text strong")
                if precio_tag:
                    precio = precio_tag.get_text(strip=True)
                else:
                    precio = "-"

                # Construir URL completa
                url_producto = "https://www.pdachile.cl" + titulo_tag['href']

                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": "Sí",  # PDAChile no marca agotado en la estructura que me diste
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
    "nombre": "PDAChile",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Sanguine Bond"
    info = buscar(producto)
    print(info)
