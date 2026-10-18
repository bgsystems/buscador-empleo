"""Pipeline: ingesta → dedup → filtro keywords → evaluación IA → notificación."""
import json
import logging
import sys
import time

from . import config, db, evaluador, fuentes, notificador

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("buscador")


def main():
    # Validar configuración antes de arrancar (evita corridas a medias)
    faltan = [n for n in ("LITELLM_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
              if not getattr(config, n)]
    if faltan:
        log.error("Faltan variables en .env: %s", ", ".join(faltan))
        sys.exit(1)
    if not config.CV_PATH.exists():
        log.error("No existe %s — extraer el CV a texto primero", config.CV_PATH)
        sys.exit(1)

    cv = config.CV_PATH.read_text()
    preferencias = config.PREFERENCIAS_PATH.read_text()
    con = db.conectar()

    nuevas = [o for o in fuentes.obtener_todas(db.urls_existentes(con))
              if db.es_nueva(con, o["url"])]
    log.info("%d ofertas nuevas", len(nuevas))

    evaluadas = notificadas = 0
    for oferta in nuevas:
        if not fuentes.coincide_keywords(oferta):
            db.guardar(con, oferta, "descartada_keyword")
            continue
        if evaluadas >= config.MAX_EVALUACIONES_POR_CORRIDA:
            # ponytail: las que no entran quedan sin registrar y se retoman en la próxima corrida
            log.info("Tope de %d evaluaciones alcanzado", config.MAX_EVALUACIONES_POR_CORRIDA)
            break

        ev = evaluador.evaluar(oferta, cv, preferencias)
        evaluadas += 1
        time.sleep(config.PAUSA_ENTRE_LLAMADAS_SEG)

        if ev is None:
            db.guardar(con, oferta, "error")
            continue

        if ev["match_score"] >= config.UMBRAL_MATCH:
            ok = notificador.enviar(oferta, ev)
            db.guardar(con, oferta, "notificada" if ok else "evaluada",
                       ev["match_score"], json.dumps(ev, ensure_ascii=False))
            notificadas += ok
            log.info("MATCH %d%% — %s (%s)", ev["match_score"], oferta["titulo"], oferta["url"])
        else:
            db.guardar(con, oferta, "evaluada", ev["match_score"],
                       json.dumps(ev, ensure_ascii=False))

    log.info("Fin: %d evaluadas, %d notificadas", evaluadas, notificadas)


if __name__ == "__main__":
    main()
