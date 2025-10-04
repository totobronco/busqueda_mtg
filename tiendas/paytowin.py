import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para PayToWin ---
def buscar(nombre_producto):
    base_url = "https://www.paytowin.cl"
    url_busqueda = f"{base_url}/search?page=1&q={nombre_producto.replace(' ', '%20')}"
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en PayToWin...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        productos = soup.select("div.productCard__card")
        encontrado = False

        for prod in productos:
            titulo_tag = prod.select_one("p.productCard__title a")
            if not titulo_tag:
                continue
            nombre = titulo_tag.get_text(strip=True)

            # Hacemos match con la palabra buscada
            if nombre_producto.lower() in nombre.lower():
                url_producto = titulo_tag['href']
                if url_producto.startswith("/"):
                    url_producto = base_url + url_producto

                precio_tag = prod.select_one("p.productCard__price")
                precio = precio_tag.get_text(strip=True) if precio_tag else "-"

                # Comprobamos disponibilidad
                disponible = "Sí"
                boton_tag = prod.select_one("div.productCard__button")
                if boton_tag and "Out of Stock" in boton_tag.get_text():
                    disponible = "No"

                resultado = {
                    "Tienda": "PayToWin",
                    "Disponible": disponible,
                    "Producto": nombre,
                    "Precio": precio,
                    "URL": url_producto
                }
                encontrado = True
                break

        if not encontrado:
            resultado = {
                "Tienda": "PayToWin",
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        resultado = {
            "Tienda": "PayToWin",
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "PayToWin",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Prosperous Innkeeper"
    info = buscar(producto)
    print(info)
