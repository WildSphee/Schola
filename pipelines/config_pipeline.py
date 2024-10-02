from typing import Any

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)


async def handle_configuration_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, user_message: str
) -> None:
    """
    Handle the configuration pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.
        user (Any): The user object from the message.
        user_message (str): The message text sent by the user.

    Returns:
        None
    """
    await update.message.reply_text(
        "Configuration settings are not implemented yet.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🏠 Back to Main Menu")]], resize_keyboard=True
        ),
    )
