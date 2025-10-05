import os
import subprocess
from datetime import datetime

# Colores ANSI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Banner de inicio estilo LOTR
banner = f"""
{Colors.YELLOW}{Colors.BOLD}
       ___       __        __   __  ___   __     __   __   __
      |__  |  | |__)  /\  |__) /  \  |   /  \ |  | /  ` /  \\
      |    \__/ |  \ /~~\ |  \ \__/  |   \__/ \__/ \__, \__/ 
{Colors.CYAN}{Colors.BOLD}
   🧙‍ Gandalf's Python Fellowship 🧝‍
      Uniendo scripts para la Tierra Media...
{Colors.RESET}
"""
print(banner)

# Carpeta donde está OneRing.py
folder = os.path.dirname(os.path.abspath(__file__))

# Buscar scripts que empiecen con "List_" en la misma carpeta
scripts = [f for f in os.listdir(folder) if f.startswith("List_") and f.endswith(".py")]

if not scripts:
    print(f"{Colors.RED}⚠️  Ningún proyecto Python de la Comarca encontrado (List_*.py).{Colors.RESET}")
    exit()

print(f"{Colors.GREEN}🗺 Se encontraron {len(scripts)} scripts aventureros:{Colors.RESET}")
for s in scripts:
    print(f"   ✦ {Colors.CYAN}{s}{Colors.RESET}")
print()

# Ejecutar cada script uno por uno
for script in scripts:
    print(f"{Colors.HEADER}🏹 En marcha: {script}...{Colors.RESET}")
    start_time = datetime.now()
    print(f"{Colors.BLUE}🕰 Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

    try:
        subprocess.run(["python", os.path.join(folder, script)], check=True)
        print(f"{Colors.GREEN}✔ {script} completado con éxito, ¡la misión continúa!{Colors.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}💀 Mordor ha interceptado {script}... Error durante la ejecución.{Colors.RESET}")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"{Colors.YELLOW}⏳ Duración de la misión: {duration}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.RESET}\n")

# Preguntar si se quiere ejecutar Unificador.py
unificador = os.path.join(folder, "Unificador.py")
if os.path.exists(unificador):
    choice = input(f"{Colors.BOLD}¿Desea ejecutar {Colors.GREEN}Unificador.py{Colors.BOLD} ahora para unir la Comunidad del Anillo? (s/n): {Colors.RESET}").strip().lower()
    if choice == 's':
        print(f"{Colors.HEADER}⚔️ Ejecutando Unificador.py... ¡Que la luz de Eärendil nos guíe!{Colors.RESET}")
        subprocess.run(["python", unificador])
        print(f"{Colors.GREEN}✔ Unificador.py completado. La Comunidad del Anillo se ha reunido.{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️ Unificador.py no fue ejecutado. La Comarca sigue segura... por ahora.{Colors.RESET}")
else:
    print(f"{Colors.RED}❌ No se encontró Unificador.py en la carpeta. Sauron está contento.{Colors.RESET}")
