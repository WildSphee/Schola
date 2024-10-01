from typing import Any, Literal

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from pipelines.db import db
from pipelines.qa import qa_image_handler, qa_start, qa_text_handler, qa_voice_handler
from pipelines.quiz import quiz_start
from pipelines.utils import send_main_menu, send_subject_menu


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    bot_response = f"Hello {user.first_name}! I am Schola, your learning assistant. 😊"

    db.set_user_pipeline(user_id, "default")
    db.clear_user_subjects(user_id)

    # Present the main menu
    await send_main_menu(update, bot_response)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if user_message.lower() == "back to main menu":
        db.set_user_pipeline(user_id, "default")
        await send_main_menu(update)
        return

    # Route the message to the appropriate pipeline handler
    if current_pipeline == "default":
        await handle_default_pipeline(update, context, user, user_message)
    elif current_pipeline == "select_subject":
        await handle_select_subject_pipeline(update, context, user, user_message)
    elif current_pipeline == "configuration":
        await handle_configuration_pipeline(update, context, user, user_message)
    elif current_pipeline == "qa":
        await qa_text_handler(update, context)
    else:
        await update.message.reply_text("Unknown command. Please use the menu options.")


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
    menu_selection: Literal["select subject", "quiz", "configuration", "q&a"] = (
        user_message.lower()
    )

    if menu_selection == "select subject":
        db.set_user_pipeline(user_id, "select_subject")
        await send_subject_menu(update)
    elif menu_selection == "quiz":
        # Start the quiz conversation
        return await quiz_start(update, context)
    elif menu_selection == "configuration":
        db.set_user_pipeline(user_id, "configuration")
        await handle_configuration_pipeline(update, context, user, user_message)
    elif menu_selection == "q&a":
        db.set_user_pipeline(user_id, "qa")
        await qa_start(update, context)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")


async def handle_select_subject_pipeline(
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
        "Done Selecting Subjects",
    ]
    if user_message in valid_subjects:
        if user_message == "Done Selecting Subjects":
            db.set_user_pipeline(user_id, "default")
            await update.message.reply_text(
                "Subjects saved.", reply_markup=ReplyKeyboardRemove()
            )
            await send_main_menu(update)
        else:
            db.add_user_subject(user_id, user_message)
            await update.message.reply_text(
                f"Added {user_message} to your subjects. You can select more or choose 'Done Selecting Subjects'."
            )
            await send_subject_menu(update)
    else:
        await update.message.reply_text(
            "Please select a subject from the list.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
            ),
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
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await update.message.reply_text("Please send images only in Q&A mode.")


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
        await update.message.reply_text("Please send voice messages only in Q&A mode.")
