from datetime import datetime

import telebot
from telebot import types

from config.config import BOT_TOKEN
from database.db import (
    create_database,
    add_task,
    get_user_tasks,
    get_completed_tasks,
    mark_task_done,
    delete_task,
    clear_completed_tasks,
    update_task,
)
from services.calendar_service import create_calendar_event
from services.date_parser import parse_user_datetime, parse_task_message


bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}


def main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(types.InlineKeyboardButton("➕ Новая задача", callback_data="menu:new"))

    keyboard.add(
        types.InlineKeyboardButton("📋 Мои задачи", callback_data="menu:list"),
        types.InlineKeyboardButton("✅ Выполненные", callback_data="menu:completed"),
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🧹 Очистить выполненные",
            callback_data="menu:clear_completed"
        )
    )

    keyboard.add(types.InlineKeyboardButton("❓ Помощь", callback_data="menu:help"))

    return keyboard


def back_to_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🏠 На главную", callback_data="menu:main"))
    return keyboard


def task_keyboard(task_id):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton("✅ Выполнить", callback_data=f"done:{task_id}"),
        types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{task_id}"),
    )

    keyboard.add(
        types.InlineKeyboardButton("✏️ Изменить", callback_data=f"edit:{task_id}"),
        types.InlineKeyboardButton("🏠 На главную", callback_data="menu:main"),
    )

    return keyboard


def format_date_for_user(date_text):
    try:
        return datetime.fromisoformat(date_text).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return date_text


def show_main_menu(chat_id):
    bot.send_message(
        chat_id,
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )


def show_tasks(chat_id, user_id):
    tasks = get_user_tasks(user_id)

    if not tasks:
        bot.send_message(
            chat_id,
            "У тебя пока нет активных задач.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    bot.send_message(chat_id, "Твои активные задачи:")

    for task in tasks:
        task_id, task_text, due_date, status = task
        formatted_date = format_date_for_user(due_date)

        bot.send_message(
            chat_id,
            f"📝 {task_text}\n"
            f"⏰ {formatted_date}",
            reply_markup=task_keyboard(task_id)
        )


def show_completed_tasks(chat_id, user_id):
    tasks = get_completed_tasks(user_id)

    if not tasks:
        bot.send_message(
            chat_id,
            "У тебя пока нет выполненных задач.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    text = "Выполненные задачи:\n\n"

    for task in tasks:
        task_id, task_text, due_date, status = task
        formatted_date = format_date_for_user(due_date)
        text += f"✅ {task_text} — {formatted_date}\n"

    bot.send_message(
        chat_id,
        text,
        reply_markup=back_to_menu_keyboard()
    )


@bot.message_handler(commands=["start"])
def start_command(message):
    user_states.pop(message.from_user.id, None)

    bot.send_message(
        message.chat.id,
        "Привет! Я бот для управления задачами.\n\n"
        "Я помогу создать задачу, сохранить её и напомнить о ней в нужное время.\n\n"
        "Выбери действие:",
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "Как пользоваться ботом:\n\n"
        "➕ Новая задача — добавить задачу\n"
        "📋 Мои задачи — посмотреть активные задачи\n"
        "✅ Выполненные — посмотреть завершённые задачи\n"
        "🧹 Очистить выполненные — удалить завершённые задачи\n\n"
        "Задачу можно отправить одним сообщением.\n\n"
        "Примеры:\n"
        "Купить лекарства завтра в 18:00\n"
        "Позвонить преподавателю 15 июня в 14:30\n"
        "Встреча 01.07.2026 в 13:00 - 17:00\n\n"
        "При редактировании дата может быть указана так:\n"
        "завтра, 12:00\n"
        "15 июня, 18:30\n"
        "01.07.2026, 13:00 - 17:00",
        reply_markup=back_to_menu_keyboard()
    )


@bot.message_handler(commands=["list"])
def list_command(message):
    show_tasks(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["completed"])
def completed_command(message):
    show_completed_tasks(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["clear_completed"])
def clear_completed_command(message):
    user_id = message.from_user.id
    deleted_count = clear_completed_tasks(user_id)

    if deleted_count == 0:
        bot.send_message(
            message.chat.id,
            "Выполненных задач для удаления нет.",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Удалено выполненных задач: {deleted_count} 🗑️",
            reply_markup=back_to_menu_keyboard()
        )


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:main")
def menu_main(callback):
    user_states.pop(callback.from_user.id, None)
    show_main_menu(callback.message.chat.id)
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:new")
def menu_new_task(callback):
    user_states[callback.from_user.id] = {"state": "waiting_for_task_input"}

    bot.send_message(
        callback.message.chat.id,
        "Отправь задачу одним сообщением.\n\n"
        "Например:\n"
        "Купить лекарства завтра в 18:00\n"
        "Позвонить преподавателю 15 июня в 14:30\n"
        "Встреча 01.07.2026 в 13:00 - 17:00"
    )

    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:list")
def menu_list(callback):
    show_tasks(callback.message.chat.id, callback.from_user.id)
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:completed")
def menu_completed(callback):
    show_completed_tasks(callback.message.chat.id, callback.from_user.id)
    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:clear_completed")
def menu_clear_completed(callback):
    user_id = callback.from_user.id
    deleted_count = clear_completed_tasks(user_id)

    if deleted_count == 0:
        bot.send_message(
            callback.message.chat.id,
            "Выполненных задач для удаления нет.",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        bot.send_message(
            callback.message.chat.id,
            f"Удалено выполненных задач: {deleted_count} 🗑️",
            reply_markup=back_to_menu_keyboard()
        )

    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data == "menu:help")
def menu_help(callback):
    bot.send_message(
        callback.message.chat.id,
        "Как пользоваться ботом:\n\n"
        "➕ Новая задача — добавить задачу\n"
        "📋 Мои задачи — посмотреть активные задачи\n"
        "✅ Выполненные — посмотреть завершённые задачи\n"
        "🧹 Очистить выполненные — удалить завершённые задачи\n\n"
        "Задачу можно отправить одним сообщением.\n\n"
        "Примеры:\n"
        "Купить лекарства завтра в 18:00\n"
        "Позвонить преподавателю 15 июня в 14:30\n"
        "Встреча 01.07.2026 в 13:00 - 17:00\n\n"
        "При редактировании дата может быть указана так:\n"
        "завтра, 12:00\n"
        "15 июня, 18:30\n"
        "01.07.2026, 13:00 - 17:00",
        reply_markup=back_to_menu_keyboard()
    )

    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("done:"))
def done_callback(callback):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = mark_task_done(user_id, task_id)

    if success:
        bot.edit_message_text(
            "Задача отмечена как выполненная ✅",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=back_to_menu_keyboard()
        )
    else:
        bot.answer_callback_query(callback.id, "Задача не найдена", show_alert=True)
        return

    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("delete:"))
