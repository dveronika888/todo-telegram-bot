import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
from services.date_parser import parse_user_datetime


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class TaskStates(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_task_datetime = State()
    waiting_for_edit_text = State()
    waiting_for_edit_datetime = State()


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Новая задача", callback_data="menu:new")],
            [
                InlineKeyboardButton(text="📋 Мои задачи", callback_data="menu:list"),
                InlineKeyboardButton(text="✅ Выполненные", callback_data="menu:completed"),
            ],
            [InlineKeyboardButton(text="🧹 Очистить выполненные", callback_data="menu:clear_completed")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help")],
        ]
    )


def back_to_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 На главную", callback_data="menu:main")]
        ]
    )


def task_keyboard(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выполнить", callback_data=f"done:{task_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{task_id}"),
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{task_id}"),
                InlineKeyboardButton(text="🏠 На главную", callback_data="menu:main"),
            ],
        ]
    )


def format_date_for_user(date_text: str):
    try:
        return datetime.fromisoformat(date_text).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return date_text


async def show_tasks(message: types.Message, user_id: int):
    tasks = get_user_tasks(user_id)

    if not tasks:
        await message.answer(
            "У тебя пока нет активных задач.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    await message.answer("Твои активные задачи:")

    for task in tasks:
        task_id, task_text, due_date, status = task
        formatted_date = format_date_for_user(due_date)

        await message.answer(
            f"📝 {task_text}\n"
            f"⏰ {formatted_date}",
            reply_markup=task_keyboard(task_id)
        )


async def show_completed_tasks(message: types.Message, user_id: int):
    tasks = get_completed_tasks(user_id)

    if not tasks:
        await message.answer(
            "У тебя пока нет выполненных задач.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    text = "Выполненные задачи:\n\n"

    for task in tasks:
        task_id, task_text, due_date, status = task
        formatted_date = format_date_for_user(due_date)
        text += f"✅ {task_text} — {formatted_date}\n"

    await message.answer(
        text,
        reply_markup=back_to_menu_keyboard()
    )


@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Привет! Я бот для управления задачами.\n\n"
        "Я помогу создать задачу, сохранить её и напомнить о ней в нужное время.\n\n"
        "Выбери действие:",
        reply_markup=main_menu_keyboard()
    )


@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Как пользоваться ботом:\n\n"
        "➕ Новая задача — добавить задачу\n"
        "📋 Мои задачи — посмотреть активные задачи\n"
        "✅ Выполненные — посмотреть завершённые задачи\n"
        "🧹 Очистить выполненные — удалить завершённые задачи\n\n"
        "При создании задачи сначала введи текст задачи, затем дату и время.\n\n"
        "Дата может быть указана так:\n"
        "завтра, 12:00\n"
        "15 июня, 18:30\n"
        "01.07.2026, 13:00 - 17:00",
        reply_markup=back_to_menu_keyboard()
    )


@dp.message(Command("list"))
async def list_command(message: types.Message):
    await show_tasks(message, message.from_user.id)


@dp.message(Command("completed"))
async def completed_command(message: types.Message):
    await show_completed_tasks(message, message.from_user.id)


@dp.message(Command("clear_completed"))
async def clear_completed_command(message: types.Message):
    user_id = message.from_user.id
    deleted_count = clear_completed_tasks(user_id)

    if deleted_count == 0:
        await message.answer(
            "Выполненных задач для удаления нет.",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await message.answer(
            f"Удалено выполненных задач: {deleted_count} 🗑️",
            reply_markup=back_to_menu_keyboard()
        )


@dp.callback_query(F.data == "menu:main")
async def menu_main(callback: types.CallbackQuery):
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "menu:new")
async def menu_new_task(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TaskStates.waiting_for_task_text)

    await callback.message.answer("Отправь текст новой задачи.")
    await callback.answer()


@dp.callback_query(F.data == "menu:list")
async def menu_list(callback: types.CallbackQuery):
    await show_tasks(callback.message, callback.from_user.id)
    await callback.answer()


@dp.callback_query(F.data == "menu:completed")
async def menu_completed(callback: types.CallbackQuery):
    await show_completed_tasks(callback.message, callback.from_user.id)
    await callback.answer()


