import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para GameOfMagicSingles ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "GameOfMagicSingles",
        "url": "https://gameofmagicsingles.cl/search?page=1&q={}"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        productos = soup.select("div.productCard__card")

        encontrado = False
        palabras_busqueda = re.findall(r'\w+', nombre_producto.lower())

        for producto in productos:
            titulo_tag = producto.select_one("p.productCard__title a")
            if not titulo_tag:
                continue

            nombre = titulo_tag.get_text(strip=True)
            palabras_titulo = re.findall(r'\w+', nombre.lower())

            if all(palabra in palabras_titulo for palabra in palabras_busqueda):
                # Revisar stock de variantes
                variantes = producto.select("li.productChip")
                precios_disponibles_foil = []
                precios_disponibles_normal = []

                for v in variantes:
                    if v.get("data-variantavailable") == "true":
                        precio_raw = v.get("data-variantprice", "0").replace("$", "").replace(",", "").strip()
                        try:
                            precio = int(precio_raw) // 100  # convertir a pesos
                        except:
                            continue

                        # Priorizar foil
                        if "Foil" in v.get("data-varianttitle", ""):
                            precios_disponibles_foil.append(precio)
                        else:
                            precios_disponibles_normal.append(precio)

                # Si hay foil disponible, usar el más barato
                if precios_disponibles_foil:
                    precio_final = f"${min(precios_disponibles_foil):,} CLP"
                elif precios_disponibles_normal:
                    precio_final = f"${min(precios_disponibles_normal):,} CLP"
                else:
                    # No hay stock en ninguna variante
                    continue

                url_producto = "https://gameofmagicsingles.cl" + titulo_tag['href']
                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": "Sí",
                    "Producto": nombre,
                    "Precio": precio_final,
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
    "nombre": "GameOfMagicSingles",
    "func": buscar
}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    producto = "Elvish Mystic"
    info = buscar(producto)
    print(info)
