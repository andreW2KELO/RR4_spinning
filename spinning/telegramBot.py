from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram import F
from io import BytesIO
from PIL import ImageGrab
import os
from dotenv import load_dotenv
import asyncio
import FishDataBase
from NewOOPSpinning import FishingSupervisor
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

AUTHORIZED_USER_IDS = {
    1923926414,
}

router = Router()

main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="🖥️ Экран"),
            types.KeyboardButton(text="📊 Сегодня"),
        ]
    ],
    resize_keyboard=True,
    # is_persistent=True,
    # one_time_keyboard=False,
    input_field_placeholder="Выберите команду",
)


async def check_access(message: types.Message) -> bool:
    if message.from_user.id not in AUTHORIZED_USER_IDS:
        await message.answer(f"Съебало в страхе уебище")
        return False

    return True


async def send_screenshot(message: types.Message):
    screenshot = ImageGrab.grab()

    buffer = BytesIO()
    screenshot.save(buffer, format="JPEG", quality=85)

    photo = BufferedInputFile(
        buffer.getvalue(),
        filename="screen.jpg",
    )

    await message.answer_photo(photo)


async def send_today_statistics(message: types.Message):
    stats = await asyncio.to_thread(
        FishDataBase.get_statistics_by_day,
        day=message.date,
    )
    await message.answer(f"Статистика за сегодня\n"
                         f"Кол-во рыб: {stats['today']}\n"
                         f"Зачётных: {stats['zach']}\n"
                         f"Трофейных: {stats['trof']}\n"
                         f"Редких трофеев: {stats['blue']}")


@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🎣 Управление ботом Russian Fishing 4\n\n"

        "📊 Аналитика:\n"
        "/today — статистика за сегодня\n"
        "/stats ДД.ММ.ГГГГ — статистика за выбранный день\n\n"

        "🖥 Управление:\n"
        "/screen — сделать скриншот экрана\n"
        "/pause — поставить бота на паузу\n"
        "/resume — возобновить работу бота\n"
        "/shutdown — выключить рыболовного бота\n"
        "/restart — перезапустить рыболовного бота\n\n"

        "🖱 Мышь:\n"
        "/click X Y — нажать ЛКМ по координатам\n"
        "/click X Y right — нажать ПКМ\n"
        "/click_text ТЕКСТ — найти надпись и нажать на неё\n\n"

        "🚶 Передвижение:\n"
        "/move forward 5 — пройти вперёд 5 шагов\n"
        "/move back 5 — пройти назад\n"
        "/move left 5 — пройти влево\n"
        "/move right 5 — пройти вправо\n\n"

        "🔐 Прочее:\n"
        "/myid — показать ваш Telegram ID\n\n"

        "Примеры:\n"
        "/stats 01.08.2026\n"
        "/click 960 540\n"
        "/click 960 540 right\n"
        "/click_text ПРОДАТЬ\n"
        "/move forward 3",
        reply_markup=main_keyboard,
    )


@router.message(Command('myid'))
async def myid_command(message: types.Message):
    await message.answer(f"Ваш id {message.from_user.id}")


@router.message(Command('stats'))
async def stats_command(message: types.Message):
    if not await check_access(message):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Формат: /stats <день в формате дд.мм.гггг>"
        )
        return

    stats = await asyncio.to_thread(
        FishDataBase.get_statistics_by_day,
        day=datetime.strptime(parts[1], "%d.%m.%Y"),
    )

    await message.answer(f"Статистика за {parts[1]}\n"
                         f"Всего было поймано: {stats['today']}\n"
                         f"Зачётных: {stats['zach']}\n"
                         f"Трофейных: {stats['trof']}\n"
                         f"Редких трофеев: {stats['blue']}")


@router.message(Command('today'))
async def today_command(message: types.Message):
    await send_today_statistics(message)


@router.message(F.text == "📊 Сегодня")
async def today_button(message: types.Message):
    await send_today_statistics(message)


@router.message(F.text == "🖥️ Экран")
async def screen_button(message: types.Message):
    if not await check_access(message):
        return

    await send_screenshot(message)


@router.message(Command("screen"))
async def screen_command(message: types.Message):
    if not await check_access(message):
        return

    await send_screenshot(message)


@router.message(Command("click"))
async def click_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    parts = message.text.split()

    if len(parts) not in {3, 4}:
        await message.answer(
            "Формат: /click X Y [left|right]"
        )
        return

    try:
        x = int(parts[1])
        y = int(parts[2])
    except ValueError:
        await message.answer("X и Y должны быть числами")
        return

    button = parts[3].lower() if len(parts) == 4 else "left"

    supervisor.command_queue.put({
        "type": "click",
        "x": x,
        "y": y,
        "button": button,
    })

    await message.answer(
        f"Команда поставлена в очередь: {button} ({x}, {y})"
    )


@router.message(Command("move"))
async def move_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Формат: /move forward 5"
        )
        return

    direction = parts[1].lower()

    try:
        steps = int(parts[2])
    except ValueError:
        await message.answer("Количество шагов должно быть числом")
        return

    supervisor.command_queue.put({
        "type": "move",
        "direction": direction,
        "steps": steps,
    })

    await message.answer("Команда движения отправлена")


@router.message(Command("click_text"))
async def click_text_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    parts = message.text.split(
        maxsplit=1,
    )

    if len(parts) != 2:
        await message.answer(
            "Формат: /click_text ПРОДАТЬ"
        )
        return

    supervisor.command_queue.put({
        "type": "click_text",
        "text": parts[1],
    })

    await message.answer(
        f'Ищу и нажимаю: "{parts[1]}"'
    )


@router.message(Command("restart"))
async def restart_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    await message.answer("Перезапускаю рыболовного бота")

    await asyncio.to_thread(
        supervisor.restart_worker
    )

    await message.answer("Рыболовный бот перезапущен")


@router.message(Command("pause"))
async def pause_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    supervisor.command_queue.put({
        "type": "pause",
    })

    await message.answer("Рыболовный бот остановлен")


@router.message(Command("resume"))
async def resume_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    supervisor.command_queue.put({
        "type": "resume",
    })

    await message.answer("Рыболовный бот возобновил работу")


@router.message(Command("shutdown"))
async def shutdown_command(message: types.Message, supervisor: FishingSupervisor):
    if not await check_access(message):
        return

    supervisor.command_queue.put({
        "type": "shutdown",
    })

    await message.answer("Рыболовный бот выключен")


def run_telegram_bot(supervisor: FishingSupervisor):
    bot = Bot(TOKEN)
    dispatcher = Dispatcher()

    dispatcher.include_router(router)
    dispatcher["supervisor"] = supervisor

    return bot, dispatcher
