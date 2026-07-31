# Бот для ловли рыбы в RussianFishing4 на спиннинг
import asyncio
from io import BytesIO

import win32gui
from PIL import ImageGrab

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

TOKEN = "6330587531:AAGdkhe2x3lYVaNIPtARomCQeIB266Nf_Yg"

router = Router()

zach = 0
trof = 0
blue = 0
count = 0
img_grab = ImageGrab.grab()


def get_rf4_client_rect(title_substr="Russian Fishing 4"):
    hwnd = None

    def enum_handler(h, _):
        nonlocal hwnd
        if win32gui.IsWindowVisible(h):
            if title_substr.lower() in win32gui.GetWindowText(h).lower():
                hwnd = h

    win32gui.EnumWindows(enum_handler, None)
    if not hwnd:
        raise RuntimeError("Окно RF4 не найдено")

    return win32gui.GetClientRect(hwnd)


win_size = get_rf4_client_rect()


@router.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer(f'Кол-во рыб: {count}\n'
                         f'Зачетных: {zach}\n'
                         f'Трофейных {trof}\n'
                         f'Редких трофеев: {blue}', message.from_user.id, )


@router.message(Command("screen"))
async def screen(message: types.Message):
    global img_grab
    buf = BytesIO()
    img_grab.save(buf, format="PNG")
    buf.seek(0)

    photo = BufferedInputFile(buf.getvalue(), filename="screen.png")
    await message.answer_photo(photo)


def run_bot_thread():
    async def _run():
        bot = Bot(TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        await dp.start_polling(bot, handle_signals=False, allowed_updates=dp.resolve_used_update_types())

    asyncio.run(_run())
