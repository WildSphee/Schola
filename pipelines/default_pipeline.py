from typing import Any, Literal

from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)
from pipelines.db import db
from pipelines.utils import send_main_menu, send_subject_menu
from pipelines.quiz_pipeline import handle_quiz_pipeline
from pipelines.qa_pipeline import qa_start
from pipelines.config_pipeline import handle_configuration_pipeline


async def handle_default_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, user_message: str
) -> None:
    """
    Handle the default pipeline where the user selects a pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.
        user (Any): The user object from the message.
        user_message (str): The message text sent by the user.

    Returns:
        None
    """
    user_id = str(user.id)
    menu_selection: Literal["📚 select subject", "📝 quiz", "⚙️ configuration", "❓ q&a"] = (
        user_message.lower()
    )

    if menu_selection == "📚 select subject":
        db.set_user_pipeline(user_id, "select_subject")
        await send_subject_menu(update)
    elif menu_selection == "📝 quiz":
        db.set_user_pipeline(user_id, "quiz")
        return await (update, context)
    elif menu_selection == "⚙️ configuration":
        db.set_user_pipeline(user_id, "configuration")
        await handle_configuration_pipeline(update, context, user, user_message)
    elif menu_selection == "❓ q&a":
        db.set_user_pipeline(user_id, "qa")
        await qa_start(update, context)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")
