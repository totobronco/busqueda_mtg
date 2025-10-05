import requests
from bs4 import BeautifulSoup
import json

def buscar_producto(nombre_busqueda):
    url_busqueda = f"https://www.cartasmagicsur.cl/?s={nombre_busqueda.replace(' ', '+')}&post_type=product"
    resultado = {
        "Tienda": "Cartas Magic Sur",
        "Disponible": "No",
        "Cantidad": "-",
        "Producto": nombre_busqueda,
        "Precio": "-",
        "URL": url_busqueda
    }

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url_busqueda, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        productos = soup.select("ul.products li.product, div.summary.entry-summary")
        for p in productos:
            titulo_tag = p.select_one("h2.product_title, h3.woocommerce-loop-product__title")
            if not titulo_tag:
                continue
            titulo = titulo_tag.text.strip()

            if nombre_busqueda.lower() in titulo.lower():
                variaciones_form = p.select_one("form.variations_form")
                if variaciones_form:
                    variations_json = variaciones_form.get("data-product_variations", "[]")
                    variations = json.loads(variations_json)
                    for v in variations:
                        if v.get("is_in_stock"):
                            cantidad = BeautifulSoup(v.get("availability_html", ""), "html.parser").text.strip()
                            precio = f"${v.get('display_price', 0):,.0f}"
                            url_prod = variaciones_form.get("action")
                            resultado.update({
                                "Disponible": "Sí",
                                "Cantidad": cantidad,
                                "Producto": titulo,
                                "Precio": precio,
                                "URL": url_prod
                            })
                            return resultado

                precio_tag = p.select_one("span.woocommerce-Price-amount")
                precio = precio_tag.text.strip() if precio_tag else "-"
                url_tag = p.select_one("a.woocommerce-LoopProduct-link, form.variations_form")
                url_prod = url_tag.get("href") if url_tag and url_tag.has_attr("href") else url_busqueda
                resultado.update({
                    "Disponible": "Sí",
                    "Producto": titulo,
                    "Precio": precio,
                    "URL": url_prod
                })
                return resultado

    except Exception as e:
        print("Error:", e)

    return resultado

# --- Metadata ---
metadata = {
    "nombre": "Cartas Magic Sur",
    "url": "https://www.cartasmagicsur.cl",
    "func": buscar_producto  # <-- clave necesaria
}
