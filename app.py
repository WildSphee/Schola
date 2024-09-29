import os

from pydantic import BaseModel
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db import DB
from llms.openai import call_openai

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")

db = DB()


class Message(BaseModel):
    role: str
    content: str


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and reset the user's pipeline."""
    user: User = update.message.from_user
    user_id = str(user.id)
    bot_response = f"Hello {user.first_name}! I am Schola, your learning assistant. 😊"

    db.set_user_pipeline(user_id, "default")
    db.clear_user_subjects(user_id)

    # Present the main menu
    await send_main_menu(update, bot_response)


async def send_main_menu(update: Update, response: str = "Please choose an option:"):
    """Send the main menu to the user."""
    keyboard = [
        [KeyboardButton("Select Subject")],
        [KeyboardButton("Quiz")],
        [KeyboardButton("Configuration")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(response, reply_markup=reply_markup)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from the user."""
    user: User = update.message.from_user
    user_id = str(user.id)
    user_message: str = update.message.text.strip()

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
    elif current_pipeline == "quiz":
        await handle_quiz_pipeline(update, context, user, user_message)
    elif current_pipeline == "configuration":
        await handle_configuration_pipeline(update, context, user, user_message)
    else:
        await update.message.reply_text("Unknown pipeline. Please /start to begin.")


async def handle_default_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    """Handle the default pipeline where the user selects a pipeline."""
    user_id = str(user.id)
    if user_message.lower() == "select subject":
        db.set_user_pipeline(user_id, "select_subject")
        await send_subject_menu(update, user)
    elif user_message.lower() == "quiz":
        db.set_user_pipeline(user_id, "quiz")
        await handle_quiz_pipeline(update, context, user, user_message)
    elif user_message.lower() == "configuration":
        db.set_user_pipeline(user_id, "configuration")
        await handle_configuration_pipeline(update, context, user, user_message)
    else:
        await update.message.reply_text("Please choose a valid option from the menu.")


async def send_subject_menu(update: Update, user: User):
    """Send the subject selection menu."""
    subjects = ["Math", "Science", "History", "English", "Done Selecting Subjects"]
    keyboard = [[KeyboardButton(subject)] for subject in subjects]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Please select a subject (you can select multiple):", reply_markup=reply_markup
    )


async def handle_select_subject_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
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


async def handle_quiz_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    """Handle interactions in the Quiz pipeline."""
    user_id = str(user.id)
    # Get user's selected subjects
    subjects = db.get_user_subjects(user_id)
    if not subjects:
        await update.message.reply_text(
            "You haven't selected any subjects yet. Please select subjects first.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
            ),
        )
        return

    # Generate a quiz question from selected subjects using LLM
    import random

    subject = random.choice(subjects)
    system_prompt = f"You are a teacher creating a simple quiz question for {subject} suitable for a child. Provide one question."

    # Prepare history
    history = []
    api_history = [{"role": msg.role, "content": msg.content} for msg in history]

    # Generate a quiz question
    bot_response = call_openai(api_history, user, "", system_prompt)

    db.log_interaction(user, user_message, bot_response)

    # Present the question to the user
    await update.message.reply_text(
        f"Here's a question from {subject}:\n\n{bot_response}",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )

    # Optionally, you can wait for the user's answer and check correctness


async def handle_configuration_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    await update.message.reply_text(
        "Configuration settings are not implemented yet.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )


def main() -> None:
    """Start the bot."""
    if TOKEN is None:
        print("No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your .env file.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # You can implement the image handler if needed
    # application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()
