import logging
import os

from pathlib import Path
from dotenv import load_dotenv
from openai import *
from telegram import *
from telegram.ext import *
from telegram.constants import *
from pydub import AudioSegment
from google.cloud import vision_v1p3beta1 as vision
from send_action_decorator import send_action

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
vision_api_key = os.getenv("VISION_API_KEY")

# Set up Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up OpenAI API Client
client = OpenAI(api_key=openai_api_key)
vision_client = vision.ImageAnnotatorClient()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    # await update.message.reply_html(
    #     rf"Hi {user.mention_html()}!",
    #     reply_markup=ForceReply(selective=True),
    # )
    await update.message.reply_text(f"Hello {user.name}! I am your GPT-based Telegram bot. Send me a message, and I "
                                    f"will generate"
                                    "a response for you.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Type text for interaction with gpt bot (new features are coming soon)!")


@send_action(ChatAction.TYPING)
async def generate_gpt_response(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text

    response = client.chat.completions.create(
        model="gpt-4-1106-preview", messages=[{"role": "user", "content": user_input}]
    )

    generated_text = response.choices[0].message.content
    await update.message.reply_text(generated_text)


@send_action(ChatAction.UPLOAD_PHOTO)
async def image_command(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text

    response = client.images.generate(
        model="dall-e-3",
        prompt=user_input,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    await update.message.reply_photo(response.data[0].url)


@send_action(ChatAction.UPLOAD_VOICE)
async def tts_command(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.replace("/tts", "")

    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=user_input
    )
    response.stream_to_file(speech_file_path)

    await update.message.reply_voice(speech_file_path)


@send_action(ChatAction.TYPING)
async def image_to_text(update: Update, context: CallbackContext) -> None:
    input_image_id = update.message.photo[-1].file_id
    image_name = f"{input_image_id}.jpeg"
    input_image = await context.bot.get_file(input_image_id)
    await input_image.download_to_drive(image_name)

    with open(image_name, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = vision_client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    await update.message.reply_text(texts[0].description)

    if os.path.exists(image_name):
        os.remove(image_name)


@send_action(ChatAction.TYPING)
async def transcribe_command(update: Update, context: CallbackContext) -> None:
    user_input = update.message.voice
    filename = update.message.effective_attachment.file_unique_id
    filename_mp3 = f'{filename}.mp3'
    media_file = await context.bot.get_file(update.message.effective_attachment.file_id)
    await media_file.download_to_drive(filename)
    audio_track = AudioSegment.from_file(filename)
    audio_track.export(filename_mp3, format="mp3")

    audio_file = open(filename_mp3, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    generated_text = transcript.text
    await update.message.reply_text(generated_text)
    audio_file.close()

    if os.path.exists(filename_mp3):
        os.remove(filename_mp3)
    if os.path.exists(filename):
        os.remove(filename)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bots token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("image", image_command))
    application.add_handler(CommandHandler("tts", tts_command))
    application.add_handler(CommandHandler("stt", transcribe_command))

    # on non command i.e. message - pass text to gpt model for interaction
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_gpt_response))
    application.add_handler(MessageHandler(filters.VOICE, transcribe_command))
    application.add_handler(MessageHandler(filters.PHOTO, image_to_text))
    # application.add_handler(MessageHandler(filters.AUDIO, transcribe_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
