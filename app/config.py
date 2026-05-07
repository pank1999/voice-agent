import os
import json
import platform
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _load_desktop_config():
    """Load config from JARVIS desktop app config file"""
    config_path = Path.home() / ".jarvis" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# Try desktop config first, fallback to env vars
_desktop_config = _load_desktop_config()

OPENAI_API_KEY = _desktop_config.get("openaiApiKey") or os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Desktop app uses SQLite (no DATABASE_URL needed)
DATABASE_URL = os.getenv("DATABASE_URL")