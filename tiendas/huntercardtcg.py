import requests
from bs4 import BeautifulSoup
import re

# --- Colores para la terminal ---
class Colores:
    VERDE = '\033[92m'
    ROJO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'

def buscar(nombre_producto):
    tienda = {
        "nombre": "HunterCardTCG",
        "url": "https://www.huntercardtcg.com/?s={}&post_type=product"
    }
    url_busqueda = tienda["url"].format(nombre_producto.replace(' ', '+'))
    resultado = {}

    try:
        print(f"{Colores.AZUL}Buscando en {tienda['nombre']}...{Colores.RESET}", end="")
        response = requests.get(url_busqueda, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        final_url = response.url  # URL final tras redirección
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- CASO 1: Página individual de producto (cuando hay solo un resultado) ---
        if "producto/" in final_url:
            titulo_tag = soup.select_one("h1.product_title.entry-title")
            precio_tag = soup.select_one("p.price .woocommerce-Price-amount")
            stock_tag = soup.select_one("p.stock")

            if titulo_tag and nombre_producto.lower() in titulo_tag.get_text(strip=True).lower():
                titulo = titulo_tag.get_text(strip=True)
                precio = precio_tag.get_text(strip=True) if precio_tag else "-"
                stock_text = stock_tag.get_text(strip=True).lower() if stock_tag else ""

                disponible = "Sí" if "disponible" in stock_text or "stock" in stock_text else "No"

                resultado = {
                    "Tienda": tienda["nombre"],
                    "Disponible": disponible,
                    "Producto": titulo,
                    "Precio": precio,
                    "URL": final_url
                }
            else:
                # Producto encontrado no coincide con la búsqueda
                resultado = {
                    "Tienda": tienda["nombre"],
                    "Disponible": "No",
                    "Producto": nombre_producto,
                    "Precio": "-",
                    "URL": url_busqueda
                }

        # --- CASO 2: Página de resultados múltiples ---
        else:
            productos = soup.select("li.thunk-woo-product-list")

            if not productos:
                resultado = {
                    "Tienda": tienda["nombre"],
                    "Disponible": "No",
                    "Producto": nombre_producto,
                    "Precio": "-",
                    "URL": url_busqueda
                }
            else:
                nombre_normalizado = nombre_producto.lower()
                coincidencias = []

                for p in productos:
                    titulo_tag = p.select_one(".woocommerce-loop-product__title")
                    if not titulo_tag:
                        continue

                    titulo = titulo_tag.get_text(strip=True)
                    titulo_normalizado = titulo.lower()

                    # Aceptar coincidencias si el nombre buscado aparece en el título
                    if nombre_normalizado in titulo_normalizado:
                        coincidencias.append(p)

                if not coincidencias:
                    resultado = {
                        "Tienda": tienda["nombre"],
                        "Disponible": "No",
                        "Producto": nombre_producto,
                        "Precio": "-",
                        "URL": url_busqueda
                    }
                else:
                    # Priorizar Foil si existe
                    producto_encontrado = None
                    for p in coincidencias:
                        titulo = p.select_one(".woocommerce-loop-product__title").get_text(strip=True)
                        if "foil" in titulo.lower():
                            producto_encontrado = p
                            break
                    if not producto_encontrado:
                        producto_encontrado = coincidencias[0]

                    titulo = producto_encontrado.select_one(".woocommerce-loop-product__title").get_text(strip=True)
                    precio_tag = producto_encontrado.select_one(".price .woocommerce-Price-amount")
                    precio = precio_tag.get_text(strip=True) if precio_tag else "-"
                    url_prod = producto_encontrado.select_one("a.woocommerce-LoopProduct-link")["href"]

                    resultado = {
                        "Tienda": tienda["nombre"],
                        "Disponible": "Sí",
                        "Producto": titulo,
                        "Precio": precio,
                        "URL": url_prod
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


# --- Metadata de la tienda ---
metadata = {
    "nombre": "HunterCardTCG",
    "func": buscar
}
