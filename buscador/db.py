"""Capa SQLite: dedup de ofertas y registro de evaluaciones."""
import sqlite3

from . import config

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS ofertas (
    url TEXT PRIMARY KEY,
    titulo TEXT,
    empresa TEXT,
    fuente TEXT,
    score INTEGER,
    estado TEXT,            -- descartada_keyword | evaluada | notificada | error
    json_eval TEXT,
    creada_en TEXT DEFAULT (datetime('now')),
    actualizada_en TEXT DEFAULT (datetime('now'))
);
"""


def conectar(path=None):
    con = sqlite3.connect(path or config.DB_PATH)
    con.execute(_ESQUEMA)
    return con


def es_nueva(con, url):
    # Las ofertas con estado 'error' se reintentan en la próxima corrida
    return con.execute(
        "SELECT 1 FROM ofertas WHERE url = ? AND estado != 'error'", (url,)
    ).fetchone() is None


def urls_existentes(con):
    return frozenset(u for (u,) in con.execute(
        "SELECT url FROM ofertas WHERE estado != 'error'"))


def guardar(con, oferta, estado, score=None, json_eval=None):
    con.execute(
        """INSERT INTO ofertas (url, titulo, empresa, fuente, score, estado, json_eval)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(url) DO UPDATE SET
             score=excluded.score, estado=excluded.estado,
             json_eval=excluded.json_eval, actualizada_en=datetime('now')""",
        (oferta["url"], oferta["titulo"], oferta.get("empresa", ""),
         oferta.get("fuente", ""), score, estado, json_eval),
    )
    con.commit()
