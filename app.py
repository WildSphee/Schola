import os
import tempfile
from typing import List, Dict

from dotenv import load_dotenv
from pydantic import BaseModel
from telegram import (
    Update,
    User,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ChatAction,
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
from llms.prompt import EXAM_BOT_PROMPT
from tools.form_recognizer import analyze_image

load_dotenv()

TOKEN = os.getenv("TELEGRAM_EXAM_BOT_TOKEN")

db = DB('interactions.csv')


class Message(BaseModel):
    role: str
    content: str


async def start_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued and log user info. Also clears context."""
    bot_response: str = "I am SCHOLA!"

    # Define the keyboard options
    keyboard = [
        [KeyboardButton('1'), KeyboardButton('2')],
        [KeyboardButton('3'), KeyboardButton('4')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)

    await update.message.reply_text(bot_response, reply_markup=reply_markup)


async def echo(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from the user."""
    user: User = update.message.from_user
    user_message: str = update.message.text

    # Retrieve chat history
    history_records = db._get_chat_history(str(user.id))
    # Get the last 4 messages (2 user-assistant exchanges)
    history_records = history_records[-4:]

    # Convert history_records to list of Message objects
    history = [Message(**msg_dict) for msg_dict in history_records]

    # Append the current user message to history
    history.append(Message(role='user', content=user_message))

    # Prepare history for OpenAI API
    api_history = [{'role': msg.role, 'content': msg.content} for msg in history]

    bot_response: str = call_openai(
        api_history,
        user,
        user_message,
        EXAM_BOT_PROMPT
    )

    # Log the interaction
    db._log_interaction(user, user_message, bot_response)

    await update.message.reply_text(bot_response)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle images sent by the user, perform OCR and respond."""
    user: User = update.message.from_user
    photo = update.message.photo[-1]  # Get the highest resolution photo

    file = await photo.get_file()
    file_path = tempfile.mktemp()

    await update.message.reply_chat_action(ChatAction.TYPING)

    try:
        await file.download_to_drive(file_path)
        extracted_text = analyze_image(file_path)

        # Retrieve chat history
        history_records = db._get_chat_history(str(user.id))
        # Get the last 4 messages (2 user-assistant exchanges)
        history_records = history_records[-4:]

        # Convert history_records to list of Message objects
        history = [Message(**msg_dict) for msg_dict in history_records]

        # Append the extracted text as current user message to history
        history.append(Message(role='user', content=extracted_text))

        # Prepare history for OpenAI API
        api_history = [{'role': msg.role, 'content': msg.content} for msg in history]

        bot_response = call_openai(
            api_history,
            user,
            extracted_text,
            EXAM_BOT_PROMPT
        )

        # Log the interaction
        db._log_interaction(user, extracted_text, bot_response)

    except Exception as e:
        bot_response = f"Error processing image: {e}"

    await update.message.reply_text(bot_response)


def main() -> None:
    """Start the bot."""
    if TOKEN is None:
        print("No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your .env file.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    application.run_polling()


if __name__ == "__main__":
    main()