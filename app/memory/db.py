import sqlite3
from datetime import datetime
from pathlib import Path
import os

# Use SQLite for desktop app - stored in user's home directory
DB_DIR = Path.home() / ".jarvis"
DB_PATH = DB_DIR / "data.db"

def _get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL DEFAULT 'default',
            user_input TEXT NOT NULL,
            intent TEXT,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS easily
    # Check if column exists by trying to select it
    try:
        cur.execute("SELECT session_id FROM interactions LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE interactions ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL DEFAULT 'default',
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL DEFAULT 'default',
            title TEXT NOT NULL,
            remind_at TIMESTAMP,
            done BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# ── Todos ──────────────────────────────────────────────────────────────────────

def add_todo(title: str, session_id: str = "default") -> dict:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO todos (session_id, title) VALUES (?, ?)",
        (session_id, title),
    )
    todo_id = cur.lastrowid
    cur.execute(
        "SELECT id, title, done, created_at FROM todos WHERE id = ?",
        (todo_id,)
    )
    row = dict(cur.fetchone())
    conn.commit()
    cur.close()
    conn.close()
    return row


def get_todos(session_id: str = "default", include_done: bool = False) -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    if include_done:
        cur.execute(
            "SELECT id, title, done, created_at FROM todos WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
    else:
        cur.execute(
            "SELECT id, title, done, created_at FROM todos WHERE session_id = ? AND done = 0 ORDER BY created_at ASC",
            (session_id,),
        )
    result = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return result


def complete_todo(todo_id: int, session_id: str = "default") -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE todos SET done = 1 WHERE id = ? AND session_id = ?",
        (todo_id, session_id),
    )
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated


def delete_todo(todo_id: int, session_id: str = "default") -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM todos WHERE id = ? AND session_id = ?",
        (todo_id, session_id),
    )
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted


# ── Reminders ──────────────────────────────────────────────────────────────────

def add_reminder(title: str, remind_at=None, session_id: str = "default") -> dict:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (session_id, title, remind_at) VALUES (?, ?, ?)",
        (session_id, title, remind_at),
    )
    reminder_id = cur.lastrowid
    cur.execute(
        "SELECT id, title, remind_at, done, created_at FROM reminders WHERE id = ?",
        (reminder_id,)
    )
    row = dict(cur.fetchone())
    conn.commit()
    cur.close()
    conn.close()
    return row


def get_reminders(session_id: str = "default", include_done: bool = False) -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    if include_done:
        cur.execute(
            "SELECT id, title, remind_at, done, created_at FROM reminders WHERE session_id = ? ORDER BY remind_at ASC",
            (session_id,),
        )
    else:
        cur.execute(
            "SELECT id, title, remind_at, done, created_at FROM reminders WHERE session_id = ? AND done = 0 ORDER BY remind_at ASC",
            (session_id,),
        )
    result = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return result


def complete_reminder(reminder_id: int, session_id: str = "default") -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reminders SET done = 1 WHERE id = ? AND session_id = ?",
        (reminder_id, session_id),
    )
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated


def save_interaction(user_input: str, response: str, intent: str = None, session_id: str = "default"):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interactions (session_id, user_input, intent, response, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_input, intent, response, datetime.utcnow().isoformat())
    )
    conn.commit()
    cur.close()
    conn.close()


def get_recent_interactions(limit: int = 10, session_id: str = "default") -> list[dict]:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_input, intent, response, created_at FROM interactions "
        "WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
        (session_id, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in reversed(rows)]