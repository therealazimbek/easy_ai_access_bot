import os
import logging

from bot.telegram_bot import TelegramBot
from clients.vision_client import VisionClient
from clients.openai_client import OpenAIClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
vision_api_key = os.getenv("VISION_API_KEY")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    openai_client = OpenAIClient(openai_api_key)
    vision_client = VisionClient()
    telegram_config = {'token': TELEGRAM_BOT_TOKEN}
    telegram_bot = TelegramBot(openai_client, vision_client, config=telegram_config)
    telegram_bot.run()


if __name__ == "__main__":
    main()
