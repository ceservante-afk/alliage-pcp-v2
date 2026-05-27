import os
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import lru_cache

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_conn():
    """Get a database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def execute(sql: str, params=None, fetch=True):
    """Execute a query and return results."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount
