import json
import random

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from llms.openai import call_openai
from llms.prompt import system_prompt
from pipelines.db import DB
from pipelines.utils import send_main_menu

db = DB()

# Conversation states for the quiz
QUIZ_START, QUIZ_QUESTION = range(2)


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

    prompt = system_prompt.format(subject=subject)
    bot_response = call_openai([], user, prompt)
    print(bot_response)
    # Parse the JSON response
    try:
        quiz_data = json.loads(bot_response)
        question = quiz_data["question"]
        options = quiz_data["options"]
        correct_option = quiz_data["correct_option"]
        explanation = quiz_data["explanation"]
    except (json.JSONDecodeError, KeyError) as e:
        print(e)
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


# Define the quiz conversation handler
quiz_conversation_handler = ConversationHandler(
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
)
