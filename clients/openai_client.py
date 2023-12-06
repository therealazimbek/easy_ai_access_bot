import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import *

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


async def generate_response(user_input: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4-1106-preview", messages=[{"role": "user", "content": user_input}]
    )

    generated_text = response.choices[0].message.content
    return generated_text


async def generate_image(user_input: str) -> str:
    response = client.images.generate(
        model="dall-e-3",
        prompt=user_input,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url


async def generate_speech(user_input) -> Path:
    speech_file_path = Path(__file__).parent / f"speech-{datetime.time}.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=user_input
    )
    response.stream_to_file(speech_file_path)

    return speech_file_path


async def transcribe_audio(audio_file) -> str:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    generated_text = transcript.text
    return generated_text
