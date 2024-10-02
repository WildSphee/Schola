import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from pipelines.handlers import (
    handle_photo,
    handle_start_command,
    handle_text,
    handle_voice,
)
from pipelines.quiz_pipeline import quiz_conversation_handler

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")


def main():
    """Start the bot."""
    if TOKEN is None:
        print(
            "No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your environment variables."
        )
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Media handlers
    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start the Telegram chatbot
    application.run_polling()


if __name__ == "__main__":
    main()
