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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL DEFAULT 'default',
                    title TEXT NOT NULL,
                    remind_at TIMESTAMP,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()


# ── Todos ──────────────────────────────────────────────────────────────────────

def add_todo(title: str, session_id: str = "default") -> dict:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO todos (session_id, title) VALUES (%s, %s) RETURNING id, title, done, created_at",
                (session_id, title),
            )
            row = dict(cur.fetchone())
        conn.commit()
    return row


def get_todos(session_id: str = "default", include_done: bool = False) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if include_done:
                cur.execute(
                    "SELECT id, title, done, created_at FROM todos WHERE session_id = %s ORDER BY created_at ASC",
                    (session_id,),
                )
            else:
                cur.execute(
                    "SELECT id, title, done, created_at FROM todos WHERE session_id = %s AND done = FALSE ORDER BY created_at ASC",
                    (session_id,),
                )
            return [dict(r) for r in cur.fetchall()]


def complete_todo(todo_id: int, session_id: str = "default") -> bool:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE todos SET done = TRUE WHERE id = %s AND session_id = %s",
                (todo_id, session_id),
            )
            updated = cur.rowcount > 0
        conn.commit()
    return updated


def delete_todo(todo_id: int, session_id: str = "default") -> bool:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM todos WHERE id = %s AND session_id = %s",
                (todo_id, session_id),
            )
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


# ── Reminders ──────────────────────────────────────────────────────────────────

def add_reminder(title: str, remind_at=None, session_id: str = "default") -> dict:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO reminders (session_id, title, remind_at) VALUES (%s, %s, %s) RETURNING id, title, remind_at, done, created_at",
                (session_id, title, remind_at),
            )
            row = dict(cur.fetchone())
        conn.commit()
    return row


def get_reminders(session_id: str = "default", include_done: bool = False) -> list[dict]:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if include_done:
                cur.execute(
                    "SELECT id, title, remind_at, done, created_at FROM reminders WHERE session_id = %s ORDER BY remind_at ASC NULLS LAST",
                    (session_id,),
                )
            else:
                cur.execute(
                    "SELECT id, title, remind_at, done, created_at FROM reminders WHERE session_id = %s AND done = FALSE ORDER BY remind_at ASC NULLS LAST",
                    (session_id,),
                )
            return [dict(r) for r in cur.fetchall()]


def complete_reminder(reminder_id: int, session_id: str = "default") -> bool:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE reminders SET done = TRUE WHERE id = %s AND session_id = %s",
                (reminder_id, session_id),
            )
            updated = cur.rowcount > 0
        conn.commit()
    return updated


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