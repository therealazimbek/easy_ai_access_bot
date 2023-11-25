import logging
import os

from pathlib import Path
from dotenv import load_dotenv
from openai import *
from telegram import *
from telegram.ext import *

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Set up Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up OpenAI API Client
client = OpenAI(api_key=openai_api_key)

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


async def generate_gpt_response(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text

    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": user_input}]
    )

    generated_text = response.choices[0].message.content
    await update.message.reply_text(generated_text)


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


async def tts_command(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text

    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Today is a wonderful day to build something people love!"
    )
    response.stream_to_file(speech_file_path)

    await update.message.reply_voice(speech_file_path)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bots token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("image", image_command))

    # on non command i.e. message - pass text to gpt model for interaction
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_gpt_response))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
