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
