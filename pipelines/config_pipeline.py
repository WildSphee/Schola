from typing import Any

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from resources.languages import en as lang


async def handle_configuration_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any
) -> None:
    """
    Handle the configuration pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.
        user (Any): The user object from the message.

    Returns:
        None
    """

    await update.message.reply_text(
        "Configuration settings are not implemented yet.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
        ),
    )
