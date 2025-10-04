import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para TiendaLaComarca ---
def buscar(nombre_producto):
    base_url = "https://www.tiendalacomarca.cl"
    url_busqueda = base_url + "/search?type=product&options%5Bprefix%5D=last&q={}".format(
        nombre_producto.replace(' ', '+')
    )
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en TiendaLaComarca...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar todos los productos
        productos = soup.select("div.product-card-list2__details div.grid-view-item__title")
        encontrado = False

        # Normalizar palabras de búsqueda
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto_tag in productos:
            nombre = producto_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            # Verificar que todas las palabras de búsqueda estén en el título
            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # URL del producto
                enlace_a = producto_tag.find_parent("a")
                url_producto = enlace_a['href'] if enlace_a else url_busqueda
                if url_producto.startswith("/"):
                    url_producto = base_url + url_producto

                # Buscar variantes y precios disponibles
                producto_parent = producto_tag.find_parent("div.product-card-list2__details")
                variantes = producto_parent.select("select.product-form__variants option")

                precios_disponibles = []

                for v in variantes:
                    if v.get("data-available") == "1":
                        precio_str = v.get("data-price", "0").replace("$", "").replace(",", "").strip()
                        try:
                            precio = int(precio_str)
                            precios_disponibles.append(precio)
                        except:
                            continue

                if precios_disponibles:
                    precio_final = f"${min(precios_disponibles)}"
                    disponible = True
                else:
                    precio_final = "-"
                    disponible = False

                resultado = {
                    "Tienda": "TiendaLaComarca",
                    "Disponible": "Sí" if disponible else "No",
                    "Producto": nombre,
                    "Precio": precio_final,
                    "URL": url_producto
                }
                encontrado = True
                break

        if not encontrado:
            resultado = {
                "Tienda": "TiendaLaComarca",
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        resultado = {
            "Tienda": "TiendaLaComarca",
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "TiendaLaComarca",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "The Endstone"
    info = buscar(producto)
    print(info)
