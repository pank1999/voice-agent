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
                    session_id TEXT NOT NULL DEFAULT 'default',
                    user_input TEXT NOT NULL,
                    intent TEXT,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                ALTER TABLE interactions
                ADD COLUMN IF NOT EXISTS session_id TEXT NOT NULL DEFAULT 'default'
            """)
        conn.commit()


def save_interaction(user_input: str, response: str, intent: str = None, session_id: str = "default"):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO interactions (session_id, user_input, intent, response, created_at) VALUES (%s, %s, %s, %s, %s)",
                (session_id, user_input, intent, response, datetime.utcnow())
            )
        conn.commit()


def get_recent_interactions(limit: int = 10, session_id: str = "default") -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT user_input, intent, response, created_at FROM interactions "
                "WHERE session_id = %s ORDER BY created_at DESC LIMIT %s",
                (session_id, limit)
            )
            rows = cur.fetchall()
    return [dict(r) for r in reversed(rows)]