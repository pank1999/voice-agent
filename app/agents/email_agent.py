from app.tools.gmail import get_emails, send_email, summarize_emails


async def handle_list_emails(max_results: int = 5) -> str:
    emails = get_emails(max_results=max_results)
    return summarize_emails(emails)


async def handle_send_email(to: str, subject: str, body: str) -> str:
    result = send_email(to=to, subject=subject, body=body)
    return f"Email sent to {to} (message id: {result['message_id']})."