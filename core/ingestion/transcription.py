import os
from core.config import client
from core.utils import Colors

def transcribe_audio(file_path: str) -> str:

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{Colors.TRANSCRIBE} File not found: {file_path}")

    print(f"{Colors.TRANSCRIBE} Sending file to Groq Whisper: {file_path}")

    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file),
            model="whisper-large-v3-turbo",  # or "whisper-large-v3-turbo" if supported
        )

    print(f"{Colors.TRANSCRIBE} Transcription complete.")
    return transcription.text
