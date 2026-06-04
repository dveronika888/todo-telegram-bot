import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F

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


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class TaskStates(StatesGroup):
    waiting_for_task_datetime = State()
    waiting_for_edit_text = State()
    waiting_for_edit_datetime = State()


def task_keyboard(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнить",
                    callback_data=f"done:{task_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"delete:{task_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Изменить",
                    callback_data=f"edit:{task_id}"
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я бот для управления задачами.\n\n"
        "Отправь мне текст задачи, а следующим сообщением — дату и время.\n\n"
        "Команды:\n"
        "/list — показать активные задачи\n"
        "/completed — показать выполненные задачи\n"
        "/done номер — отметить задачу выполненной\n"
        "/delete номер — удалить задачу\n"
        "/edit номер — изменить задачу\n"
        "/clear_completed — удалить выполненные задачи\n"
        "/help — помощь"
    )


@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Доступные команды:\n\n"
        "/start — начать работу\n"
        "/list — показать активные задачи\n"
        "/completed — показать выполненные задачи\n"
        "/done номер — отметить задачу выполненной\n"
        "/delete номер — удалить задачу\n"
        "/edit номер — изменить задачу\n"
        "/clear_completed — удалить выполненные задачи\n\n"
        "Пример добавления задачи:\n"
        "1. купить молоко\n"
        "2. 12:00, 3 июня"
    )


@dp.message(Command("list"))
async def list_command(message: types.Message):
    user_id = message.from_user.id
    tasks = get_user_tasks(user_id)

    if not tasks:
        await message.answer("У тебя пока нет активных задач.")
        return

    await message.answer("Твои активные задачи:")

    for task in tasks:
        task_id, task_text, due_date, status = task
        await message.answer(
            f"№{task_id}\n"
            f"📝 {task_text}\n"
            f"⏰ {due_date}",
            reply_markup=task_keyboard(task_id)
        )


@dp.message(Command("completed"))
async def completed_command(message: types.Message):
    user_id = message.from_user.id
    tasks = get_completed_tasks(user_id)

    if not tasks:
        await message.answer("У тебя пока нет выполненных задач.")
        return

    text = "Выполненные задачи:\n\n"

    for task in tasks:
        task_id, task_text, due_date, status = task
        text += f"№{task_id}. {task_text} — {due_date}\n"

    await message.answer(text)


@dp.message(Command("done"))
async def done_command(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Укажи номер задачи.\n\nПример:\n/done 1")
        return

    task_id = int(parts[1])
    success = mark_task_done(user_id, task_id)

    if success:
        await message.answer(f"Задача №{task_id} отмечена как выполненная ✅")
    else:
        await message.answer("Не удалось найти активную задачу с таким номером.")


@dp.message(Command("delete"))
async def delete_command(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Укажи номер задачи.\n\nПример:\n/delete 1")
        return

    task_id = int(parts[1])
    success = delete_task(user_id, task_id)

    if success:
        await message.answer(f"Задача №{task_id} удалена 🗑️")
    else:
        await message.answer("Не удалось найти задачу с таким номером.")


@dp.message(Command("clear_completed"))
async def clear_completed_command(message: types.Message):
    user_id = message.from_user.id
    deleted_count = clear_completed_tasks(user_id)

    if deleted_count == 0:
        await message.answer("Выполненных задач для удаления нет.")
    else:
        await message.answer(f"Удалено выполненных задач: {deleted_count} 🗑️")


@dp.message(Command("edit"))
async def edit_command(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Укажи номер задачи.\n\nПример:\n/edit 1")
        return

    task_id = int(parts[1])

    await state.update_data(edit_task_id=task_id, user_id=user_id)
    await state.set_state(TaskStates.waiting_for_edit_text)

    await message.answer(
        f"Редактирование задачи №{task_id}.\n\n"
        "Отправь новый текст задачи."
    )


@dp.callback_query(F.data.startswith("done:"))
async def done_callback(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = mark_task_done(user_id, task_id)

    if success:
        await callback.message.edit_text(f"Задача №{task_id} отмечена как выполненная ✅")
    else:
        await callback.answer("Задача не найдена", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("delete:"))
async def delete_callback(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success = delete_task(user_id, task_id)

    if success:
        await callback.message.edit_text(f"Задача №{task_id} удалена 🗑️")
    else:
        await callback.answer("Задача не найдена", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("edit:"))
async def edit_callback(callback: types.CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await state.update_data(edit_task_id=task_id, user_id=user_id)
    await state.set_state(TaskStates.waiting_for_edit_text)

    await callback.message.answer(
        f"Редактирование задачи №{task_id}.\n\n"
        "Отправь новый текст задачи."
    )

    await callback.answer()


@dp.message(TaskStates.waiting_for_edit_text)
async def edit_text_received(message: types.Message, state: FSMContext):
    await state.update_data(new_task_text=message.text)
    await state.set_state(TaskStates.waiting_for_edit_datetime)

    await message.answer("Теперь отправь новую дату и время выполнения.")


@dp.message(TaskStates.waiting_for_edit_datetime)
async def edit_datetime_received(message: types.Message, state: FSMContext):
    data = await state.get_data()

    user_id = data["user_id"]
    task_id = data["edit_task_id"]
    new_text = data["new_task_text"]
    new_due_date = message.text

    success = update_task(user_id, task_id, new_text, new_due_date)

    if success:
        await message.answer(
            f"Задача №{task_id} обновлена ✅\n\n"
            f"Новый текст: {new_text}\n"
            f"Новая дата и время: {new_due_date}"
        )
    else:
        await message.answer("Не удалось найти задачу с таким номером.")

    await state.clear()


@dp.message(TaskStates.waiting_for_task_datetime)
async def task_datetime_received(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    task_text = data["task_text"]
    task_datetime = message.text

    add_task(user_id, task_text, task_datetime)

    await message.answer(
        "Задача добавлена ✅\n\n"
        f"Задача: «{task_text}»\n"
        f"Дата и время: {task_datetime}"
    )

    await state.clear()


@dp.message()
async def handle_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await state.set_state(TaskStates.waiting_for_task_datetime)

    await message.answer(
        "Задача принята.\n\n"
        f"Текст задачи: «{message.text}»\n\n"
        "Теперь укажи дату и время выполнения."
    )


async def main():
    create_database()
    print("База данных готова")

    me = await bot.get_me()
    print(f"Бот подключен: @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())