from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from app.agents.orchestrator import handle_user_input, execute_confirmed_action
from app.memory.db import (
    init_db,
    get_todos, complete_todo, delete_todo,
    get_reminders, complete_reminder,
)

_pending_actions: dict[str, dict] = {}
_openai = OpenAI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# CORS: allow all for desktop app, localhost only for dev
import os
if os.getenv("JARVIS_DESKTOP"):
    origins = ["*"]  # Desktop app - allow all
else:
    origins = ["http://localhost:5173"]  # Dev mode only

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    import tempfile, os
    suffix = "." + (file.filename.split(".")[-1] if file.filename and "." in file.filename else "webm")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            result = _openai.audio.transcriptions.create(model="whisper-1", file=f)
        return {"text": result.text}
    finally:
        os.unlink(tmp_path)


@app.get("/")
def read_root():
    return {"status": "voice-agent running"}


@app.post("/command")
async def process_command(payload: dict):
    session_id = payload.get("session_id", "default")
    user_input = payload.get("text")
    if not user_input:
        raise HTTPException(status_code=400, detail="Missing 'text' field")

    result = await handle_user_input(user_input, session_id=session_id)

    if result.get("status") == "needs_confirmation":
        _pending_actions[session_id] = {
            "action": result["action"],
            "args": result["args"],
        }
        return {"status": "needs_confirmation", "message": result["message"]}

    return result


@app.post("/confirm")
async def confirm_action(payload: dict):
    session_id = payload.get("session_id", "default")
    pending = _pending_actions.pop(session_id, None)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending action for this session")
    return await execute_confirmed_action(pending["action"], pending["args"], session_id=session_id)


@app.post("/cancel")
async def cancel_action(payload: dict):
    session_id = payload.get("session_id", "default")
    _pending_actions.pop(session_id, None)
    return {"status": "cancelled", "message": "Action cancelled."}


@app.get("/todos")
def list_todos(session_id: str = "default"):
    return {"todos": get_todos(session_id=session_id, include_done=False)}


@app.patch("/todos/{todo_id}/complete")
def mark_todo_done(todo_id: int, payload: dict = {}):
    session_id = payload.get("session_id", "default")
    complete_todo(todo_id, session_id=session_id)
    return {"status": "ok"}


@app.delete("/todos/{todo_id}")
def remove_todo(todo_id: int, session_id: str = "default"):
    delete_todo(todo_id, session_id=session_id)
    return {"status": "ok"}


@app.get("/reminders")
def list_reminders(session_id: str = "default"):
    items = get_reminders(session_id=session_id, include_done=False)
    for r in items:
        if r.get("remind_at"):
            r["remind_at"] = r["remind_at"].isoformat()
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return {"reminders": items}


@app.patch("/reminders/{reminder_id}/complete")
def mark_reminder_done(reminder_id: int, payload: dict = {}):
    session_id = payload.get("session_id", "default")
    complete_reminder(reminder_id, session_id=session_id)
    return {"status": "ok"}