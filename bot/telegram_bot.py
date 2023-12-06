from telegram import *
from telegram.ext import *

from clients.openai_client import *
from clients.vision_client import *
from utils.delete_file import delete_file_if_exists
from utils.token_counter import validate_user_input
# from decorators.send_action_decorator import send_action
from telegram.constants import ChatAction
from pydub import AudioSegment
from functools import wraps


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return await func(update, context, *args, **kwargs)

        return command_func

    return decorator


class TelegramBot:
    def __init__(self, config: dict):
        self.config = config
        self.commands = [
            BotCommand(command='help', description="Show help message"),
            BotCommand(command='start', description="Show welcome message"),
            BotCommand(command='image', description="Generate image from prompt (e.g. /image cat)"),
            BotCommand(command='tts', description="Generate speech from text (e.g. /tts my house)")
        ]
        self.custom_keyboard = [['test']]
        self.reply_markup = ReplyKeyboardMarkup(self.custom_keyboard)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        bot_name = context.bot.name
        user = update.effective_user
        await update.message.reply_text(
            f"Hello {user.name}! I am your GPT-based Telegram bot. Send me a message, and I "
            f"will generate"
            f"a response for you. \nWith respect, {bot_name} team")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Type text for interaction with gpt bot (new features are coming soon)!")

    async def generate_gpt_response(self, update: Update, context: CallbackContext) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

        user_input = update.message.text.strip()

        if validate_user_input(user_input):
            generated_text = await generate_response(user_input)
            await update.message.reply_text(generated_text)
        else:
            await update.message.reply_text("Too many characters. Please try again with less characters.")

    async def image_command(self, update: Update, context: CallbackContext) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)

        user_input = update.message.text.replace("/image", "").strip()

        if validate_user_input(user_input):
            response = await generate_image(user_input)
            await update.message.reply_photo(response)
        else:
            await update.message.reply_text("Please provide valid input.")

    async def tts_command(self, update: Update, context: CallbackContext) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_VOICE)

        user_input = update.message.text.replace("/tts", "").strip()

        if validate_user_input(user_input):
            response = await generate_speech(user_input)
            await update.message.reply_voice(response)
            if response.exists():
                response.unlink()
        else:
            await update.message.reply_text("Please provide valid input.")

    async def image_to_text(self, update: Update, context: CallbackContext) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

        if update.message.photo:
            input_image_id = update.message.photo[-1].file_id
        elif update.message.document and update.message.document.mime_type.startswith('image'):
            input_image_id = update.message.document.file_id
        else:
            await update.message.reply_text("Please send a valid photo or image file.")
            return

        image_name = f"{input_image_id}.jpeg"
        input_image = await context.bot.get_file(input_image_id)
        await input_image.download_to_drive(image_name)

        with open(image_name, "rb") as image_file:
            content = image_file.read()

        response = await image_to_text_client(content)
        await update.message.reply_text(response)

        delete_file_if_exists(image_name)

    async def transcribe_command(self, update: Update, context: CallbackContext) -> None:
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

        filename = update.message.effective_attachment.file_unique_id
        filename_mp3 = f'{filename}.mp3'
        media_file = await context.bot.get_file(update.message.effective_attachment.file_id)
        await media_file.download_to_drive(filename)
        audio_track = AudioSegment.from_file(filename)
        audio_track.export(filename_mp3, format="mp3")

        audio_file = open(filename_mp3, "rb")
        generated_text = await transcribe_audio(audio_file)
        await update.message.reply_text(generated_text)
        audio_file.close()

        delete_file_if_exists(filename_mp3)
        delete_file_if_exists(filename)

    async def post_init(self, application: Application) -> None:
        """
        Post initialization hook for the bot.
        """
        # await application.bot.set_my_commands(self.group_commands, scope=BotCommandScopeAllGroupChats())
        await application.bot.set_my_commands(self.commands)

    def run(self):
        application = Application.builder().token(self.config['token']).post_init(self.post_init).build()

        # on different commands - answer in Telegram
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("image", self.image_command))
        application.add_handler(CommandHandler("tts", self.tts_command))
        application.add_handler(CommandHandler("stt", self.transcribe_command))

        # on non command i.e. message - pass text to gpt model for interaction
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_gpt_response))
        application.add_handler(
            MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.AUDIO, self.transcribe_command))
        application.add_handler(MessageHandler(filters.PHOTO | filters.ATTACHMENT, self.image_to_text))

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
