import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para AFKStore ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "AFKStore",
        "url": "https://www.afkstore.cl/search?q={}&options%5Bprefix%5D=last"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.select("li.grid__item")

        encontrado = False
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto in productos:
            titulo_tag = producto.select_one("h3.card__heading a.full-unstyled-link")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            # Verifica que todas las palabras del nombre buscado estén en el título
            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # Extraer precio
                precio_tag = producto.select_one(".price-item--sale, .price-item--regular")
                if precio_tag:
                    precio = precio_tag.get_text(strip=True)
                else:
                    precio = "-"

                # Detectar si está agotado
                agotado_tag = producto.select_one(".badge")
                disponible = "No" if (agotado_tag and "Agotado" in agotado_tag.get_text()) else "Sí"

                # Construir URL completa
                url_producto = "https://www.afkstore.cl" + titulo_tag['href']

                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": disponible,
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
    "nombre": "AFKStore",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Sanguine Bond"
    info = buscar(producto)
    print(info)
