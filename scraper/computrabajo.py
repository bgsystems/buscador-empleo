"""Estrategia Computrabajo AR: listado HTML + JSON-LD (JobPosting) del detalle."""
import json
import logging
import re

from . import comun

log = logging.getLogger(__name__)

_BASE = "https://ar.computrabajo.com"
_LISTADO = _BASE + "/trabajo-de-{keyword}-en-capital-federal"
MAX_DETALLES = 10


def _jobposting(html_detalle):
    """Extrae el bloque JobPosting del JSON-LD (viene dentro de @graph)."""
    m = re.search(r'application/ld\+json.>(.*?)</script>', html_detalle, re.DOTALL)
    if not m:
        return None
    grafo = json.loads(m.group(1)).get("@graph", [])
    return next((g for g in grafo if g.get("@type") == "JobPosting"), None)


def buscar(keyword, urls_conocidas=frozenset()):
    listado = comun.get(_LISTADO.format(keyword=keyword.replace(" ", "-")))
    rutas = re.findall(r'class="js-o-link[^"]*" href="(/ofertas-de-trabajo/[^"#]+)', listado)
    ofertas, detalles = [], 0
    for ruta in dict.fromkeys(rutas):  # dedup preservando orden
        url = _BASE + ruta
        if url in urls_conocidas or detalles >= MAX_DETALLES:
            continue
        try:
            jp = _jobposting(comun.get(url))
            detalles += 1
        except Exception as e:
            log.debug("Detalle %s falló: %s", url, e)
            continue
        if not jp:
            continue
        lugar = jp.get("jobLocation", {})
        direccion = lugar.get("address", {}) if isinstance(lugar, dict) else {}
        ofertas.append({
            "url": url,
            "titulo": jp.get("title", ""),
            "empresa": (jp.get("hiringOrganization") or {}).get("name", ""),
            "ubicacion": ", ".join(filter(None, [direccion.get("addressLocality"),
                                                 direccion.get("addressRegion")])),
            "descripcion": comun.limpiar_html(jp.get("description", ""))[:8000],
            "fuente": "computrabajo",
        })
    return ofertas
