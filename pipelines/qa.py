import os
import tempfile
from typing import Dict, List

from telegram import Update, User
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from llms.openai import call_openai
from llms.prompt import qa_prompt
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
    await update.message.reply_text(bot_response)


async def qa_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages during the Q&A pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user_message: str = update.message.text.strip()

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        history: List[
            Dict[str, str]
        ] = []  # Replace with actual retrieval from the database
        bot_response: str = call_openai(history, user_message, qa_prompt)
    except Exception as e:
        bot_response = f"Error processing your request: {e}"

    await update.message.reply_text(bot_response)


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
    photo = update.message.photo[-1]  # Get the highest resolution photo

    file = await photo.get_file()
    file_path = tempfile.mktemp()

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        await file.download_to_drive(file_path)
        extracted_text: str = analyze_image(file_path)
        history: List[
            Dict[str, str]
        ] = []  # Replace with actual retrieval from the database
        bot_response: str = call_openai(history, user, extracted_text, qa_prompt)
    except Exception as e:
        bot_response = f"Error processing image: {e}"

    await update.message.reply_text(bot_response)
