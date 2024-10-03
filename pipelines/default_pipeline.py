from typing import Any

from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from db.db import db
from pipelines.config_pipeline import handle_configuration_pipeline
from pipelines.qa_pipeline import qa_start
from pipelines.quiz_pipeline import handle_quiz_pipeline
from resources.languages import en as lang
from utils.keyboard_markup import send_subject_menu


async def handle_default_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, menu_selection: str
) -> None:
    """
    Handle the default pipeline where the user selects a pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.
        user (Any): The user object from the message.
        menu_selection (str): The message text sent by the user.

    Returns:
        None
    """
    user_id = str(user.id)

    if menu_selection == lang.select_subject:
        db.set_user_pipeline(user_id, "select_subject")
        await send_subject_menu(update)
    elif menu_selection == lang.quiz:
        db.set_user_pipeline(user_id, "quiz")
        return await handle_quiz_pipeline(update, context)
    elif menu_selection == lang.configuration:
        db.set_user_pipeline(user_id, "configuration")
        await handle_configuration_pipeline(update, context, user, menu_selection)
    elif menu_selection == lang.qa:
        db.set_user_pipeline(user_id, "qa")
        await qa_start(update, context)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")
