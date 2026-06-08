# test_aiohttp.py

import asyncio
import aiohttp

TOKEN = "8273279484:AAGqyfrVXvBqN0mBsaZiXBwr-0cLVCXnKdM"

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.telegram.org/bot{TOKEN}/getMe"
        ) as resp:
            print(resp.status)
            print(await resp.text())

asyncio.run(main())