import json
from openai import OpenAI
from app.agents.email_agent import handle_list_emails, handle_send_email
from app.agents.calendar_agent import handle_calendar
from app.memory.db import get_recent_interactions, save_interaction

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "Fetch and summarize the user's latest inbox emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of emails to fetch (default 5).",
                        "default": 5,
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email on the user's behalf. Requires explicit confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address."},
                    "subject": {"type": "string", "description": "Email subject line."},
                    "body": {"type": "string", "description": "Email body text."},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": "Get today's calendar events for the user.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

REQUIRES_CONFIRMATION = {"send_email"}


def _build_messages(text: str) -> list[dict]:
    history = get_recent_interactions(limit=6)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful voice assistant. You can read emails, send emails, "
                "and check calendar events. Use the provided tools to fulfill requests. "
                "For send_email, always call the tool so the user can confirm before sending."
            ),
        }
    ]
    for item in history:
        messages.append({"role": "user", "content": item["user_input"]})
        messages.append({"role": "assistant", "content": item["response"]})
    messages.append({"role": "user", "content": text})
    return messages


async def handle_user_input(text: str) -> dict:
    messages = _build_messages(text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if fn_name in REQUIRES_CONFIRMATION:
            return {
                "status": "needs_confirmation",
                "action": fn_name,
                "args": fn_args,
                "message": (
                    f"I'm about to send an email to {fn_args.get('to')} "
                    f"with subject \"{fn_args.get('subject')}\". "
                    "Reply with /confirm to proceed or /cancel to abort."
                ),
            }

        if fn_name == "list_emails":
            result = await handle_list_emails(fn_args.get("max_results", 5))
        elif fn_name == "get_calendar":
            result = await handle_calendar(text)
        else:
            result = "Unknown tool called."

        save_interaction(text, result, intent=fn_name)
        return {"status": "ok", "response": result}

    text_response = choice.message.content or "I can help with email and calendar."
    save_interaction(text, text_response, intent="general")
    return {"status": "ok", "response": text_response}


async def execute_confirmed_action(action: str, args: dict) -> dict:
    if action == "send_email":
        result = await handle_send_email(args["to"], args["subject"], args["body"])
        save_interaction(
            f"[confirmed] send_email to {args['to']}",
            result,
            intent="send_email",
        )
        return {"status": "ok", "response": result}
    return {"status": "error", "response": "Unknown action."}