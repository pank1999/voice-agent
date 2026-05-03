from openai import OpenAI
from app.agents.email_agent import handle_email
from app.agents.calendar_agent import handle_calendar

client = OpenAI()

async def handle_user_input(text: str):
    prompt = f"""
    Classify intent into one of:
    - email
    - calendar
    - general

    Input: {text}
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    intent = res.choices[0].message.content.lower()

    if "email" in intent:
        return await handle_email(text)
    elif "calendar" in intent:
        return await handle_calendar(text)
    else:
        return "I can help with email and calendar right now."