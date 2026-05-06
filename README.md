# JARVIS — Personal AI Voice Assistant

A full-stack AI voice assistant and **desktop app** built with **FastAPI** + **React** (Vite) + **Electron**. Talk to it via voice or text to manage emails, check your calendar, control your system, track tasks, check the weather, and set up your entire workspace in one command.

---

## Features

### AI & Voice

- **Voice input via Whisper** — click the orb or mic to record; audio sent to OpenAI Whisper for transcription (works in browser and Electron)
- **Text-to-speech** — every response is spoken aloud via Web Speech API
- **Follow-up questions** — JARVIS asks clarifying questions for ambiguous requests
- **Session memory** — conversation context stored per-session in PostgreSQL for multi-turn dialog
- **Markdown responses** — bold, lists, headings, inline code, and links rendered in the UI

### Productivity

- **Gmail integration** — read inbox, send emails with confirmation flow
- **Google Calendar** — query today's events
- **To-do list** — add, list, complete, and delete tasks (persisted in PostgreSQL)
- **Reminders** — set timed reminders with natural language dates
- **Tasks & Reminders panel** — dedicated side panel in the UI to view and manage tasks

### System Control (macOS)

- **Open apps** — launch any desktop application by name
- **Open URLs** — open websites in the default browser
- **Search Google** — fire a Google search from voice
- **Open YouTube** — search and open YouTube videos
- **Music control** — play, pause, next, previous via Spotify/Apple Music
- **Weather** — real-time weather for any city via Open-Meteo (no API key needed)

### Workspace Setup

- **One-command workspace** — say "set up my workspace" to launch apps and open browser tabs in one shot
- **Configurable presets** — `default`, `work`, `focus`, `social` (edit `app/tools/system.py`)

| Preset    | Apps              | Browser tabs                            |
| --------- | ----------------- | --------------------------------------- |
| `default` | Windsurf, Discord | GitHub, ClickUp, Gmail                  |
| `work`    | Windsurf, Discord | GitHub, ClickUp, Gmail, Google Calendar |
| `focus`   | Windsurf          | GitHub                                  |
| `social`  | Discord           | Twitter, YouTube                        |

### Desktop App

- **Electron wrapper** — runs as a native macOS/Windows/Linux desktop app
- **Auto-starts backend** — spawns uvicorn on launch in production mode
- **Draggable window** — drag from the top bar; resize from any edge
- **Native traffic lights** — macOS close/minimize/maximize controls

---

## Tech Stack

| Layer      | Technology                                   |
| ---------- | -------------------------------------------- |
| Frontend   | React 19, Vite, TailwindCSS v4, Lucide Icons |
| Desktop    | Electron 31, electron-builder                |
| Backend    | FastAPI, Python 3.11, Uvicorn                |
| AI         | OpenAI GPT-4o-mini (tool-calling), Whisper-1 |
| Email      | Gmail API (google-auth-oauthlib)             |
| Weather    | Open-Meteo API (free, no key required)       |
| Database   | PostgreSQL (psycopg2)                        |
| Containers | Docker, Docker Compose (DB only)             |

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
│   │   ├── gmail.py            # Gmail API client
│   │   ├── system.py           # macOS system tools + workspace presets
│   │   ├── weather.py          # Open-Meteo weather queries
│   │   └── tasks.py            # Todo & reminder CRUD
│   ├── memory/
│   │   └── db.py               # PostgreSQL: interactions, todos, reminders
│   ├── config.py               # Env var loading
│   └── main.py                 # FastAPI app + all routes incl. /transcribe
├── electron/
│   ├── main.js                 # Electron main process (window, backend spawn)
│   └── preload.js              # Context bridge (window.electron)
├── frontend/
│   └── src/
│       └── App.jsx             # React UI (VoiceOrb, TasksPanel, chat)
├── docker-compose.yml          # PostgreSQL only
├── run.sh                      # Dev backend start script
└── requirements.txt
```

---

## Setup

### 1. Clone & install Python deps

```bash
git clone https://github.com/Optimeleon/voice-agent.git
cd voice-agent

python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
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

### 3. Start the database

```bash
docker compose up -d db
```

### 4. Gmail OAuth setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Library**
2. Enable the **Gmail API** and **Google Calendar API**
3. Go to **Credentials** → create an **OAuth 2.0 Client ID** (Desktop app type)
4. Download the JSON → save as `credentials.json` in the project root
5. Go to **OAuth consent screen** → add your Gmail address as a **Test user**
6. Run the one-time auth flow:

```bash
python -c "from app.tools.gmail import _get_service; _get_service()"
```

A browser tab opens — authorize → `token.json` is saved automatically.

---

## Running

### Web mode (browser)

```bash
# Terminal 1 — backend
bash run.sh

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### Desktop app (Electron)

```bash
# Terminal 1 — backend
bash run.sh

# Terminal 2 — Electron + Vite together
cd frontend
npm install
npm run electron:start
```

### Build distributable desktop app

```bash
cd frontend

# macOS (.dmg)
npm run electron:build

# Windows (.exe installer)
npm run electron:build:win

# Linux (.AppImage)
npm run electron:build:linux
```

Output goes to `dist-electron/`.

---

## API Routes

| Method   | Route                      | Description                                |
| -------- | -------------------------- | ------------------------------------------ |
| `GET`    | `/`                        | Health check                               |
| `POST`   | `/command`                 | Send a text command                        |
| `POST`   | `/transcribe`              | Upload audio blob → Whisper transcription  |
| `POST`   | `/confirm`                 | Confirm a pending action (e.g. send email) |
| `POST`   | `/cancel`                  | Cancel a pending action                    |
| `GET`    | `/todos`                   | List todos for a session                   |
| `PATCH`  | `/todos/{id}/complete`     | Mark a todo as done                        |
| `DELETE` | `/todos/{id}`              | Delete a todo                              |
| `GET`    | `/reminders`               | List reminders for a session               |
| `PATCH`  | `/reminders/{id}/complete` | Dismiss a reminder                         |

---

## Example Commands

```
# Email & Calendar
Show my latest emails
What's on my calendar today?
Send an email to john@example.com saying "Are you free tomorrow?"

# Tasks
Add todo: Review pull requests
Show my todos
Mark todo 1 as done
Remind me to call John tomorrow at 9am
Show my reminders

# Weather
How's the weather in Delhi today?
What's the forecast for Mumbai?

# System
Open Spotify
Play music
Search Google for FastAPI tutorial
Open YouTube and search for lo-fi music

# Workspace
Set up my workspace
Set up focus mode
Set up my work environment
Start my day

# About Pankaj
Who is Pankaj?
What technologies does Pankaj know?
Tell me about his projects
```

---

## Customizing Workspace Presets

Edit `WORKSPACE_PRESETS` in `app/tools/system.py`:

```python
"default": {
    "apps": ["Windsurf", "Discord"],
    "urls": [
        "https://github.com/YourUsername",
        "https://app.clickup.com/your-workspace",
        "https://mail.google.com",
    ],
},
```

Add new presets by adding a new key — then update the `enum` in the `setup_workspace` tool definition in `app/agents/orchestrator.py`.
