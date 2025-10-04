# 📖 Buscador de Cartas Online

Una aplicación en Python que permite buscar cartas de Magic (u otras) en múltiples tiendas online, mostrando disponibilidad y precio. Permite búsquedas individuales o múltiples desde un archivo `buscar.txt`, resaltando la opción más económica.

---

## 🔹 Requisitos

- Python 3.10 o superior  
- Conexión a Internet  
- Paquetes de Python:
  - `requests`
  - `beautifulsoup4`

---

## 🔹 Instalación rápida

1. **Clonar o descargar el repositorio**

```bash
git clone https://github.com/usuario/buscador-cartas.git
cd buscador-cartas
Crear un entorno virtual (opcional, pero recomendado)

bash
Copy code
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
Instalar dependencias

bash
Copy code
pip install -r requirements.txt
requirements.txt debería incluir:

nginx
Copy code
requests
beautifulsoup4
Verificar estructura del proyecto

bash
Copy code
buscador-cartas/
│
├── tiendas/                # Carpeta con todos los módulos de tiendas
│   ├── __init__.py
│   ├── bloodmoongames.py
│   ├── oasisgames.py
│   ├── ...
│
├── main.py                 # Archivo principal para ejecutar el buscador
├── buscar.txt              # Archivo con varias cartas para búsqueda
└── README.md
🔹 Uso
1️⃣ Buscar una sola carta
bash
Copy code
python main.py
El programa preguntará si quieres buscar 1 carta o varias (1 o +)

Si seleccionas 1, ingresa el nombre exacto de la carta

Los resultados aparecerán en pantalla, resaltando en verde la opción más económica

2️⃣ Buscar varias cartas desde archivo
Crea o edita buscar.txt con cada carta en una línea:

rust
Copy code
Battershield Warrior
Gaea's Cradle
ITALIAN The Tabernacle at Pendrell Vale
Ejecuta:

bash
Copy code
python main.py
Selecciona +

El programa buscará las cartas de 3 en 3, preguntando si deseas continuar después de cada batch.

🔹 Recomendaciones
Mantén tu archivo buscar.txt limpio, sin líneas vacías al final

Asegúrate de tener conexión a Internet para que el scraper funcione correctamente

Puedes agregar nuevas tiendas creando módulos dentro de la carpeta tiendas siguiendo el mismo formato de metadata

🔹 Posibles mejoras
Exportar resultados a CSV o Excel

Interfaz gráfica con Tkinter o PyQt

Guardar historial de búsquedas

Ejemplo de resultados
bash
Copy code
✅ Disponibles:
💰 BloodMoonGames | Battershield Warrior | $400 | https://bloodmoongames.cl/...
   OasisGames | Battershield Warrior [Kaldheim] | $700 | https://www.oasisgames.cl/...

❌ No disponibles:
   HunterCardTCG | Battershield Warrior | - | https://www.huntercardtcg.com/...
🔹 Comandos rápidos de consola para el usuario final
bash
Copy code
# Activar entorno virtual
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Ejecutar buscador
python main.py

# Instalar paquetes si faltan
pip install -r requirements.txt
yaml
Copy code

---

Si quieres, puedo hacer una **versión extendida con colores y emojis de ejemplo en la salida** para que quede mucho más visual en la terminal y el README. Esto ayuda a que cualquier usuario que abra el proyecto entienda rápido cómo funciona.  

¿Quieres que haga esa versión más “visual”?






