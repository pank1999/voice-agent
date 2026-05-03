from fastapi import FastAPI
from app.agents.orchestrator import handle_user_input

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/command")
async def process_command(payload: dict):
    user_input = payload.get("text")
    response = await handle_user_input(user_input)
    return {"response": response}