import sys
import subprocess
import urllib.parse
import webbrowser


def _is_mac() -> bool:
    return sys.platform == "darwin"


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if _is_mac():
        result = subprocess.run(["open", url], capture_output=True)
        if result.returncode == 0:
            return f"Opened {url} in your browser."
        return f"Failed to open URL: {result.stderr.decode().strip()}"
    webbrowser.open(url)
    return f"Opened {url} in your browser."


def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)


def open_youtube(query: str = None) -> str:
    if query:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = "https://www.youtube.com"
    return open_url(url)


def open_app(name: str) -> str:
    if _is_mac():
        result = subprocess.run(["open", "-a", name], capture_output=True)
        if result.returncode == 0:
            return f"Opened {name}."
        stderr = result.stderr.decode().strip()
        return f"Could not open \"{name}\". Make sure the app is installed. ({stderr})"
    if sys.platform == "win32":
        result = subprocess.run(["start", name], shell=True, capture_output=True)
        return f"Tried to open {name}." if result.returncode == 0 else f"Could not open {name}."
    result = subprocess.run(["xdg-open", name], capture_output=True)
    return f"Tried to open {name}." if result.returncode == 0 else f"Could not open {name}."


WORKSPACE_PRESETS: dict[str, dict] = {
    "default": {
        "apps": ["Windsurf", "Discord"],
        "urls": [
            "https://github.com/Optimeleon",
            "https://app.clickup.com/9012320528/v/l/6-901212169458-1",
            "https://mail.google.com",
        ],
    },
    "work": {
        "apps": ["Windsurf", "Discord"],
        "urls": [
            "https://github.com/Optimeleon",
            "https://app.clickup.com/9012320528/v/l/6-901212169458-1",
            "https://mail.google.com",
            "https://calendar.google.com",
        ],
    },
    "focus": {
        "apps": ["Windsurf"],
        "urls": [
            "https://github.com/Optimeleon",
        ],
    },
    "social": {
        "apps": ["Discord"],
        "urls": [
            "https://twitter.com",
            "https://www.youtube.com",
        ],
    },
}


def setup_workspace(preset: str = "default") -> str:
    key = preset.lower().strip()
    config = WORKSPACE_PRESETS.get(key, WORKSPACE_PRESETS["default"])

    apps = config.get("apps", [])
    urls = config.get("urls", [])
    results = []
    failed = []

    for app in apps:
        res = open_app(app)
        if "Could not open" in res or "doesn't appear" in res:
            failed.append(f"App: {app}")
        else:
            results.append(app)

    import time
    time.sleep(0.5)

    for url in urls:
        open_url(url)
        results.append(url)

    launched_apps = [r for r in results if not r.startswith("http")]
    opened_urls = [r for r in results if r.startswith("http")]

    preset_phrases = {
        "default": "your default workspace",
        "work":    "your work environment",
        "focus":   "focus mode",
        "social":  "your social setup",
    }
    label = preset_phrases.get(key, f"your {key} workspace")

    if not results and not failed:
        return "Workspace setup complete."

    parts = []
    if launched_apps:
        if len(launched_apps) == 1:
            parts.append(f"I've launched {launched_apps[0]}")
        else:
            parts.append(f"I've launched {', '.join(launched_apps[:-1])} and {launched_apps[-1]}")
    if opened_urls:
        count = len(opened_urls)
        parts.append(f"opened {count} browser {'tab' if count == 1 else 'tabs'} for you")

    action_summary = " and ".join(parts)

    if failed:
        failed_names = [f.replace("App: ", "") for f in failed]
        fail_note = f" I couldn't open {', '.join(failed_names)}, you may need to install {'it' if len(failed_names) == 1 else 'them'}."
    else:
        fail_note = ""

    return f"Sir, {label} is ready. {action_summary}.{fail_note} You're all set to start working."


def _applescript_music(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def control_music(action: str, service: str = "spotify") -> str:
    if not _is_mac():
        return "Music controls via AppleScript are only supported on macOS."

    app_name = "Spotify" if service.lower() == "spotify" else "Music"

    scripts = {
        "play": f'tell application "{app_name}" to play',
        "pause": f'tell application "{app_name}" to pause',
        "next": f'tell application "{app_name}" to next track',
        "previous": f'tell application "{app_name}" to previous track',
        "toggle": f'tell application "{app_name}" to playpause',
    }

    action = action.lower()
    if action not in scripts:
        return f"Unknown music action '{action}'. Try: play, pause, next, previous, toggle."

    _, code = _applescript_music(scripts[action])
    app_display = app_name

    if code != 0:
        open_result = subprocess.run(["open", "-a", app_name], capture_output=True)
        if open_result.returncode != 0:
            return f"{app_display} doesn't appear to be installed."
        if action in ("play", "toggle"):
            _applescript_music(scripts["play"])
            return f"Opened {app_display} and started playing."
        return f"Opened {app_display}."

    labels = {
        "play": f"Playing on {app_display}.",
        "pause": f"Paused {app_display}.",
        "next": f"Skipped to next track on {app_display}.",
        "previous": f"Went to previous track on {app_display}.",
        "toggle": f"Toggled play/pause on {app_display}.",
    }
    return labels[action]
