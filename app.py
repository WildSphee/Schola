# app.py

import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from pipelines.db import DB
from pipelines.handlers import echo, start_command
from pipelines.quiz import quiz_conversation_handler

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")


def main() -> None:
    """Start the bot."""
    if TOKEN is None:
        print(
            "No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your environment variables."
        )
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Initialize the database (ensure it's a singleton if necessary)
    db = DB()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(quiz_conversation_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()

    # Close the database connection when the bot stops
    db.close()


if __name__ == "__main__":
    main()
