import requests
from app.config import ELEVENLABS_API_KEY

def text_to_speech(text: str):
    url = "https://api.elevenlabs.io/v1/text-to-speech/YOUR_VOICE_ID"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }

    response = requests.post(url, json={"text": text}, headers=headers)

    with open("output.mp3", "wb") as f:
        f.write(response.content)

    return "output.mp3"