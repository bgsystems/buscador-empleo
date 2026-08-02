"""Utilidades HTTP compartidas por las estrategias de scraping."""
import html
import logging
import re
import time

import requests

log = logging.getLogger(__name__)

_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Pausa entre requests para no gatillar bloqueos (respeto básico al sitio)
PAUSA_SEG = 2


def get(url, **params):
    time.sleep(PAUSA_SEG)
    r = requests.get(url, params=params or None,
                     headers={"User-Agent": _UA, "Accept-Language": "es-AR,es;q=0.9"},
                     timeout=30)
    r.raise_for_status()
    return r.text


def limpiar_html(texto):
    return html.unescape(re.sub(r"<[^>]+>", " ", texto or "")).strip()
