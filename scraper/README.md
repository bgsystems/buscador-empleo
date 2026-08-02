# Scraper — patrón strategy

Punto de entrada único (`scraper.obtener_ofertas()`) que ejecuta las estrategias
habilitadas en `config.SCRAPER_SITIOS` con los términos de `config.SCRAPER_BUSQUEDAS`.
Todo con `requests` puro — sin Playwright ni login.

## Estrategias

| Sitio | Módulo | Técnica |
|---|---|---|
| LinkedIn | `linkedin.py` | API guest pública (`jobs-guest/jobs/api/...`) — sin sesión, cero riesgo para cuentas |
| Computrabajo AR | `computrabajo.py` | Listado HTML + JSON-LD (`JobPosting` en `@graph`) del detalle |
| Zonajobs | — | **No viable**: SPA React y su API interna está detrás de Cloudflare; requeriría browser real (Playwright). Descartado por ahora. |

## Agregar una estrategia

1. Crear `scraper/<sitio>.py` con una función:
   ```python
   def buscar(keyword: str, urls_conocidas: frozenset = frozenset()) -> list[dict]:
       # devuelve dicts: {url, titulo, empresa, ubicacion, descripcion, fuente}
       # saltear detalle si url in urls_conocidas (ahorra requests)
   ```
2. Registrarla en `ESTRATEGIAS` (`scraper/__init__.py`).
3. Habilitarla en `SCRAPER_SITIOS` (`buscador/config.py`).

## Notas
- Pausa de 2s entre requests (`comun.PAUSA_SEG`) y tope de 10 fetches de
  detalle por búsqueda (`MAX_DETALLES`) para no gatillar bloqueos.
- Solo se scrapean páginas públicas, nunca con la cuenta de la candidata.
- Los sitios cambian su HTML: si una estrategia deja de devolver ofertas,
  revisar las regex del módulo (los checks offline de `test_buscador.py`
  cubren el parseo, no el HTML real).
