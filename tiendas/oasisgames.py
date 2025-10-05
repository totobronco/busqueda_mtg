import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para OasisGames ---
def buscar(nombre_producto):
    base_url = "https://www.oasisgames.cl"
    url_busqueda = base_url + "/search?q={}".format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en OasisGames...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar los productos
        productos = soup.select("div.product-card-list2__details.product-description a div.grid-view-item__title")

        encontrado = False
        for producto_tag in productos:
            nombre = producto_tag.get_text(strip=True)
            if nombre_producto.lower() in nombre.lower():
                link_tag = producto_tag.find_parent("a")
                url_producto = link_tag['href'] if link_tag else url_busqueda
                if url_producto.startswith("/"):
                    url_producto = base_url + url_producto
                
                # Obtener la página del producto para verificar stock
                prod_resp = requests.get(url_producto, headers={"User-Agent": "Mozilla/5.0"})
                prod_soup = BeautifulSoup(prod_resp.content, 'html.parser')
                
                opciones = prod_soup.select("select.product-form__variants option")
                disponible = "No"
                precio = "-"
                
                for opcion in opciones:
                    stock = int(opcion.get("data-stock", "0"))
                    if stock > 0:
                        disponible = "Sí"
                        # Intentar tomar precio
                        precio_tag = prod_soup.select_one("span.product-price__price")
                        if precio_tag:
                            precio = precio_tag.get_text(strip=True)
                        break
                
                resultado = {
                    "Tienda": "OasisGames",
                    "Disponible": disponible,
                    "Producto": nombre,
                    "Precio": precio,
                    "URL": url_producto
                }
                encontrado = True
                break

        if not encontrado:
            resultado = {
                "Tienda": "OasisGames",
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        print(f"\nError: {e}")
        resultado = {
            "Tienda": "OasisGames",
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "OasisGames",
    "func": buscar
}
