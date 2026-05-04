from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.agents.orchestrator import handle_user_input, execute_confirmed_action
from app.memory.db import init_db

_pending_actions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "voice-agent running"}


@app.post("/command")
async def process_command(payload: dict):
    session_id = payload.get("session_id", "default")
    user_input = payload.get("text")
    if not user_input:
        raise HTTPException(status_code=400, detail="Missing 'text' field")

    result = await handle_user_input(user_input)

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
    return await execute_confirmed_action(pending["action"], pending["args"])


@app.post("/cancel")
async def cancel_action(payload: dict):
    session_id = payload.get("session_id", "default")
    _pending_actions.pop(session_id, None)
    return {"status": "cancelled", "message": "Action cancelled."}