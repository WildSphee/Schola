import json
import os
import random

from pydantic import BaseModel
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db import DB
from llms.openai import call_openai
from llms.prompt import system_prompt

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")

db = DB()

# Conversation states for the quiz
QUIZ_START, QUIZ_QUESTION = range(2)


class Message(BaseModel):
    role: str
    content: str


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and reset the user's pipeline."""
    user = update.message.from_user
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


async def send_subject_menu(update: Update, user):
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
    await update.message.reply_text(
        "Configuration settings are not implemented yet.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )


# Quiz conversation handler functions
async def quiz_start(update: Update, context: CallbackContext):
    """Start the quiz by checking if the user has selected subjects."""
    user = update.message.from_user
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
        return ConversationHandler.END

    # Store subjects in context for later use
    context.user_data["subjects"] = subjects

    # Move to the next state to get a question
    return await quiz_get_question(update, context)


async def quiz_get_question(update: Update, context: CallbackContext):
    """Generate and present a quiz question to the user."""
    user = update.message.from_user
    user_id = str(user.id)
    subjects = context.user_data.get("subjects")

    if not subjects:
        subjects = db.get_user_subjects(user_id)
        context.user_data["subjects"] = subjects

    # Randomly select a subject
    subject = random.choice(subjects)

    bot_response = call_openai([], user, system_prompt.format(subject=subject))

    # Parse the JSON response
    try:
        quiz_data = json.loads(bot_response)
        question = quiz_data["question"]
        options = quiz_data["options"]
        correct_option = quiz_data["correct_option"]
        explanation = quiz_data["explanation"]
    except (json.JSONDecodeError, KeyError):
        await update.message.reply_text(
            "Sorry, there was an error generating the quiz question. Please try again.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
            ),
        )
        return ConversationHandler.END

    # Save the correct answer and explanation in user_data
    context.user_data["correct_option"] = correct_option.upper()
    context.user_data["explanation"] = explanation

    # Present the question and options to the user
    options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
    message = f"Here's your question from {subject}:\n\n{question}\n\n{options_text}\n\nPlease select A, B, C, or D."
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(
            [["A", "B", "C", "D"], [KeyboardButton("Back to Main Menu")]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )

    return QUIZ_QUESTION


async def quiz_check_answer(update: Update, context: CallbackContext):
    """Check the user's answer and provide feedback."""
    user_answer = update.message.text.strip().upper()
    valid_options = ["A", "B", "C", "D"]

    if user_answer == "Next Question":
        return await quiz_get_question(update, context)

    if user_answer == "Back to Main Menu":
        await send_main_menu(update)
        return ConversationHandler.END

    if user_answer not in valid_options:
        await update.message.reply_text(
            "Please select a valid option: A, B, C, or D.",
            reply_markup=ReplyKeyboardMarkup(
                [["A", "B", "C", "D"], [KeyboardButton("Back to Main Menu")]],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return QUIZ_QUESTION

    correct_option = context.user_data.get("correct_option")
    explanation = context.user_data.get("explanation")

    if user_answer == correct_option:
        await update.message.reply_text(
            "Correct! 🎉",
            reply_markup=ReplyKeyboardMarkup(
                [
                    [KeyboardButton("Next Question")],
                    [KeyboardButton("Back to Main Menu")],
                ],
                resize_keyboard=True,
            ),
        )
    else:
        await update.message.reply_text(
            f"Incorrect. The correct answer is {correct_option}.\n\nExplanation: {explanation}",
            reply_markup=ReplyKeyboardMarkup(
                [
                    [KeyboardButton("Next Question")],
                    [KeyboardButton("Back to Main Menu")],
                ],
                resize_keyboard=True,
            ),
        )

    return QUIZ_START


async def stop_quiz(update: Update, context: CallbackContext):
    """End the quiz conversation."""
    await update.message.reply_text(
        "Quiz ended. Returning to main menu.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    if TOKEN is None:
        print("No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your .env file.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Define the quiz conversation handler
    quiz_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Quiz$"), quiz_start)],
        states={
            QUIZ_START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_get_question)
            ],
            QUIZ_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_check_answer)
            ],
        },
        fallbacks=[CommandHandler("stop", stop_quiz)],
        map_to_parent={
            ConversationHandler.END: QUIZ_START,
        },
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(quiz_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()
