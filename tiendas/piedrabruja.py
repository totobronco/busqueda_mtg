import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para PiedraBruja ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "PiedraBruja",
        "url": "https://piedrabruja.cl/search?type=product&q={}"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        productos = soup.select("div.product-item__info a.product-item__title")
        encontrado = False

        for producto_tag in productos:
            nombre = producto_tag.get_text(strip=True)
            if nombre_producto.lower() in nombre.lower():
                url_producto = "https://piedrabruja.cl" + producto_tag['href']
                precio_tag = producto_tag.find_next("span", class_="price")
                precio = precio_tag.get_text(strip=True) if precio_tag else "-"
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
    "nombre": "PiedraBruja",
    "func": buscar
}
