"""Ingesta de ofertas desde fuentes públicas estables (APIs y RSS).

Toda fuente devuelve una lista de dicts normalizados:
    {url, titulo, empresa, ubicacion, descripcion, fuente}
El scraper Playwright (fase 2, carpeta scraper/) debe cumplir el mismo contrato.
"""
import html
import logging
import re

import feedparser
import requests

from . import config

log = logging.getLogger(__name__)


def _limpiar_html(texto):
    return html.unescape(re.sub(r"<[^>]+>", " ", texto or "")).strip()


def desde_remotive():
    """API pública de Remotive (empleos remotos, sin API key)."""
    ofertas = []
    try:
        r = requests.get("https://remotive.com/api/remote-jobs", timeout=30)
        r.raise_for_status()
        for j in r.json().get("jobs", []):
            ofertas.append({
                "url": j["url"],
                "titulo": j.get("title", ""),
                "empresa": j.get("company_name", ""),
                "ubicacion": j.get("candidate_required_location", ""),
                "descripcion": _limpiar_html(j.get("description", ""))[:8000],
                "fuente": "remotive",
            })
    except requests.RequestException as e:
        log.warning("Remotive falló: %s", e)
    return ofertas


def desde_rss():
    ofertas = []
    for feed_url in config.FEEDS_RSS:
        try:
            feed = feedparser.parse(feed_url)
            for e in feed.entries:
                ofertas.append({
                    "url": e.get("link", ""),
                    "titulo": e.get("title", ""),
                    "empresa": e.get("author", ""),
                    "ubicacion": "",
                    "descripcion": _limpiar_html(e.get("summary", ""))[:8000],
                    "fuente": feed_url,
                })
        except Exception as e:
            log.warning("Feed %s falló: %s", feed_url, e)
    return ofertas


def coincide_keywords(oferta):
    texto = (oferta["titulo"] + " " + oferta.get("descripcion", "")[:500]).lower()
    return any(k in texto for k in config.KEYWORDS)


def obtener_todas(urls_conocidas=frozenset()):
    import scraper
    ofertas = desde_remotive() + desde_rss() + scraper.obtener_ofertas(urls_conocidas)
    log.info("Ingesta: %d ofertas crudas", len(ofertas))
    return [o for o in ofertas if o.get("url")]
