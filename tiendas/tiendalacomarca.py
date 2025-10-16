import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para TiendaLaComarca ---
def buscar(nombre_producto):
    base_url = "https://www.tiendalacomarca.cl"
    url_busqueda = f"{base_url}/search?type=product&options%5Bprefix%5D=last&q={nombre_producto.replace(' ', '+')}"
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en TiendaLaComarca...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar todos los productos
        productos = soup.select("div.product-card-list2__details")
        encontrado = False

        for prod in productos:
            titulo_tag = prod.select_one("div.grid-view-item__title")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)

            # Verificar coincidencia exacta parcial
            if nombre_producto.lower() not in nombre.lower():
                continue

            # URL del producto
            enlace_a = prod.find_parent("a")
            url_producto = enlace_a['href'] if enlace_a else url_busqueda
            if url_producto.startswith("/"):
                url_producto = base_url + url_producto

            # Verificar si alguna variante está disponible
            opciones = prod.select("select.product-form__variants option")
            disponible = any(opt.get("data-available") == "1" for opt in opciones)

            # Obtener precio real mostrado
            precio_tag = prod.select_one("span.product-price__price.is-bold.qv-regularprice")
            if precio_tag:
                precio_final = precio_tag.get_text(strip=True)
            else:
                precio_final = "-"

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

metadata = { 
    "nombre": "TiendaLaComarca", 
    "func": buscar 
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Meticulous Archive"
    info = buscar(producto)
    print(info)
