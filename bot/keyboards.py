from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Новая задача")
        ],
        [
            KeyboardButton(text="📋 Мои задачи"),
            KeyboardButton(text="✅ Выполненные")
        ],
        [
            KeyboardButton(text="❓ Помощь")
        ]
    ],
    resize_keyboard=True
)