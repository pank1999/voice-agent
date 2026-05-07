# JARVIS — Personal AI Voice Assistant

A **native desktop AI voice assistant** for macOS, built with **FastAPI** + **React** + **Electron**. Talk to it via voice or text to manage emails, check your calendar, control your system, track tasks, check the weather, and set up your entire workspace in one command.

**Zero dependencies** — download the `.dmg`, drag to Applications, and go. No Python, no Docker, no terminal required.

---

## Features

### AI & Voice

- **Voice input via Whisper** — click the orb or mic to record; audio sent to OpenAI Whisper for transcription (works in browser and Electron)
- **Text-to-speech** — every response is spoken aloud via Web Speech API
- **Follow-up questions** — JARVIS asks clarifying questions for ambiguous requests
- **Session memory** — conversation context stored locally in SQLite for multi-turn dialog
- **Markdown responses** — bold, lists, headings, inline code, and links rendered in the UI

### Productivity

- **Gmail integration** — read inbox, send emails with confirmation flow
- **Google Calendar** — query today's events
- **To-do list** — add, list, complete, and delete tasks (persisted locally)
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

- **Zero-dependency install** — single `.dmg` download, no Python or Docker needed
- **Onboarding wizard** — first-run setup for OpenAI API key
- **Auto-updater** — checks GitHub releases and prompts to update
- **Bundled backend** — Python backend compiled into the app bundle
- **Draggable window** — drag from the top bar; resize from any edge
- **Native traffic lights** — macOS close/minimize/maximize controls
- **Splash screen** — branded startup experience

---

## Tech Stack

| Layer    | Technology                                   |
| -------- | -------------------------------------------- |
| Frontend | React 19, Vite, TailwindCSS v4, Lucide Icons |
| Desktop  | Electron 31, electron-builder                |
| Backend  | FastAPI, Python 3.11, Uvicorn                |
| AI       | OpenAI GPT-4o-mini (tool-calling), Whisper-1 |
| Email    | Gmail API (google-auth-oauthlib)             |
| Weather  | Open-Meteo API (free, no key required)       |
| Database | SQLite (local, zero setup)                   |
| Bundling | PyInstaller (backend binary)                 |

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
│   │   └── db.py               # SQLite: interactions, todos, reminders
│   ├── config.py               # Env var loading
│   └── main.py                 # FastAPI app + all routes incl. /transcribe
├── electron/
│   ├── main.cjs                # Electron main process (window, backend spawn)
│   └── preload.js              # Context bridge (window.electron)
├── backend.spec                # PyInstaller spec for bundling Python
├── .github/workflows/
│   └── release.yml             # GitHub Actions: auto-build releases
├── frontend/
│   └── src/
│       └── App.jsx             # React UI (VoiceOrb, TasksPanel, chat)
├── run.sh                      # Dev backend start script
└── requirements.txt
```

---

## Quick Start (For Users)

### Download & Install

1. Go to [GitHub Releases](https://github.com/Optimeleon/voice-agent/releases)
2. Download `JARVIS-x.x.x-arm64.dmg` (Apple Silicon) or `JARVIS-x.x.x.dmg` (Intel)
3. Open the `.dmg`, drag JARVIS.app to Applications
4. Launch from Applications folder

### First Run

On first launch, you'll see the onboarding wizard:

1. Enter your **OpenAI API key** ([get one here](https://platform.openai.com/api-keys))
2. Click "Initialize JARVIS"
3. Grant microphone permission when prompted
4. Start talking!

Your API key is stored securely in `~/.jarvis/config.json`. All data (todos, reminders, chat history) is stored locally in `~/.jarvis/data.db`.

### System Requirements

- **macOS 12+** (Monterey or later)
- **Apple Silicon (M1/M2/M3)** or **Intel Mac**
- **Microphone** (for voice input)
- **Internet connection** (for OpenAI API and Gmail)

**Note:** This is a macOS-only app. Windows and Linux support coming in future releases.

---

## Development Setup

### 1. Clone & install deps

```bash
git clone https://github.com/Optimeleon/voice-agent.git
cd voice-agent

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

Create `.env`:

```env
OPENAI_API_KEY=sk-...
```

### 3. Gmail OAuth (optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Library**
2. Enable the **Gmail API** and **Google Calendar API**
3. Go to **Credentials** → create an **OAuth 2.0 Client ID** (Desktop app type)
4. Download the JSON → save as `credentials.json` in the project root
5. Go to **OAuth consent screen** → add your Gmail address as a **Test user**
6. Run the one-time auth flow:

```bash
python -c "from app.tools.gmail import _get_service; _get_service()"
```

A browser tab opens — authorize → `token.json` is saved in the project root.

---

## Running (Development)

### Desktop app (Electron + Vite)

```bash
# Terminal 1 — backend
bash run.sh

# Terminal 2 — Electron + Vite together
cd frontend
npm install
npm run electron:start
```

### Build production desktop app

```bash
# 1. Build Python backend binary
pip install pyinstaller
pyinstaller backend.spec --clean

# 2. Build Electron app
cd frontend
npm install
cp -r ../electron electron
npm run electron:build

# Output: dist-electron/JARVIS-x.x.x-arm64.dmg
```

### Automated GitHub Releases

Push a version tag to trigger the build workflow:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will build the `.dmg` and attach it to a new release automatically.

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

---

## Troubleshooting

### "JARVIS can't be opened because it is from an unidentified developer"

This appears because the app is not code-signed (unsigned). To open:

1. **Right-click** (or Control+click) on JARVIS.app
2. Select **Open** from the context menu
3. Click **Open** in the security dialog

Alternatively, after trying to open once:

```bash
xattr -cr /Applications/JARVIS.app
```

Then open normally.

### Microphone not working

- Ensure JARVIS has microphone permission in **System Settings → Privacy & Security → Microphone**
- If disabled, enable it and restart the app

### Backend won't start / "Backend Not Found" error

This should not happen in the bundled app. If it does:

1. Check `~/.jarvis/` directory exists and is writable
2. Delete `~/.jarvis/` and restart (you'll need to re-enter your API key)
3. Report the issue on [GitHub](https://github.com/Optimeleon/voice-agent/issues)

### Updates not working

Auto-updater requires the app to be in `/Applications/`. If running from Downloads or Desktop, move it to Applications first.
