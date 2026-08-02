"""Notificación de matches por Telegram Bot API."""
import html
import logging

import requests

from . import config

log = logging.getLogger(__name__)


def _esc(t):
    return html.escape(str(t or ""))


def formatear(oferta, ev):
    fuertes = "\n".join(f"• {_esc(p)}" for p in ev.get("puntos_fuertes", []))
    gaps = "\n".join(f"• {_esc(g)}" for g in ev.get("gaps_o_faltantes", []))
    return (
        f"🎯 <b>¡NUEVO MATCH! ({ev['match_score']}%)</b>\n\n"
        f"📌 <b>{_esc(oferta['titulo'])}</b>\n"
        f"🏢 {_esc(oferta.get('empresa', '?'))}\n"
        f"📍 {_esc(oferta.get('ubicacion', '?'))}\n\n"
        f"📄 {_esc(ev.get('resumen_puesto', ''))}\n\n"
        f"💡 <b>Por qué encaja:</b>\n{fuertes}\n\n"
        f"⚠️ <b>A tener en cuenta:</b>\n{gaps or '• Nada relevante'}\n\n"
        f"🔗 {_esc(oferta['url'])}\n\n"
        f"📝 <b>Pitch sugerido:</b>\n<i>{_esc(ev.get('carta_presentacion_sugerida', ''))}</i>"
    )


def enviar(oferta, ev):
    """Envía el match a Telegram. Devuelve True si se envió OK."""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID,
                  "text": formatear(oferta, ev)[:4000],
                  "parse_mode": "HTML",
                  "disable_web_page_preview": False},
            timeout=30,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        # ponytail: no loguear el token; el mensaje de error de requests no lo incluye en la URL con json=
        log.error("Telegram falló para %s: %s", oferta["url"], type(e).__name__)
        return False
