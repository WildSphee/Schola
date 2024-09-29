from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from pipelines.db import DB
from pipelines.quiz import quiz_start
from pipelines.utils import send_main_menu, send_subject_menu

db = DB()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and reset the user's pipeline."""
    user = update.message.from_user
    user_id = str(user.id)
    bot_response = f"Hello {user.first_name}! I am Schola, your learning assistant. 😊"

    db.set_user_pipeline(user_id, "default")
    db.clear_user_subjects(user_id)

    # Present the main menu
    await send_main_menu(update, bot_response)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from the user."""
    user = update.message.from_user
    user_id = str(user.id)
    user_message = update.message.text.strip()

    # Get the user's current pipeline
    current_pipeline = db.get_user_pipeline(user_id)

    # If no pipeline is set, default to 'default'
    if not current_pipeline:
        current_pipeline = "default"
        db.set_user_pipeline(user_id, current_pipeline)

    # Check for 'Back to Main Menu' command
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
    else:
        await update.message.reply_text("Unknown command. Please use the menu options.")


async def handle_default_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, user_message: str
):
    """Handle the default pipeline where the user selects a pipeline."""
    user_id = str(user.id)
    if user_message.lower() == "select subject":
        db.set_user_pipeline(user_id, "select_subject")
        await send_subject_menu(update, user)
    elif user_message.lower() == "quiz":
        # Start the quiz conversation
        return await quiz_start(update, context)
    elif user_message.lower() == "configuration":
        db.set_user_pipeline(user_id, "configuration")
        await handle_configuration_pipeline(update, context, user, user_message)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")


async def handle_select_subject_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, user_message: str
):
    """Handle the subject selection pipeline."""
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
            await send_subject_menu(update, user)
    else:
        await update.message.reply_text(
            "Please select a subject from the list.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
            ),
        )


async def handle_configuration_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user, user_message: str
):
    """Handle the configuration pipeline."""
    await update.message.reply_text(
        "Configuration settings are not implemented yet.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )
