# JARVIS — Personal AI Voice Assistant

A full-stack AI voice assistant built with **FastAPI** + **React** (Vite). Talk to it via voice or text to read emails, check your calendar, and get answers about Pankaj Pandey's professional background. Responses are spoken aloud using the browser's Web Speech API.

---

## Features

- **Voice input** — click the orb or mic button to speak; auto-submits on silence
- **Text-to-speech** — every assistant response is read aloud
- **Gmail integration** — read inbox emails and send emails with confirmation flow
- **Calendar integration** — query today's calendar events
- **Personal context** — JARVIS knows Pankaj's background, skills, projects, and experience
- **Conversation memory** — recent interactions stored in PostgreSQL for context
- **Jarvis-style UI** — full-page split layout with animated voice orb, glassmorphic chat bubbles, and rich markdown rendering
- **Markdown responses** — bold, lists, headings, inline code, and links rendered beautifully

---

## Tech Stack

| Layer      | Technology                                   |
| ---------- | -------------------------------------------- |
| Frontend   | React 19, Vite, TailwindCSS v4, Lucide Icons |
| Backend    | FastAPI, Python 3.11, Uvicorn                |
| AI         | OpenAI GPT-4o-mini (tool-calling)            |
| Email      | Gmail API (google-auth-oauthlib)             |
| Database   | PostgreSQL (psycopg2)                        |
| Containers | Docker, Docker Compose                       |

---

## Project Structure

```
voice-agent/
├── app/
│   ├── agents/
│   │   ├── orchestrator.py     # Intent routing via OpenAI tool-calling
│   │   ├── email_agent.py      # Email read/send handlers
│   │   └── calendar_agent.py   # Calendar handler
│   ├── tools/
│   │   └── gmail.py            # Gmail API client
│   ├── memory/
│   │   └── db.py               # PostgreSQL interaction history
│   ├── config.py               # Env var loading
│   └── main.py                 # FastAPI app + routes
├── frontend/
│   └── src/
│       └── App.jsx             # React UI (VoiceOrb, MarkdownContent, chat)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/pank1999/voice-agent.git
cd voice-agent

python -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://voice_user:voice_pass@localhost:5432/voice_agent
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

### 3. Gmail OAuth setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Library**
2. Enable the **Gmail API**
3. Go to **Credentials** → create an **OAuth 2.0 Client ID** (Desktop app type)
4. Download the JSON → save as `credentials.json` in the project root
5. Go to **OAuth consent screen** → add your Gmail address as a **Test user**
6. Run the one-time auth flow locally:

```bash
python -c "from app.tools.gmail import _get_service; _get_service()"
```

A browser tab opens — authorize → `token.json` is written automatically.

### 4. Run with Docker

```bash
docker compose up --build
```

Backend available at `http://localhost:8000`

### 5. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`

---

## API Routes

| Method | Route      | Description                                |
| ------ | ---------- | ------------------------------------------ |
| `GET`  | `/`        | Health check                               |
| `POST` | `/command` | Send a text/voice command                  |
| `POST` | `/confirm` | Confirm a pending action (e.g. send email) |
| `POST` | `/cancel`  | Cancel a pending action                    |

### `/command` payload

```json
{
  "session_id": "uuid",
  "text": "Show my latest emails"
}
```

---

## Voice Usage

- **Click the orb** (left panel) or the **mic button** (input bar) to start listening
- Speak your command — it auto-submits when you stop talking
- Click again to stop early
- Works in **Chrome**, **Edge**, and **Safari** (Firefox unsupported)

---

## Example Commands

```
Show my latest emails
What's on my calendar today?
Send an email to john@example.com with subject "Hello" saying "How are you?"
Who is Pankaj?
What technologies does Pankaj know?
Tell me about the Marketing SaaS project
```
