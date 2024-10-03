from typing import Any

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from db.db import db
from resources.languages import en as lang
from utils.keyboard_markup import send_main_menu, send_subject_menu


async def handle_subject_select_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, user_message: str
) -> None:
    """
    Handle the subject selection pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.
        user (Any): The user object from the message.
        user_message (str): The message text sent by the user.

    Returns:
        None
    """
    user_id = str(user.id)
    valid_subjects = [
        "Math",
        "Science",
        "History",
        "English",
        lang.done_selecting,
    ]
    if user_message in valid_subjects:
        if user_message == lang.done_selecting:
            db.set_user_pipeline(user_id, "default")
            await update.message.reply_text(
                "Subjects saved.", reply_markup=ReplyKeyboardRemove()
            )
            await send_main_menu(update)
        else:
            db.add_user_subject(user_id, user_message)
            await update.message.reply_text(
                f"Added {user_message} to your subjects. You can select more or choose '{lang.done_selecting}'."
            )
            await send_subject_menu(update)
    else:
        await update.message.reply_text(
            "Please select a subject from the list.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
            ),
        )
