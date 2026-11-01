"""Self-checks mínimos: parseo JSON del evaluador, dedup de db, formato Telegram.

Correr con: python test_buscador.py
"""
import tempfile
import os
import subprocess
import sys

from buscador import db, evaluador, notificador
from buscador.evaluador import _parsear_json
from buscador.fuentes import coincide_keywords


def test_rutas_configurables():
    subprocess.run(
        [sys.executable, "-c",
         "from buscador import config; from pathlib import Path; "
         "assert config.DB_PATH == Path('/state/check.db'); "
         "assert config.CV_PATH == Path('/profile/check.txt'); "
         "assert config.PREFERENCIAS_PATH == Path('/profile/preferences.txt')"],
        env={**os.environ, "DB_PATH": "/state/check.db",
             "CV_PATH": "/profile/check.txt",
             "PREFERENCIAS_PATH": "/profile/preferences.txt"},
        check=True,
    )


def test_parseo_json():
    # JSON limpio
    ev = _parsear_json('{"match_score": 85, "resumen_puesto": "x"}')
    assert ev["match_score"] == 85
    # JSON envuelto en markdown
    ev = _parsear_json('```json\n{"match_score": "70"}\n```')
    assert ev["match_score"] == 70
    # Sin JSON → error
    try:
        _parsear_json("no hay json acá")
        assert False, "debía fallar"
    except ValueError:
        pass


def test_evaluar_via_litellm():
    class Respuesta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {
                "content": '{"match_score": 82, "resumen_puesto": "x"}'
            }}]}

    llamada = {}

    def post(url, **kwargs):
        llamada.update(url=url, **kwargs)
        return Respuesta()

    original_post = evaluador.requests.post
    evaluador.requests.post = post
    try:
        resultado = evaluador.evaluar(
            {"url": "https://example.test/job", "titulo": "Analista"},
            "cv de prueba", "preferencias de prueba",
        )
    finally:
        evaluador.requests.post = original_post

    assert resultado["match_score"] == 82
    assert llamada["url"] == evaluador.config.LITELLM_API_BASE.rstrip("/") + "/chat/completions"
    assert llamada["headers"]["Authorization"] == f"Bearer {evaluador.config.LITELLM_TOKEN}"
    assert llamada["json"]["model"] == evaluador.config.LITELLM_MODEL
    assert llamada["json"]["response_format"] == {"type": "json_object"}
    assert llamada["verify"] is False


def test_dedup():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        con = db.conectar(f.name)
        oferta = {"url": "http://x/1", "titulo": "Admin", "empresa": "ACME", "fuente": "test"}
        assert db.es_nueva(con, oferta["url"])
        db.guardar(con, oferta, "evaluada", 50, "{}")
        assert not db.es_nueva(con, oferta["url"])
        # Upsert no duplica
        db.guardar(con, oferta, "notificada", 90, "{}")
        filas = con.execute("SELECT COUNT(*), MAX(score) FROM ofertas").fetchone()
        assert filas == (1, 90)


def test_keywords_y_formato():
    assert coincide_keywords({"titulo": "Analista de RRHH", "descripcion": ""})
    assert not coincide_keywords({"titulo": "Chief Legal Officer", "descripcion": "law firm"})
    msg = notificador.formatear(
        {"url": "http://x", "titulo": "Admin <b>", "empresa": "ACME"},
        {"match_score": 88, "resumen_puesto": "r", "puntos_fuertes": ["a"],
         "gaps_o_faltantes": [], "carta_presentacion_sugerida": "hola"},
    )
    assert "88%" in msg and "&lt;b&gt;" in msg  # escapa HTML del título


def test_scraper_parsers():
    # Fixtures mínimas offline: si cambia el HTML de los sitios, esto no lo detecta,
    # pero sí detecta roturas en nuestras regex/parseo.
    from scraper.linkedin import _tarjetas
    from scraper.computrabajo import _jobposting
    li = ('<li><a href="https://ar.linkedin.com/jobs/view/admin-at-acme-123?x=1">'
          '<h3 class="base-search-card__title"> Admin &amp; RRHH </h3>'
          '<h4 class="base-search-card__subtitle"><a>ACME</a></h4>'
          '<span class="job-search-card__location"> CABA </span></li>')
    t = list(_tarjetas(li))
    assert t == [("https://www.linkedin.com/jobs/view/123", "123",
                  "Admin & RRHH", "ACME", "CABA")]
    ct = ('<script type="application/ld+json">{"@graph": [{"@type": "WebPage"},'
          '{"@type": "JobPosting", "title": "Data Entry"}]}</script>')
    assert _jobposting(ct)["title"] == "Data Entry"
    assert _jobposting("<html>sin json</html>") is None


if __name__ == "__main__":
    test_rutas_configurables()
    test_parseo_json()
    test_evaluar_via_litellm()
    test_dedup()
    test_keywords_y_formato()
    test_scraper_parsers()
    print("OK: todos los checks pasaron")
