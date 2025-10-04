import requests
from bs4 import BeautifulSoup
import re

class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

def buscar(nombre_producto):
    tienda = {
        "nombre": "Magic4Ever",
        "url": "https://www.magic4ever.cl/advanced_search_result.php?keywords={}&x=0&y=0"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        tabla = soup.find("table", {"class": "productListingData"})
        if not tabla:
            raise ValueError("No se encontró la tabla de productos")

        filas = tabla.find_all("tr")
        productos = []

        for fila in filas:
            celdas = fila.find_all("td")
            if len(celdas) < 5:
                continue

            # Extraer título y URL del producto
            titulo_tag = celdas[1].find("a")
            if not titulo_tag:
                continue
            titulo = titulo_tag.get_text(strip=True)
            url_prod = titulo_tag['href']

            # Extraer precio y normalizar a número
            precio_text = celdas[3].get_text(strip=True)
            precio_num = int(re.sub(r"[^\d]", "", precio_text))

            # Revisar disponibilidad
            select_tag = celdas[4].find("select")
            disponible = "No"
            if select_tag:
                if any(int(opt.get("value", "0")) > 0 for opt in select_tag.find_all("option")):
                    disponible = "Sí"

            # Filtrar por nombre buscado (coincidencia parcial, case insensitive)
            if re.search(re.escape(nombre_producto), titulo, re.IGNORECASE):
                productos.append({
                    "Producto": titulo,
                    "Precio": precio_num,
                    "URL": url_prod,
                    "Disponible": disponible
                })

        if not productos:
            resultado = {
                "Tienda": tienda["nombre"],
                "Disponible": "No",
                "Producto": nombre_producto,
                "Precio": "-",
                "URL": url_busqueda
            }
        else:
            # Elegir el más barato entre los disponibles
            productos_disponibles = [p for p in productos if p["Disponible"] == "Sí"]
            if productos_disponibles:
                producto_final = min(productos_disponibles, key=lambda x: x["Precio"])
            else:
                producto_final = min(productos, key=lambda x: x["Precio"])

            resultado = {
                "Tienda": tienda["nombre"],
                "Disponible": producto_final["Disponible"],
                "Producto": producto_final["Producto"],
                "Precio": f"${producto_final['Precio']:,}".replace(",", "."),
                "URL": producto_final["URL"]
            }

    except Exception as e:
        resultado = {
            "Tienda": tienda["nombre"],
            "Disponible": "No",
            "Producto": nombre_producto,
            "Precio": "-",
            "URL": url_busqueda
        }

    print(f"{Colores.VERDE} listo{Colores.RESET}")
    return resultado


# Metadata de la tienda
metadata = {
    "nombre": "Magic4Ever",
    "func": buscar
}

# Ejemplo de uso
if __name__ == "__main__":
    producto = "Anti-Venom"
    resultado = buscar(producto)
    print(resultado)
