from telegram import KeyboardButton, ReplyKeyboardMarkup, Update

from resources.languages import en as lang


async def send_main_menu(
    update: Update, response: str = "Please choose an option:"
) -> None:
    """
    Send the main menu to the user.
    this function must be awaited.

    Attribute:
        update (Update): the update object of the conversation
        response (str): the text to be sent along with the keyboard
    """
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
