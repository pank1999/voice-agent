from datetime import datetime
from app.memory.db import (
    add_todo as db_add_todo,
    get_todos as db_get_todos,
    complete_todo as db_complete_todo,
    add_reminder as db_add_reminder,
    get_reminders as db_get_reminders,
    complete_reminder as db_complete_reminder,
)


def _fmt_time(ts) -> str:
    if ts is None:
        return "No time set"
    if isinstance(ts, str):
        return ts
    return ts.strftime("%b %d, %Y %I:%M %p")


def tool_add_todo(title: str, session_id: str = "default") -> str:
    row = db_add_todo(title, session_id=session_id)
    return f"Added to your to-do list: **{row['title']}** (#{row['id']})"


def tool_list_todos(session_id: str = "default") -> str:
    todos = db_get_todos(session_id=session_id, include_done=False)
    if not todos:
        return "Your to-do list is empty! Say 'Add todo: buy groceries' to get started."
    lines = [f"**Your To-Do List** ({len(todos)} pending)\n"]
    for t in todos:
        lines.append(f"- #{t['id']} {t['title']}")
    return "\n".join(lines)


def tool_complete_todo(todo_id: int, session_id: str = "default") -> str:
    success = db_complete_todo(todo_id, session_id=session_id)
    if success:
        return f"Marked todo #{todo_id} as complete!"
    return f"Couldn't find todo #{todo_id} in your list."


def tool_set_reminder(title: str, remind_at_str: str = None, session_id: str = "default") -> str:
    remind_at = None
    if remind_at_str:
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                remind_at = datetime.strptime(remind_at_str, fmt)
                break
            except ValueError:
                continue

    row = db_add_reminder(title, remind_at=remind_at, session_id=session_id)
    time_str = _fmt_time(row["remind_at"])
    return f"Reminder set: **{row['title']}** — {time_str} (#{row['id']})"


def tool_list_reminders(session_id: str = "default") -> str:
    reminders = db_get_reminders(session_id=session_id, include_done=False)
    if not reminders:
        return "No reminders set. Say 'Remind me to call John tomorrow at 9am' to add one."
    lines = [f"**Your Reminders** ({len(reminders)} active)\n"]
    for r in reminders:
        time_str = _fmt_time(r["remind_at"])
        lines.append(f"- #{r['id']} **{r['title']}** — {time_str}")
    return "\n".join(lines)


def tool_complete_reminder(reminder_id: int, session_id: str = "default") -> str:
    success = db_complete_reminder(reminder_id, session_id=session_id)
    if success:
        return f"Dismissed reminder #{reminder_id}."
    return f"Couldn't find reminder #{reminder_id}."
