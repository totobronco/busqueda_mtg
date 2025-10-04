import requests
from bs4 import BeautifulSoup

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

# --- Función de búsqueda para HunterCardTCG ---
def buscar(nombre_producto):
    tienda = {
        "nombre": "HunterCardTCG",
        "url": "https://www.huntercardtcg.com/?s={}&post_type=product"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')

        # Verificar si no hay resultados
        productos = soup.select("li.thunk-woo-product-list")
        if not productos:
            resultado = {
                "Tienda": tienda['nombre'], 
                "Disponible": "No", 
                "Producto": nombre_producto, 
                "Precio": "-", 
                "URL": url_busqueda
            }
        else:
            producto_encontrado = None
            for p in productos:
                titulo = p.select_one(".woocommerce-loop-product__title")
                if titulo:
                    texto = titulo.get_text(strip=True)
                    # Prioriza inglés y Foil
                    if "English" in texto or "Inglés" in texto:
                        if "Foil" in texto or "foil" in texto:
                            producto_encontrado = p
                            break
                        elif not producto_encontrado:
                            producto_encontrado = p

            if producto_encontrado:
                titulo = producto_encontrado.select_one(".woocommerce-loop-product__title").get_text(strip=True)
                precio_tag = producto_encontrado.select_one(".price .woocommerce-Price-amount")
                precio = precio_tag.get_text(strip=True) if precio_tag else "-"
                url_prod = producto_encontrado.select_one("a.woocommerce-LoopProduct-link")["href"]

                resultado = {
                    "Tienda": tienda['nombre'],
                    "Disponible": "Sí",
                    "Producto": titulo,
                    "Precio": precio,
                    "URL": url_prod
                }
            else:
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
    "nombre": "HunterCardTCG",
    "func": buscar
}
