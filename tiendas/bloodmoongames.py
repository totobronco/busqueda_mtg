import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para BloodMoonGames ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "BloodMoonGames",
        "url": "https://bloodmoongames.cl/?post_type=product&s={}&product_cat="
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        texto_pagina = soup.get_text()

        if "No se encontraron productos que concuerden con la selección." in texto_pagina:
            resultado = {"Tienda": tienda['nombre'], "Disponible": "No", "Producto": nombre_producto, "Precio": "-", "URL": url_busqueda}
        else:
            nombre = soup.select_one("h1.product_title.entry-title")
            precio = soup.select_one("p.price span.woocommerce-Price-amount")
            if nombre and precio:
                resultado = {"Tienda": tienda['nombre'], "Disponible": "Sí", "Producto": nombre.get_text(strip=True), "Precio": precio.get_text(strip=True), "URL": url_busqueda}
            else:
                resultado = {"Tienda": tienda['nombre'], "Disponible": "No", "Producto": nombre_producto, "Precio": "-", "URL": url_busqueda}
    except Exception as e:
        resultado = {"Tienda": tienda['nombre'], "Disponible": "No", "Producto": nombre_producto, "Precio": "-", "URL": url_busqueda}

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "BloodMoonGames",
    "func": buscar
}
