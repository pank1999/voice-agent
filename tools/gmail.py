def get_emails():
    return [
        {"subject": "Team Meeting", "body": "Discuss roadmap at 3PM"},
        {"subject": "Discount Offer", "body": "50% off on tools"}
    ]

def summarize_emails(emails):
    return "Your emails:\n" + "\n".join([f"- {e['subject']}" for e in emails])