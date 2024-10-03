from telegram import (
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from pipelines.config_pipeline import handle_configuration_pipeline
from db.db import db
from pipelines.default_pipeline import handle_default_pipeline
from pipelines.qa_pipeline import (
    qa_image_handler,
    qa_text_handler,
    qa_voice_handler,
)
from pipelines.quiz_pipeline import handle_quiz_pipeline
from pipelines.subject_select_pipeline import handle_subject_select_pipeline
from resources.languages import en as lang
from utils.keyboard_markup import send_main_menu


async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command and reset the user's pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.message.from_user
    user_id = str(user.id)
    bot_response = lang.schola_intro.format(name=user.first_name)

    db.set_user_pipeline(user_id, "default")
    db.clear_user_subjects(user_id)

    # Present the main menu
    await send_main_menu(update, bot_response)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages from the user and route them based on the current pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.message.from_user
    user_id = str(user.id)
    user_message: str = update.message.text.strip()
    current_pipeline: str = db.get_user_pipeline(user_id)

    if not current_pipeline:
        current_pipeline = "default"
        db.set_user_pipeline(user_id, current_pipeline)

    if user_message == lang.back_to_main:
        db.set_user_pipeline(user_id, "default")
        await send_main_menu(update)
        return

    # Route the message to the appropriate pipeline handler
    if current_pipeline == "default":
        await handle_default_pipeline(update, context, user, user_message)
    elif current_pipeline == "select_subject":
        await handle_subject_select_pipeline(update, context, user, user_message)
    elif current_pipeline == "quiz":
        await handle_quiz_pipeline(update, context)
    elif current_pipeline == "configuration":
        await handle_configuration_pipeline(update, context, user, user_message)
    elif current_pipeline == "qa":
        await qa_text_handler(update, context)
    else:
        await update.message.reply_text("Unknown command. Please use the menu options.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo messages by routing them to the appropriate pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.message.from_user
    user_id = str(user.id)
    current_pipeline: str = db.get_user_pipeline(user_id)

    if current_pipeline == "qa":
        await qa_image_handler(update, context)
    else:
        await update.message.reply_text(lang.image_debug)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle voice messages by converting them to text and passing to qa_text_handler.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.message.from_user
    user_id = str(user.id)
    current_pipeline: str = db.get_user_pipeline(user_id)

    if current_pipeline == "qa":
        await qa_voice_handler(update, context)
    else:
        await update.message.reply_text(lang.voice_debug)
