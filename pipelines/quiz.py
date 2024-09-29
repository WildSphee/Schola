import json
import random
import re

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
from pipelines.db import db
from pipelines.utils import send_main_menu

# Conversation state for the quiz
QUIZ_QUESTION = 0


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

    await quiz_get_question(update, context)

    return QUIZ_QUESTION


async def quiz_get_question(update: Update, context: CallbackContext):
    """Generate and present a quiz question to the user."""
    user = update.message.from_user
    subjects = context.user_data.get("subjects")

    # Randomly select a subject
    subject = random.choice(subjects)

    prompt = system_prompt.format(subject=subject)
    bot_response = call_openai([], user, prompt)

    # Remove any code fences from the response
    bot_response = bot_response.strip()
    code_fence_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.match(code_fence_pattern, bot_response)
    if match:
        bot_response = match.group(1).strip()
    else:
        bot_response = bot_response.strip("`")

    # Parse the JSON response
    try:
        quiz_data = json.loads(bot_response)
        question = quiz_data["question"]
        options = quiz_data["options"]
        correct_option = quiz_data["correct_option"].upper()
        explanation = quiz_data["explanation"]
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(e)
        await update.message.reply_text(
            "Sorry, there was an error generating the quiz question. Please try again.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
            ),
        )
        return ConversationHandler.END

    # Save the correct answer and explanation in user_data
    context.user_data["correct_option"] = correct_option
    context.user_data["explanation"] = explanation

    # display question & options to the user
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


async def quiz_check_answer(update: Update, context: CallbackContext):
    """Check the user's answer and provide feedback."""
    user_answer = update.message.text.strip().upper()
    valid_options = ["A", "B", "C", "D"]

    if user_answer == "NEXT QUESTION":
        # Generate and send the next question
        await quiz_get_question(update, context)
        return QUIZ_QUESTION

    if user_answer == "BACK TO MAIN MENU":
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

    # Retrieve the correct answer and explanation
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

    return QUIZ_QUESTION


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
        QUIZ_QUESTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_check_answer)
        ],
    },
    fallbacks=[CommandHandler("stop", stop_quiz)],
)
