import os

from pydantic import BaseModel
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
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
    bot_response = "Welcome to the bot! Please choose a pipeline: 1 or 2"

    db.set_user_pipeline(user_id, "default")

    keyboard = [
        [KeyboardButton("1"), KeyboardButton("2")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(bot_response, reply_markup=reply_markup)


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

    # Route the message to the appropriate pipeline handler
    if current_pipeline == "default":
        await handle_default_pipeline(update, context, user, user_message)
    elif current_pipeline == "pipeline1":
        await handle_pipeline1(update, context, user, user_message)
    elif current_pipeline == "pipeline2":
        await handle_pipeline2(update, context, user, user_message)
    else:
        await update.message.reply_text("Unknown pipeline. Please /start to begin.")


async def handle_default_pipeline(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    """Handle the default pipeline where the user selects a pipeline."""
    user_id = str(user.id)
    if user_message == "1":
        db.set_user_pipeline(user_id, "pipeline1")
        await update.message.reply_text("You've selected Pipeline 1. Let's begin!")
    elif user_message == "2":
        db.set_user_pipeline(user_id, "pipeline2")
        await update.message.reply_text("You've selected Pipeline 2. Let's begin!")
    else:
        await update.message.reply_text("Please choose a valid option: 1 or 2.")


async def handle_pipeline1(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    """Handle interactions in Pipeline 1."""
    user_id = str(user.id)

    # Retrieve chat history for context (optional)
    history_records = db.get_chat_history(user_id)
    # Get recent messages if needed
    history_records = history_records[-4:]

    # Prepare history
    history = [Message(**msg_dict) for msg_dict in history_records]
    history.append(Message(role="user", content=user_message))

    api_history = [{"role": msg.role, "content": msg.content} for msg in history]

    # Call your specific LLM prompt for Pipeline 1
    bot_response = call_openai(api_history, user, user_message, "Pipeline 1 Prompt")

    db.log_interaction(user, user_message, bot_response)

    await update.message.reply_text(bot_response)



async def handle_pipeline2(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, user_message: str
):
    """Handle interactions in Pipeline 2."""
    user_id = str(user.id)

    # Similar to Pipeline 1 but with different prompt or processing
    history_records = db.get_chat_history(user_id)
    history_records = history_records[-4:]

    history = [Message(**msg_dict) for msg_dict in history_records]
    history.append(Message(role="user", content=user_message))

    api_history = [{"role": msg.role, "content": msg.content} for msg in history]

    bot_response = call_openai(api_history, user, user_message, "Pipeline 2 Prompt")

    db.log_interaction(user, user_message, bot_response)

    await update.message.reply_text(bot_response)



async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle images sent by the user."""
    # You may decide which pipeline to use or handle images separately
    pass  # Implement as needed


def main() -> None:
    """Start the bot."""
    if TOKEN is None:
        print("No token found. Please set TELEGRAM_EXAM_BOT_TOKEN in your .env file.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    application.run_polling()


main()
