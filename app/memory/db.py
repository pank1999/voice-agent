import psycopg2
import psycopg2.extras
from datetime import datetime
from app.config import DATABASE_URL


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id SERIAL PRIMARY KEY,
                    user_input TEXT NOT NULL,
                    intent TEXT,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()


def save_interaction(user_input: str, response: str, intent: str = None):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO interactions (user_input, intent, response, created_at) VALUES (%s, %s, %s, %s)",
                (user_input, intent, response, datetime.utcnow())
            )
        conn.commit()


def get_recent_interactions(limit: int = 10) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_input, intent, response, created_at FROM interactions ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            rows = cur.fetchall()
    return [dict(r) for r in reversed(rows)]