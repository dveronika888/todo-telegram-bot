import os
from dotenv import load_dotenv

print("Текущая папка:", os.getcwd())

loaded = load_dotenv()

print("load_dotenv:", loaded)

BOT_TOKEN = os.getenv("BOT_TOKEN")

print("BOT_TOKEN =", BOT_TOKEN)