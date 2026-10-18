"""Configuración: lee .env simple y define parámetros de búsqueda."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_env():
    # ponytail: parser .env de 5 líneas, python-dotenv sería una dependencia más
    archivo = RAIZ / ".env"
    if archivo.exists():
        for linea in archivo.read_text().splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, _, valor = linea.partition("=")
                os.environ.setdefault(clave.strip(), valor.strip())


_cargar_env()

LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE", "https://litellm.home.arpa/v1")
LITELLM_TOKEN = os.environ.get("LITELLM_TOKEN", "")
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "gemini-3.8-flash")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
UMBRAL_MATCH = int(os.environ.get("UMBRAL_MATCH", "75"))

# Límites conservadores para evitar corridas largas y picos de consumo.
MAX_EVALUACIONES_POR_CORRIDA = 20
PAUSA_ENTRE_LLAMADAS_SEG = 12

DB_PATH = RAIZ / "ofertas.db"
CV_PATH = RAIZ / "perfil" / "cv.txt"
PREFERENCIAS_PATH = RAIZ / "perfil" / "preferencias.txt"

# Keywords para filtrar títulos de ofertas antes de gastar llamadas a la IA.
# Derivadas del perfil: administrativa/RRHH + soporte IT + frontend/QA junior.
KEYWORDS = [
    "administrativ", "recursos humanos", "rrhh", "human resources", "hr ",
    "soporte", "help desk", "mesa de ayuda", "support",
    "frontend", "front-end", "front end", "desarrollador junior", "developer junior",
    "qa", "tester", "testing",
    "analista funcional", "data entry", "back office", "backoffice",
]

# Feeds RSS de portales de empleo (agregar/quitar libremente)
FEEDS_RSS = [
    # We Work Remotely - categorías afines
    "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
]

# Scraper (patrón strategy): sitios habilitados y términos de búsqueda.
# Estrategias disponibles en scraper/__init__.py (zonajobs bloqueado por Cloudflare).
SCRAPER_SITIOS = ["linkedin", "computrabajo"]
SCRAPER_BUSQUEDAS = ["administrativa", "recursos humanos", "soporte tecnico"]
