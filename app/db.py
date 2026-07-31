import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

_url = urlparse(os.environ.get("DATABASE_URL", ""))

DB_PARAMS = {
    "host":     _url.hostname,
    "port":     _url.port or 5432,
    "dbname":   _url.path.lstrip("/"),
    "user":     _url.username,
    "password": _url.password,
    "sslmode":  "require",
}

def get_conn():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)

def execute(sql: str, params=None, fetch=True):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount
