"""Evaluación de ofertas a través de la API OpenAI-compatible de LiteLLM."""
import json
import logging
import re

import requests

from . import config

log = logging.getLogger(__name__)

_PROMPT = """Actúa como un reclutador experto IT/Corporativo en Argentina.

[PERFIL Y CV DEL CANDIDATO]
{cv}

[REQUISITOS / PREFERENCIAS DEL CANDIDATO]
{preferencias}

[DESCRIPCIÓN DE LA OFERTA LABORAL]
Título: {titulo}
Empresa: {empresa}
Ubicación: {ubicacion}
{descripcion}

TAREA:
Analiza la coincidencia entre el perfil del candidato y la oferta laboral.
Devuelve la respuesta estrictamente en formato JSON con esta estructura, sin texto adicional:

{{
  "match_score": <número entero entre 0 y 100>,
  "resumen_puesto": "<resumen de 2 oraciones del puesto>",
  "puntos_fuertes": ["<punto 1>", "<punto 2>"],
  "gaps_o_faltantes": ["<habilidad o requisito que le falta al candidato>"],
  "carta_presentacion_sugerida": "<un párrafo breve resaltando las fortalezas clave para este puesto>"
}}

Si la oferta viola alguna exclusión/dealbreaker del candidato, el match_score debe ser menor a 30.
"""


def _parsear_json(texto):
    """Parseo tolerante: extrae el primer bloque {...} aunque venga con markdown."""
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        raise ValueError("Respuesta sin JSON")
    datos = json.loads(m.group(0))
    datos["match_score"] = int(datos.get("match_score", 0))
    return datos


def evaluar(oferta, cv, preferencias):
    """Devuelve dict con la evaluación, o None si falla la llamada."""
    prompt = _PROMPT.format(
        cv=cv, preferencias=preferencias,
        titulo=oferta["titulo"], empresa=oferta.get("empresa", "?"),
        ubicacion=oferta.get("ubicacion", "?"),
        descripcion=oferta.get("descripcion", "")[:6000],
    )
    try:
        r = requests.post(
            f"{config.LITELLM_API_BASE.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.LITELLM_TOKEN}"},
            json={"model": config.LITELLM_MODEL,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2,
                  "response_format": {"type": "json_object"}},
            # ponytail: internal proxy has no hostname-valid certificate; trust its CA if that changes.
            verify=False,
            timeout=60,
        )
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"]
        if not isinstance(texto, str):
            raise ValueError("Respuesta del modelo sin contenido de texto")
        return _parsear_json(texto)
    except (requests.RequestException, KeyError, ValueError, IndexError, TypeError) as e:
        log.warning("Evaluación falló para %s: %s", oferta["url"], type(e).__name__)
        return None
