import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart

from config.config import BOT_TOKEN
from database.db import create_database, add_task, get_user_tasks


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_tasks = {}


@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот для управления задачами.\n\n"
        "Отправь мне текст задачи, а следующим сообщением — дату и время."
    )


@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — начать работу\n"
        "/help — список команд\n"
        "/list — показать список задач\n\n"
        "Пример:\n"
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

    text = "Твои задачи:\n\n"

    for task in tasks:
        task_id, task_text, due_date, status = task
        text += f"{task_id}. {task_text} — {due_date}\n"

    await message.answer(text)


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_tasks:
        user_tasks[user_id] = {"task": text}
        await message.answer(
            "Задача принята.\n\n"
            f"Текст задачи: «{text}»\n\n"
            "Теперь укажи дату и время выполнения."
        )
    else:
        task_text = user_tasks[user_id]["task"]
        task_datetime = text

        add_task(user_id, task_text, task_datetime)

        await message.answer(
            "Задача добавлена ✅\n\n"
            f"Задача: «{task_text}»\n"
            f"Дата и время: {task_datetime}"
        )

        del user_tasks[user_id]


async def main():
    create_database()
    print("База данных готова")

    me = await bot.get_me()
    print(f"Бот подключен: @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())