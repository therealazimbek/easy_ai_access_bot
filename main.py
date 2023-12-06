import logging

from bot.telegram_bot import TelegramBot
from clients.vision_client import *

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    telegram_config = {'token': TELEGRAM_BOT_TOKEN}
    telegram_bot = TelegramBot(config=telegram_config)
    telegram_bot.run()


if __name__ == "__main__":
    main()
