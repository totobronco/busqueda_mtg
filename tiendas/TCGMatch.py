import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para TCGMatch ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "TCGMatch",
        "url": "https://tcgmatch.cl/cartas/busqueda/palabra={}"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        # <-- Cambio aquí: seleccionar todos los links de productos -->
        productos = soup.select("section[aria-labelledby='products'] a")

        encontrado = False
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto in productos:
            nombre_tag = producto.select_one("p.text-base.font-semibold")
            if not nombre_tag:
                continue

            nombre = nombre_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # Extraer precio
                precio_tag = producto.select_one("p.text-xl.font-semibold.text-green-600")
                if precio_tag:
                    precio = precio_tag.get_text(strip=True)
                else:
                    precio = "-"

                # Extraer URL completa
                url_producto = "https://tcgmatch.cl" + producto['href']

                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": "Sí",
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
    "nombre": "TCGMatch",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Geode Golem"
    info = buscar(producto)
    print(info)
