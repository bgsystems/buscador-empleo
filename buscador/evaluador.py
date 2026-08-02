"""Evaluación de ofertas con Gemini API (REST, sin SDK)."""
import json
import logging
import re

import requests

from . import config

log = logging.getLogger(__name__)

_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
        "{modelo}:generateContent")

# Fallback: cada modelo tiene su propia cuota diaria en el free tier
# (gemini-3.6-flash: solo 20 req/día). Si uno se agota, se pasa al siguiente.
MODELOS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
_modelo_idx = 0

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
        raise ValueError(f"Sin JSON en respuesta: {texto[:200]}")
    datos = json.loads(m.group(0))
    datos["match_score"] = int(datos.get("match_score", 0))
    return datos


def evaluar(oferta, cv, preferencias):
    """Devuelve dict con la evaluación, o None si falla la llamada."""
    global _modelo_idx
    prompt = _PROMPT.format(
        cv=cv, preferencias=preferencias,
        titulo=oferta["titulo"], empresa=oferta.get("empresa", "?"),
        ubicacion=oferta.get("ubicacion", "?"),
        descripcion=oferta.get("descripcion", "")[:6000],
    )
    while _modelo_idx < len(MODELOS):
        modelo = MODELOS[_modelo_idx]
        try:
            r = requests.post(
                _URL.format(modelo=modelo),
                params={"key": config.GEMINI_API_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.2,
                                           "responseMimeType": "application/json"}},
                timeout=60,
            )
            if r.status_code == 429:
                # Cuota del modelo agotada: pasar al siguiente por el resto de la corrida
                _modelo_idx += 1
                log.info("429 en %s, cambio a %s", modelo,
                         MODELOS[_modelo_idx] if _modelo_idx < len(MODELOS) else "ninguno")
                continue
            r.raise_for_status()
            texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return _parsear_json(texto)
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            log.warning("Evaluación falló para %s: %s", oferta["url"], e)
            return None
    log.warning("Todos los modelos agotaron cuota")
    return None
