from typing import Any

from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from pipelines.config_pipeline import handle_configuration_pipeline
from pipelines.qa_pipeline import qa_start
from pipelines.quiz_pipeline import handle_quiz_pipeline
from pipelines.subject_select_pipeline import handle_subject_select_pipeline
from resources.languages import en as lang


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

    if menu_selection == lang.select_subject:
        await handle_subject_select_pipeline(update, context, user)
    elif menu_selection == lang.quiz:
        return await handle_quiz_pipeline(update, context)
    elif menu_selection == lang.configuration:
        await handle_configuration_pipeline(update, context, user)
    elif menu_selection == lang.qa:
        await qa_start(update, context)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")