@dp.callback_query(F.data == "menu:clear_completed")
async def menu_clear_completed(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    deleted_count = clear_completed_tasks(user_id)

    if deleted_count == 0:
        await callback.message.answer(
            "Выполненных задач для удаления нет.",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await callback.message.answer(
            f"Удалено выполненных задач: {deleted_count} 🗑️",
            reply_markup=back_to_menu_keyboard()
        )

    await callback.answer()


@dp.callback_query(F.data == "menu:help")
async def menu_help(callback: types.CallbackQuery):
    await callback.message.answer(
        "Как пользоваться ботом:\n\n"
        "➕ Новая задача — добавить задачу\n"
        "📋 Мои задачи — посмотреть активные задачи\n"
        "✅ Выполненные — посмотреть завершённые задачи\n"
        "🧹 Очистить выполненные — удалить завершённые задачи\n\n"
        "При создании задачи сначала введи текст задачи, затем дату и время.\n\n"
        "Дата может быть указана так:\n"
        "завтра, 12:00\n"
        "15 июня, 18:30\n"
        "01.07.2026, 13:00 - 17:00",
        reply_markup=back_to_menu_keyboard()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("done:"))
async def done_callback(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = mark_task_done(user_id, task_id)

    if success:
        await callback.message.edit_text(
            "Задача отмечена как выполненная ✅",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await callback.answer("Задача не найдена", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("delete:"))
async def delete_callback(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = delete_task(user_id, task_id)

    if success:
        await callback.message.edit_text(
            "Задача удалена 🗑️",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await callback.answer("Задача не найдена", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("edit:"))
async def edit_callback(callback: types.CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await state.update_data(edit_task_id=task_id, user_id=user_id)
    await state.set_state(TaskStates.waiting_for_edit_text)

    await callback.message.answer("Отправь новый текст задачи.")
    await callback.answer()


@dp.message(TaskStates.waiting_for_task_text)
async def task_text_received(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Создание задачи отменено.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    await state.update_data(task_text=message.text)
    await state.set_state(TaskStates.waiting_for_task_datetime)

    await message.answer(
        "Задача принята.\n\n"
        f"Текст задачи: «{message.text}»\n\n"
        "Теперь укажи дату и время выполнения.\n\n"
        "Например:\n"
        "завтра, 12:00\n"
        "15 июня, 18:30\n"
        "01.07.2026, 13:00 - 17:00"
    )


@dp.message(TaskStates.waiting_for_task_datetime)
async def task_datetime_received(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Создание задачи отменено.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    user_id = message.from_user.id
    data = await state.get_data()

    task_text = data["task_text"]
    task_datetime = message.text

    start_time, end_time = parse_user_datetime(task_datetime)

    if start_time is None:
        await message.answer(
            "Не удалось распознать дату и время.\n\n"
            "Попробуй один из вариантов:\n"
            "завтра, 12:00\n"
            "15 июня, 18:30\n"
            "01.07.2026, 13:00 - 17:00"
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

    await message.answer(
        "Задача добавлена ✅\n\n"
        f"Задача: «{task_text}»\n"
        f"Дата и время: {formatted_date}",
        reply_markup=back_to_menu_keyboard()
    )

    await state.clear()


@dp.message(TaskStates.waiting_for_edit_text)
async def edit_text_received(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Редактирование отменено.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    await state.update_data(new_task_text=message.text)
    await state.set_state(TaskStates.waiting_for_edit_datetime)

    await message.answer("Теперь отправь новую дату и время выполнения.")


@dp.message(TaskStates.waiting_for_edit_datetime)
async def edit_datetime_received(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Редактирование отменено.",
            reply_markup=back_to_menu_keyboard()
        )
        return

    data = await state.get_data()

    user_id = data["user_id"]
    task_id = data["edit_task_id"]
    new_text = data["new_task_text"]
    new_due_date = message.text

    start_time, end_time = parse_user_datetime(new_due_date)

    if start_time is None:
        await message.answer(
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

        await message.answer(
            "Задача обновлена ✅\n\n"
            f"Новый текст: {new_text}\n"
            f"Новая дата и время: {formatted_date}",
            reply_markup=back_to_menu_keyboard()
        )
    else:
        await message.answer(
            "Не удалось найти задачу.",
            reply_markup=back_to_menu_keyboard()
        )

    await state.clear()


@dp.message()
async def handle_task_text(message: types.Message):
    await message.answer(
        "Я не понял сообщение.\n\n"
        "Чтобы добавить задачу, нажми /start и выбери «➕ Новая задача».",
        reply_markup=back_to_menu_keyboard()
    )


async def main():
    create_database()
    print("База данных готова")

    me = await bot.get_me()
    print(f"Бот подключен: @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())