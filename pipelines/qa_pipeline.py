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
from pipelines.db import db
from resources.languages import en as lang
from resources.prompt import qa_prompt_img, qa_prompt_msg, qa_prompt_voice
from tools.form_recognizer import analyze_image
from tools.whisper import transcribe_voice
from utils.keyboard_markup import send_main_menu
from utils.md_parser import parse

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")


async def qa_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start the Q&A pipeline by sending a welcome message.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    """
    bot_response: str = lang.qa_intro
    await update.message.reply_text(
        bot_response,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
        ),
    )


async def qa_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages during the Q&A pipeline.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    """
    user = update.message.from_user
    user_id = str(user.id)
    user_message: str = update.message.text.strip()

    if user_message.lower() == lang.back_to_main:
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
        parse(bot_response),
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
        ),
    )


async def qa_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle images sent by the user during the Q&A pipeline; perform OCR and respond.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

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
        parse(bot_response),
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
        ),
    )


async def qa_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voices sent by the user during the Q&A pipeline; perform transcription and respond.

    Args:
        update (Update): Incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    """
    user: User = update.message.from_user
    user_id = str(user.id)

    voice = update.message.voice
    file = await voice.get_file()
    file_path = tempfile.mktemp(suffix=".ogg")

    await update.message.chat.send_action(action=ChatAction.TYPING)

    try:
        await file.download_to_drive(file_path)

        transcribed_text = transcribe_voice(file_path)
        subjects: List[str] = db.get_user_subjects(user_id)
        history: List[Dict[str, str]] = db.get_chat_history(user_id)

        bot_response: str = call_openai(
            history,
            qa_prompt_voice.format(subject=", ".join(subjects), query=transcribed_text),
        )

    except Exception as e:
        await update.message.reply_text(f"Error processing voice message: {e}")

    await update.message.reply_text(
        parse(bot_response),
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(lang.back_to_main)]], resize_keyboard=True
        ),
    )
