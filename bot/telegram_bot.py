from telegram import BotCommand, Update, ReplyKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

from utils.delete_file import delete_file_if_exists
from utils.token_counter import validate_user_input
from pydub import AudioSegment
from clients.vision_client import VisionClient
from clients.openai_client import OpenAIClient
from repositories.user_repository import UserRepository


class TelegramBot:
    def __init__(
        self, openai_client: OpenAIClient, vision_client: VisionClient, config: dict
    ):
        self.openai_client = openai_client
        self.vision_client = vision_client
        self.repository = UserRepository()
        self.config = config
        self.commands = [
            BotCommand(command="help", description="Show help message"),
            BotCommand(command="start", description="Show welcome message"),
            BotCommand(
                command="image",
                description="Generate image from prompt (e.g. /image cat)",
            ),
            BotCommand(
                command="tts",
                description="Generate speech from text (e.g. /tts my house)",
            ),
            BotCommand(command="stats", description="Show user statistics"),
        ]
        self.custom_keyboard = [["test"]]
        self.reply_markup = ReplyKeyboardMarkup(self.custom_keyboard)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        bot_name = context.bot.name
        user = update.effective_user

        await self.add_user_to_db(user)

        await update.message.reply_text(
            f"Hello {user.name}! I am your GPT-based Telegram bot. Send me a message, and I "
            f"will generate "
            f"a response for you. \nWith respect, {bot_name} team!"
        )

    async def add_user_to_db(self, user):
        if not self.repository.user_exists(user.id):
            self.repository.insert_user(
                user.id, user.username, user.first_name, user.last_name
            )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.add_user_to_db(update.effective_user)
        message = """
        Welcome. This message will help you to use this bot
        \n- GPT-4 Turbo: send message to this bot without commands
        \n- Image generation: use /image command with desired input
        \n- Text-To-Speech: use /tts command along with a message
        \n- Image-To-Text: send images, documenst with image types without commands
        \n- Audio transcribing: send voice message, audio or documents with audio types without commands

        \nThanks for using this bot!\nEasyAIAccess Bot by @therealazimbek
        """
        await update.message.reply_text(message)

    async def generate_gpt_response(
        self, update: Update, context: CallbackContext
    ) -> None:
        await self.add_user_to_db(update.effective_user)

        user_input = update.message.text.strip()

        if validate_user_input(user_input):
            await update.message.reply_text(
                "Please wait, your request is processing, for large responses it can take a while!"
            )
            generated_text = await self.openai_client.generate_response(user_input)
            await update.message.reply_text(generated_text)
            self.repository.update_request_count(update.effective_user.id, "gpt")
        else:
            await update.message.reply_text(
                "Too many characters. Please try again with less characters."
            )

    async def stats_command(self, update: Update, context: CallbackContext) -> None:
        await self.add_user_to_db(update.effective_user)

        result = self.repository.get_service_counts(update.effective_user.id)
        result_string = "Your total request so far:\n"
        for service, count in result.items():
            service_name = "-".join(word.capitalize() for word in service.split("-"))
            result_string += f"{service_name}: {count}\n"

        await update.message.reply_text(result_string.strip())

    async def unrecognized_command(
        self, update: Update, context: CallbackContext
    ) -> None:
        await self.add_user_to_db(update.effective_user)
        await update.message.reply_text(
            "Sorry, I don't understand that command. See /help"
        )

    async def image_command(self, update: Update, context: CallbackContext) -> None:
        await self.add_user_to_db(update.effective_user)

        user_input = update.message.text.replace("/image", "").strip()

        if validate_user_input(user_input):
            await update.message.reply_text(
                "Please wait, your request is processing, for large responses and images it can take a while!"
            )
            response = await self.openai_client.generate_image(user_input)
            await update.message.reply_photo(response)
            self.repository.update_request_count(
                update.effective_user.id, "image-generation"
            )
        else:
            await update.message.reply_text(
                "Please provide valid input. Example: /image cute cat"
            )

    async def tts_command(self, update: Update, context: CallbackContext) -> None:
        await self.add_user_to_db(update.effective_user)

        user_input = update.message.text.replace("/tts", "").strip()

        if validate_user_input(user_input):
            await update.message.reply_text(
                "Please wait, your request is processing, for large responses it can take a while!"
            )
            response = await self.openai_client.generate_speech(user_input)
            await update.message.reply_voice(response)
            self.repository.update_request_count(
                update.effective_user.id, "text-to-speech"
            )
            if response.exists():
                response.unlink()
        else:
            await update.message.reply_text(
                "Please provide valid input. Example: /tts Hello from ai speech"
            )

    async def image_to_text(self, update: Update, context: CallbackContext) -> None:
        await self.add_user_to_db(update.effective_user)

        if update.message.photo:
            input_image_id = update.message.photo[-1].file_id
        elif update.message.document and update.message.document.mime_type.startswith(
            "image"
        ):
            input_image_id = update.message.document.file_id
        else:
            await update.message.reply_text("Please send a valid photo or image file.")
            return

        image_name = f"{input_image_id}.jpeg"
        input_image = await context.bot.get_file(input_image_id)
        await input_image.download_to_drive(image_name)

        with open(image_name, "rb") as image_file:
            content = image_file.read()

        await update.message.reply_text(
            "Please wait, your request is processing, for large responses it can take a while!"
        )
        response = await self.vision_client.image_to_text_client(content)
        await update.message.reply_text(response)
        self.repository.update_request_count(update.effective_user.id, "image-to-text")

        delete_file_if_exists(image_name)

    async def transcribe_command(
        self, update: Update, context: CallbackContext
    ) -> None:
        await self.add_user_to_db(update.effective_user)

        filename = update.message.effective_attachment.file_unique_id
        filename_mp3 = f"{filename}.mp3"
        media_file = await context.bot.get_file(
            update.message.effective_attachment.file_id
        )
        await media_file.download_to_drive(filename)
        audio_track = AudioSegment.from_file(filename)
        audio_track.export(filename_mp3, format="mp3")

        audio_file = open(filename_mp3, "rb")
        await update.message.reply_text(
            "Please wait, your request is processing, for large responses it can take a while!"
        )
        generated_text = await self.openai_client.transcribe_audio(audio_file)
        await update.message.reply_text("Transcirbed text: " + generated_text)
        self.repository.update_request_count(update.effective_user.id, "audio-to-text")
        audio_file.close()

        delete_file_if_exists(filename_mp3)
        delete_file_if_exists(filename)

    async def post_init(self, application: Application) -> None:
        # await application.bot.set_my_commands(self.group_commands, scope=BotCommandScopeAllGroupChats())
        await application.bot.set_my_commands(self.commands)

    def run(self):
        application = (
            Application.builder()
            .token(self.config["token"])
            .post_init(self.post_init)
            .build()
        )

        # on different commands - answer in Telegram
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("image", self.image_command))
        application.add_handler(CommandHandler("tts", self.tts_command))
        application.add_handler(CommandHandler("stt", self.transcribe_command))

        # on non command i.e. message - pass text to gpt model for interaction
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_gpt_response)
        )
        application.add_handler(
            MessageHandler(
                filters.AUDIO | filters.VOICE | filters.Document.AUDIO,
                self.transcribe_command,
            )
        )
        application.add_handler(
            MessageHandler(filters.PHOTO | filters.ATTACHMENT, self.image_to_text)
        )
        application.add_handler(
            MessageHandler(filters.COMMAND, self.unrecognized_command)
        )

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
