"""Scraper de portales de empleo — patrón strategy.

Punto de entrada único: obtener_ofertas(). Cada sitio es una estrategia
(función `buscar(keyword, urls_conocidas)`) registrada en ESTRATEGIAS.
Todas devuelven el contrato normalizado de buscador/fuentes.py:
    {url, titulo, empresa, ubicacion, descripcion, fuente}

`urls_conocidas` permite saltear el fetch del detalle de ofertas ya vistas
(menos requests = menos riesgo de bloqueo).
"""
import logging

from buscador import config

from . import computrabajo, linkedin

log = logging.getLogger(__name__)

# ponytail: strategy = dict de funciones; una clase por sitio sería ceremonia
ESTRATEGIAS = {
    "linkedin": linkedin.buscar,
    "computrabajo": computrabajo.buscar,
    # "zonajobs": bloqueado por Cloudflare sin browser — ver README.md
}


def obtener_ofertas(urls_conocidas=frozenset()):
    ofertas = []
    for sitio in config.SCRAPER_SITIOS:
        estrategia = ESTRATEGIAS.get(sitio)
        if estrategia is None:
            log.warning("Sitio sin estrategia registrada: %s", sitio)
            continue
        for keyword in config.SCRAPER_BUSQUEDAS:
            try:
                nuevas = estrategia(keyword, urls_conocidas)
                log.info("Scraper %s '%s': %d ofertas", sitio, keyword, len(nuevas))
                ofertas.extend(nuevas)
            except Exception as e:
                log.warning("Scraper %s '%s' falló: %s", sitio, keyword, e)
    return ofertas
