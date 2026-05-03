from app.tools.gmail import get_emails, summarize_emails

async def handle_email(text: str):
    emails = get_emails()
    return summarize_emails(emails)