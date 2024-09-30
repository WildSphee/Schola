import os
import tempfile
from typing import Dict, List

from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    User,
)
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from llms.openai import call_openai
from llms.prompt import qa_prompt_img, qa_prompt_msg
from pipelines.db import db
from pipelines.utils import send_main_menu
from tools.form_recognizer import analyze_image

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")


async def qa_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start the Q&A pipeline by sending a welcome message.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    bot_response: str = "You are now in the Q&A mode. You can ask questions or send images for analysis."
    await update.message.reply_text(
        bot_response,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )


async def qa_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages during the Q&A pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.message.from_user
    user_id = str(user.id)
    user_message: str = update.message.text.strip()

    if user_message.lower() == "back to main menu":
        db.set_user_pipeline(user_id, "default")
        await send_main_menu(update)
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        history: List[Dict[str, str]] = db.get_chat_history(user_id)
        subjects: List[str] = db.get_user_subjects(user_id)

        bot_response: str = call_openai(
            history,
            qa_prompt_msg.format(subject=", ".join(subjects), query=user_message),
        )
    except Exception as e:
        bot_response = f"Error processing your request: {e}"

    await update.message.reply_text(
        bot_response,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )


async def qa_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle images sent by the user during the Q&A pipeline; perform OCR and respond.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user: User = update.message.from_user
    user_id = str(user.id)
    photo = update.message.photo[-1]  # Get the highest resolution photo

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        # processing the file
        file = await photo.get_file()
        file_path = tempfile.mktemp()
        await file.download_to_drive(file_path)

        extracted_text: str = analyze_image(file_path)
        subjects: List[str] = db.get_user_subjects(user_id)
        history: List[Dict[str, str]] = db.get_chat_history(user_id)

        bot_response: str = call_openai(
            history,
            qa_prompt_img.format(subject=", ".join(subjects), query=extracted_text),
        )

    except Exception as e:
        bot_response = f"Error processing image: {e}"

    await update.message.reply_text(
        bot_response,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Back to Main Menu")]], resize_keyboard=True
        ),
    )
