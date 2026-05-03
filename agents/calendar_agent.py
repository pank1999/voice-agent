from app.tools.calendar import get_today_events

async def handle_calendar(text: str):
    events = get_today_events()

    if not events:
        return "You have no events today."

    return "\n".join([f"{e['time']} - {e['title']}" for e in events])