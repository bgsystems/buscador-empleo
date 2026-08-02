# Buscador de Empleos Automatizado

Pipeline que busca ofertas de empleo, las evalúa con IA (Gemini) contra el CV y
preferencias de la candidata, y notifica por Telegram solo los matches altos con
un pitch de postulación listo para usar.

```
[ Remotive API / RSS / Scrapers (LinkedIn, Computrabajo) ] → [ dedup SQLite ]
   → [ filtro keywords ] → [ Gemini: match_score + pitch ] → [ score ≥ umbral → Telegram ]
```

**No postula automáticamente**: la cuenta de la candidata nunca se toca.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # completar credenciales (ver abajo)
```

### Credenciales (`.env` — nunca commitear)

| Variable | Cómo obtenerla |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (free tier) |
| `TELEGRAM_BOT_TOKEN` | Hablar con [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | **Primero** mandarle `/start` al bot en Telegram, **después** consultar `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id` (si devuelve `[]`, el bot aún no recibió ningún mensaje) |
| `UMBRAL_MATCH` | Opcional, default 75 |

### Perfil de la candidata

- `perfil/cv.txt` — CV en texto plano (gitignoreado por ser dato personal).
  Generar con: `pdftotext cv.pdf perfil/cv.txt`
- `perfil/preferencias.txt` — modalidad, roles de interés, exclusiones.

Las keywords de pre-filtro y los feeds RSS se ajustan en `buscador/config.py`.

## Uso

```bash
python -m buscador          # una corrida completa
python test_buscador.py     # self-checks
```

### Automatizar con cron (cada 4 horas)

```cron
0 */4 * * * cd /ruta/al/buscador-empleos && /usr/bin/python3 -m buscador >> buscador.log 2>&1
```

## Salidas

- Mensajes de Telegram con: score, puesto, empresa, puntos fuertes, gaps,
  link y pitch sugerido.
- `ofertas.db` (SQLite): historial de todas las ofertas vistas con su estado
  (`descartada_keyword`, `evaluada`, `notificada`, `error`). Sirve de dedup:
  ninguna oferta se evalúa ni notifica dos veces.

## Troubleshooting

- **"Faltan variables en .env"**: copiar `.env.example` a `.env` y completar.
- **Evaluaciones que fallan (429)**: el free tier limita por modelo y por día
  (gemini-3.6-flash: 20 req/día). El evaluador hace fallback automático entre
  los modelos de `MODELOS` (`buscador/evaluador.py`); si todos se agotan,
  las ofertas quedan en estado `error` y se reintentan en la próxima corrida.
- **No llegan mensajes de Telegram**: verificar que iniciaste chat con el bot
  (mandarle `/start`) y que el `chat_id` es correcto.
- **Pocas ofertas relevantes**: agregar feeds en `FEEDS_RSS` y ampliar `KEYWORDS`
  en `buscador/config.py`.

## Fase 2 (implementada)

Scraper con patrón strategy para LinkedIn (API guest) y Computrabajo (JSON-LD),
sin browser ni login: ver `scraper/README.md`. Sitios y búsquedas se configuran
con `SCRAPER_SITIOS` y `SCRAPER_BUSQUEDAS` en `buscador/config.py`.
Zonajobs descartado (Cloudflare bloquea su API sin browser).
