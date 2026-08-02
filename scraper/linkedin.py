"""Estrategia LinkedIn: API guest pública (sin login, sin riesgo para cuentas).

Listado: /jobs-guest/jobs/api/seeMoreJobPostings/search (HTML de tarjetas).
Detalle: /jobs-guest/jobs/api/jobPosting/<id> (HTML con la descripción).
"""
import logging
import re

from . import comun

log = logging.getLogger(__name__)

_LISTADO = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
_DETALLE = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{id}"
_UBICACION = "Buenos Aires, Argentina"
MAX_DETALLES = 10  # tope de fetches de detalle por búsqueda


def _tarjetas(html_listado):
    """Extrae (url_canonica, id, titulo, empresa, ubicacion) de cada tarjeta."""
    for card in re.split(r"<li>", html_listado)[1:]:
        m_link = re.search(r'href="https://[^"]*linkedin\.com/jobs/view/[^"?]*?-(\d+)\?', card)
        m_tit = re.search(r'base-search-card__title">\s*([^<]+)', card)
        if not (m_link and m_tit):
            continue
        jid = m_link.group(1)
        m_emp = re.search(r'base-search-card__subtitle">.*?>([^<]+)<', card, re.DOTALL)
        m_ubi = re.search(r'job-search-card__location">\s*([^<]+)', card)
        yield (f"https://www.linkedin.com/jobs/view/{jid}", jid,
               comun.limpiar_html(m_tit.group(1)),
               comun.limpiar_html(m_emp.group(1)) if m_emp else "",
               comun.limpiar_html(m_ubi.group(1)) if m_ubi else "")


def _descripcion(jid):
    detalle = comun.get(_DETALLE.format(id=jid))
    m = re.search(r"show-more-less-html__markup[^>]*>(.*?)</div>", detalle, re.DOTALL)
    return comun.limpiar_html(m.group(1))[:8000] if m else ""


def buscar(keyword, urls_conocidas=frozenset()):
    listado = comun.get(_LISTADO, keywords=keyword, location=_UBICACION, start=0)
    ofertas, detalles = [], 0
    for url, jid, titulo, empresa, ubicacion in _tarjetas(listado):
        if url in urls_conocidas or detalles >= MAX_DETALLES:
            continue
        try:
            descripcion = _descripcion(jid)
            detalles += 1
        except Exception as e:
            log.debug("Detalle %s falló: %s", jid, e)
            descripcion = ""
        ofertas.append({"url": url, "titulo": titulo, "empresa": empresa,
                        "ubicacion": ubicacion, "descripcion": descripcion,
                        "fuente": "linkedin"})
    return ofertas
