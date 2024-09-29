from telegram import KeyboardButton, ReplyKeyboardMarkup, Update


async def send_main_menu(update: Update, response: str = "Please choose an option:"):
    """Send the main menu to the user."""
    keyboard = [
        [KeyboardButton("Select Subject")],
        [KeyboardButton("Quiz")],
        [KeyboardButton("Configuration")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(response, reply_markup=reply_markup)


async def send_subject_menu(update: Update, user):
    """Send the subject selection menu."""
    subjects = ["Math", "Science", "History", "English", "Done Selecting Subjects"]
    keyboard = [[KeyboardButton(subject)] for subject in subjects]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Please select a subject (you can select multiple):", reply_markup=reply_markup
    )
