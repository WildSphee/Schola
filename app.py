import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from pipelines.handlers import echo, handle_photo, handle_voice, start_command
from pipelines.quiz import quiz_conversation_handler

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")


def main():
    """Start the bot."""
    if TOKEN is None:
        print(
            "No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your environment variables."
        )
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))

    # Add message handlers
    application.add_handler(quiz_conversation_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    application.run_polling()


if __name__ == "__main__":
    main()
