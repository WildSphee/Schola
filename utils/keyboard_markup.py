from telegram import KeyboardButton, ReplyKeyboardMarkup, Update

from resources.languages import en as lang


async def send_main_menu(update: Update, response: str = "Please choose an option:"):
    """Send the main menu to the user."""
    keyboard = [
        [KeyboardButton(lang.select_subject)],
        [KeyboardButton(lang.quiz)],
        [KeyboardButton(lang.configuration)],
        [KeyboardButton(lang.qa)],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(response, reply_markup=reply_markup)
