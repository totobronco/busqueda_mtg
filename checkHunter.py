import requests
from bs4 import BeautifulSoup
import re

# Colores ANSI
VERDE = "\033[92m"
ROJO = "\033[91m"
RESET = "\033[0m"

# URL base
BASE_URL = "https://www.huntercardtcg.com/categoria-producto/mtg/mtg-singles/page/{}/?orderby=price"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 🔸 Preguntar si desea discriminar las no Foil
while True:
    opcion = input("¿Deseas mostrar solo cartas Foil? (S/N): ").strip().lower()
    if opcion in ["s", "n"]:
        solo_foil = (opcion == "s")
        break
    else:
        print("⚠️ Opción inválida. Por favor escribe 'S' o 'N'.")

# 🔸 Preguntar si desea mostrar el contenido entre paréntesis
while True:
    opcion_parentesis = input("¿Deseas mostrar el texto entre paréntesis (como '(Foil)' o '(Showcase Foil)')? (S/N): ").strip().lower()
    if opcion_parentesis in ["s", "n"]:
        mostrar_parentesis = (opcion_parentesis == "s")
        break
    else:
        print("⚠️ Opción inválida. Por favor escribe 'S' o 'N'.")

# 🔸 Preguntar por precio máximo
while True:
    precio_input = input("Ingresa precio máximo o '-' para no limitar: ").strip()
    if precio_input == "-":
        precio_max = None
        break
    elif precio_input.isdigit():
        precio_max = int(precio_input)
        break
    else:
        print("⚠️ Solo puedes ingresar un número o '-'.")

# 🔸 Preguntar si quiere mostrar solo los nombres
while True:
    opcion_nombres = input("¿Deseas mostrar solo los nombres? (S/N): ").strip().lower()
    if opcion_nombres in ["s", "n"]:
        solo_nombres = (opcion_nombres == "s")
        break
    else:
        print("⚠️ Opción inválida. Por favor escribe 'S' o 'N'.")

pagina = 1
total_productos = 0

while True:
    url = BASE_URL.format(pagina)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ No se pudo acceder a la página {pagina}")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    productos = soup.find_all("li", class_="product")

    if not productos:
        print(f"\n✅ No se encontraron más productos. Fin en página {pagina - 1}.")
        break

    print(f"\n📄 Página {pagina} - {len(productos)} productos encontrados:")
    print("-" * 60)

    for producto in productos:
        nombre_tag = producto.find("h2", class_="woocommerce-loop-product__title")
        precio_tag = producto.find("span", class_="woocommerce-Price-amount")

        if nombre_tag and precio_tag:
            nombre_completo = nombre_tag.get_text(strip=True)
            precio_texto = precio_tag.get_text(strip=True).replace("$", "").replace(".", "").strip()

            try:
                precio_num = int(precio_texto)
            except ValueError:
                continue  # si no se puede convertir el precio, se salta

            # Detectar si es Foil
            es_foil = "foil" in nombre_completo.lower()
            foil_symbol = f"{VERDE}☑{RESET}" if es_foil else f"{ROJO}X{RESET}"

            # Filtros
            if solo_foil and not es_foil:
                continue
            if precio_max is not None and precio_num > precio_max:
                continue

            # Limpiar nombre si no se quieren ver los paréntesis
            if not mostrar_parentesis:
                nombre_completo = re.sub(r"\s*\(.*?\)", "", nombre_completo)

            # Obtener solo la primera parte del nombre antes del primer "–"
            nombre_simple = nombre_completo.split("–")[0].strip()

            # Mostrar según si quiere solo nombres o todo
            if solo_nombres:
                print(f"{nombre_simple}")
            else:
                print(f"{nombre_simple} - ${precio_num} - {foil_symbol}")

            total_productos += 1

    pagina += 1

print(f"\n🧾 Total de productos mostrados: {total_productos}")
