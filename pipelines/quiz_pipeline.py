import json
import random
import re

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
)

from llms.openai import call_openai
from pipelines.db import db
from resources.languages import en as lang
from resources.prompt import quiz_prompt
from utils.keyboard_markup import send_main_menu


async def generate_question(update: Update, context: CallbackContext):
    """Generate and present a quiz question to the user."""
    user = update.message.from_user
    user_id = str(user.id)
    subjects = db.get_user_subjects(user_id)
    if not subjects:
        await update.message.reply_text(
            lang.pls_select_subject,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
            ),
        )
        return ConversationHandler.END

    # Randomly select a subject
    subject = random.choice(subjects)

    prompt = quiz_prompt.format(subject=subject)
    bot_response = call_openai([], prompt)

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
                [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
            ),
        )
        return ConversationHandler.END

    # Save the correct answer and explanation in user_data
    context.user_data["correct_option"] = correct_option
    context.user_data["explanation"] = explanation

    # display question & options to the user
    options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
    message = lang.mc_format.format(
        subject=subject, question=question, options_text=options_text
    )
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(
            [["A", "B", "C", "D"], [KeyboardButton(lang.back_to_main)]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )


async def handle_quiz_pipeline(update: Update, context: CallbackContext):
    """Check the user's answer and provide feedback."""
    user_answer = update.message.text
    valid_options = ["A", "B", "C", "D"]

    # If the user have NOT generated a question - they will not have correct_option data
    if user_answer == lang.next_question or not context.user_data.get("correct_option"):
        await generate_question(update, context)
        return

    if user_answer == lang.back_to_main:
        # reset user data for quiz
        context.user_data["correct_option"] = None
        context.user_data["explanation"] = None
        db.set_user_pipeline(update.message.from_user.id, "default")
        await send_main_menu(update)
        return

    if user_answer not in valid_options:
        await update.message.reply_text(
            lang.pls_select_valid,
            reply_markup=ReplyKeyboardMarkup(
                [["A", "B", "C", "D"], [KeyboardButton(lang.back_to_main)]],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return

    # Retrieve the correct answer and explanation
    correct_option = context.user_data.get("correct_option")
    explanation = context.user_data.get("explanation")

    reply: str = (
        lang.correct_ans
        if user_answer == correct_option
        else lang.incorrect_ans.format(
            correct_option=correct_option, explanation=explanation
        )
    )
    await update.message.reply_text(
        reply,
        reply_markup=ReplyKeyboardMarkup(
            [
                [KeyboardButton(lang.next_question)],
                [KeyboardButton(lang.back_to_main)],
            ],
            resize_keyboard=True,
        ),
    )
