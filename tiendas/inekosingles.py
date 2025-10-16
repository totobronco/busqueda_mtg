import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para Inekosingles ---
def buscar(nombre_producto):
    base_url = "https://inekosingles.com"
    url_busqueda = f"{base_url}/search?q={nombre_producto.replace(' ', '+')}"
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en Inekosingles...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        productos = soup.select("li.grid__item")
        encontrado = False
        precio_menor = None
        mejor_producto = {}
        hay_disponible = False

        for prod in productos:
            titulo_tag = prod.select_one("h3.card__heading a")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)
            url_producto = titulo_tag['href']
            if url_producto.startswith("/"):
                url_producto = base_url + url_producto

            # Extraer precio
            precio_tag = prod.select_one("span.price-item.price-item--regular")
            precio = precio_tag.get_text(strip=True) if precio_tag else "-"
            precio_valor = None
            if precio != "-":
                precio_valor = int(precio.replace("$", "").replace("CLP", "").replace(".", "").strip())

            # Verificar disponibilidad (robusto, ignora mayúsculas y espacios)
            agotado_tag = prod.select_one(".badge, .price--sold-out")
            disponible = "Sí"
            if agotado_tag and "agotado" in agotado_tag.get_text(strip=True).lower():
                disponible = "No"

            # Solo productos que coincidan en nombre
            if nombre_producto.lower() in nombre.lower():
                encontrado = True
                if disponible == "Sí":
                    hay_disponible = True
                    # Guardar el de precio más bajo
                    if precio_valor is not None:
                        if precio_menor is None or precio_valor < precio_menor:
                            precio_menor = precio_valor
                            mejor_producto = {
                                "Tienda": "Inekosingles",
                                "Disponible": disponible,
                                "Producto": nombre,
                                "Precio": precio,
                                "URL": url_producto
                            }

        # Resultado final
        if encontrado:
            if hay_disponible:
                resultado = mejor_producto
            else:
                resultado = {
                    "Tienda": "Inekosingles",
                    "Disponible": "No",
                    "Producto": nombre_producto,
                    "Precio": "-",
                    "URL": url_busqueda
                }
        else:
            resultado = {
                "Tienda": "Inekosingles",
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }

    except Exception as e:
        resultado = {
            "Tienda": "Inekosingles",
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado

# --- Metadata de la tienda ---
metadata = {
    "nombre": "Inekosingles",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Xu-Ifit, Osteoharmonist"
    info = buscar(producto)
    print(info)
