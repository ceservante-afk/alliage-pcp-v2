import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_PARAMS = {
    "host":     os.environ["DB_HOST"],
    "port":     int(os.environ.get("DB_PORT", "5432")),
    "dbname":   os.environ["DB_NAME"],
    "user":     os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
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
