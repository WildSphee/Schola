from typing import Any, List, Optional

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from db.db import db
from resources.languages import en as lang
from tools.messenger import schola_reply
from utils.keyboard_markup import send_main_menu


async def handle_subject_select_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, user_message: str
) -> None:
    db.set_user_pipeline(user.id, "subject_select")

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

    subject_info_list: List[str] = db.get_user_subjects(user_id)
    current_subject: str = db.get_current_subject(user_id) or "'No current subject'"

    # displaying message regarding course info
    subject_info: str = ""
    for i, s in enumerate(subject_info_list, start=1):
        s_info: Optional[str] = db.get_subject_info_by_subject_name(s)
        subject_info += f"\n<b>{i}.{s}</b>\n"
        subject_info += f"{dict(s_info).get('subject_description')}" if s_info else ""
        subject_info += "\n"

    if user_message == lang.select_subject:
        await schola_reply(
            update=update,
            message=lang.selecting_text.format(
                subject=current_subject, subjects=subject_info
            ),
            reply_markup=ReplyKeyboardMarkup(
                [
                    *[[KeyboardButton(k)] for k in subject_info_list],
                    [KeyboardButton(lang.back_to_main)],
                ]
            ),
        )
    elif user_message == lang.done_selecting:
        await update.message.reply_text("Subjects saved.")
        await send_main_menu(update)
    elif user_message in subject_info_list:
        db.set_current_subject(user_id=user_id, subject=user_message)
        await update.message.reply_text(
            f"Your current subject is now: {user_message}. You can now choose: '{lang.done_selecting}'.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
            ),
        )
    else:
        await update.message.reply_text(
            "Please select a subject from the list.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
            ),
        )