def delete_callback(callback):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = delete_task(user_id, task_id)

    if success:
        bot.edit_message_text(
            "Задача удалена 🗑️",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=back_to_menu_keyboard()
        )
    else:
        bot.answer_callback_query(callback.id, "Задача не найдена", show_alert=True)
        return

    bot.answer_callback_query(callback.id)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("edit:"))
def edit_callback(callback):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    user_states[user_id] = {
        "state": "waiting_for_edit_text",
        "edit_task_id": task_id,
    }

    bot.send_message(
        callback.message.chat.id,
        "Отправь новый текст задачи."
    )

    bot.answer_callback_query(callback.id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text.startswith("/"):
        user_states.pop(user_id, None)
        bot.send_message(
            chat_id,
            "Действие отменено.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    state_data = user_states.get(user_id)

    if not state_data:
        bot.send_message(
            chat_id,
            "Я не понял сообщение.\n\n"
            "Чтобы добавить задачу, нажми /start и выбери «➕ Новая задача».",
            reply_markup=back_to_menu_keyboard()
        )
        return

    state = state_data["state"]

    if state == "waiting_for_task_input":
        task_text, start_time, end_time = parse_task_message(message.text)

        if task_text is None:
            bot.send_message(
                chat_id,
                "Не удалось распознать задачу, дату или время.\n\n"
                "Попробуй написать так:\n"
                "Купить лекарства завтра в 18:00\n"
                "Позвонить преподавателю 15 июня в 14:30\n"
                "Встреча 01.07.2026 в 13:00 - 17:00"
            )
            return

        add_task(user_id, task_text, start_time)

        create_calendar_event(
            title=task_text,
            start_time=start_time,
            end_time=end_time,
            description=f"Задача пользователя Telegram ID: {user_id}"
        )

        formatted_date = format_date_for_user(start_time)

        bot.send_message(
            chat_id,
            "Задача добавлена ✅\n\n"
            f"Задача: «{task_text}»\n"
            f"Дата и время: {formatted_date}",
            reply_markup=back_to_menu_keyboard()
        )

        user_states.pop(user_id, None)
        return

    if state == "waiting_for_edit_text":
        user_states[user_id] = {
            "state": "waiting_for_edit_datetime",
            "edit_task_id": state_data["edit_task_id"],
            "new_task_text": message.text,
        }

        bot.send_message(
            chat_id,
            "Теперь отправь новую дату и время выполнения.\n\n"
            "Например:\n"
            "завтра, 12:00\n"
            "15 июня, 18:30\n"
            "01.07.2026, 13:00 - 17:00"
        )
        return

    if state == "waiting_for_edit_datetime":
        task_id = state_data["edit_task_id"]
        new_text = state_data["new_task_text"]

        start_time, end_time = parse_user_datetime(message.text)

        if start_time is None:
            bot.send_message(
                chat_id,
                "Не удалось распознать дату и время.\n\n"
                "Попробуй один из вариантов:\n"
                "завтра, 12:00\n"
                "15 июня, 18:30\n"
                "01.07.2026, 13:00 - 17:00"
            )
            return

        success = update_task(user_id, task_id, new_text, start_time)

        if success:
            formatted_date = format_date_for_user(start_time)

            bot.send_message(
                chat_id,
                "Задача обновлена ✅\n\n"
                f"Новый текст: {new_text}\n"
                f"Новая дата и время: {formatted_date}",
                reply_markup=back_to_menu_keyboard()
            )
        else:
            bot.send_message(
                chat_id,
                "Не удалось найти задачу.",
                reply_markup=back_to_menu_keyboard()
            )

        user_states.pop(user_id, None)


if __name__ == "__main__":
    create_database()
    print("База данных готова")
    print("Бот запускается через pyTelegramBotAPI...")

    bot.infinity_polling()