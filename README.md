# Buscador de Empleos Automatizado

Pipeline que busca ofertas de empleo, las evalúa con IA (LiteLLM) contra el CV y
preferencias de la candidata, y notifica por Telegram solo los matches altos con
un pitch de postulación listo para usar.

```
[ Remotive API / RSS / Scrapers (LinkedIn, Computrabajo) ] → [ dedup SQLite ]
   → [ filtro keywords ] → [ LiteLLM: match_score + pitch ] → [ score ≥ umbral → Telegram ]
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
| `LITELLM_API_BASE` | URL base de la API del proxy (default `https://litellm.home.arpa/v1`) |
| `LITELLM_MODEL` | Alias configurado en LiteLLM (default `gemini-3.8-flash`) |
| `LITELLM_TOKEN` | Virtual key dedicada creada en LiteLLM; en Kubernetes la inyecta `busqueda-config` |
| `TELEGRAM_BOT_TOKEN` | Hablar con [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | **Primero** mandarle `/start` al bot en Telegram, **después** consultar `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id` (si devuelve `[]`, el bot aún no recibió ningún mensaje) |
| `UMBRAL_MATCH` | Opcional, default 75 |

La llamada a LiteLLM omite la validación del certificado TLS, ya que el proxy
interno presenta el certificado por defecto de Traefik. Usar solo en una red de
confianza; si el proxy obtiene un certificado válido, volver a habilitarla.
El CronJob de Kubernetes usa el Service interno de LiteLLM y HTTP en el cluster.

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

### Contenedor

```bash
docker build -t buscador-empleo .
docker run --rm --network none buscador-empleo python test_buscador.py
docker run --rm --env-file .env \
  --mount type=bind,src="$(pwd)/perfil",dst=/profile,readonly \
  --mount type=bind,src="$(pwd)/state",dst=/state \
  buscador-empleo
```

Crear `state/` con permisos de escritura para UID/GID 1000. Para conservar
deduplicación, trasladar la SQLite existente a `state/ofertas.db` antes de
reemplazar una instalación. No ejecutar dos instancias sobre el mismo historial.
La imagen incluye código y dependencias, nunca `.env`, perfiles ni SQLite.
Las rutas se pueden ajustar con `DB_PATH`, `CV_PATH` y `PREFERENCIAS_PATH`;
fuera del contenedor mantienen sus valores locales originales.

GitHub Actions construye y ejecuta los self-checks en cada push a `main` o PR;
solo publica en pushes a `main` o ejecuciones manuales. GHCR usa tags
`sha-<commit>` y el resumen del build indica el digest para fijar en GitOps.
El paquete GHCR es privado. El homelab necesita un `imagePullSecret` de tipo
`kubernetes.io/dockerconfigjson` con acceso `read:packages` al paquete,
gestionado mediante SealedSecrets; nunca incluir credenciales en la imagen.
El CronJob conserva su PVC y SealedSecret; no instala paquetes ni monta código.

## Salidas

- Mensajes de Telegram con: score, puesto, empresa, puntos fuertes, gaps,
  link y pitch sugerido.
- `ofertas.db` (SQLite): historial de todas las ofertas vistas con su estado
  (`descartada_keyword`, `evaluada`, `notificada`, `error`). Sirve de dedup:
  ninguna oferta se evalúa ni notifica dos veces.

## Troubleshooting

- **"Faltan variables en .env"**: copiar `.env.example` a `.env` y completar.
- **Evaluaciones que fallan (401/429/5xx)**: comprobar la virtual key, el alias
  y el estado/cuota del proveedor configurado en LiteLLM. Las ofertas quedan en
  estado `error` y se reintentan en la próxima corrida.
- **No llegan mensajes de Telegram**: verificar que iniciaste chat con el bot
  (mandarle `/start`) y que el `chat_id` es correcto.
- **Pocas ofertas relevantes**: agregar feeds en `FEEDS_RSS` y ampliar `KEYWORDS`
  en `buscador/config.py`.

## Fase 2 (implementada)

Scraper con patrón strategy para LinkedIn (API guest) y Computrabajo (JSON-LD),
sin browser ni login: ver `scraper/README.md`. Sitios y búsquedas se configuran
con `SCRAPER_SITIOS` y `SCRAPER_BUSQUEDAS` en `buscador/config.py`.
Zonajobs descartado (Cloudflare bloquea su API sin browser).
