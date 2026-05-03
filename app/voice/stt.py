from openai import OpenAI

client = OpenAI()

def speech_to_text(audio_path: str):
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text