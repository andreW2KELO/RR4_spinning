# Бот для ловли рыбы в RussianFishing4 на спиннинг
import cv2
import numpy as np
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from io import BytesIO
from difflib import SequenceMatcher

import keyboard
import mouse
import pytesseract
import win32gui
from PIL import ImageGrab, Image, ImageOps
from colorama import init, Fore

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

TOKEN = "6330587531:AAGdkhe2x3lYVaNIPtARomCQeIB266Nf_Yg"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

template_fish = cv2.imread('../sea/fish.png', cv2.IMREAD_COLOR)
template_reel = cv2.imread('../sea/reel.png', cv2.IMREAD_COLOR)
template_reel2 = cv2.imread('../sea/reel2.png', cv2.IMREAD_COLOR)

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


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"⏱ {func.__name__} выполнена за {end - start:.4f} сек")
        return result

    return wrapper


@timeit
def press_take_fish():
    mouse.release(button='right')
    keyboard.release('shift')
    mouse.release(button='left')
    mouse.move(910, 958, absolute=True, duration=0.05)
    mouse.click(button='left')


@timeit
def press_throw_away_fish():
    mouse.release(button='right')
    keyboard.release('shift')
    mouse.release(button='left')
    mouse.move(1161, 958, absolute=True, duration=0.05)
    mouse.click(button='left')


def release_all_button():
    mouse.release(button='left')
    mouse.release(button='right')
    keyboard.release('shift')


def button_v_sadok_on_screen():
    image = img_grab.crop((790, 949, 876, 970))
    return searching_coincidence(recognize_the_text(image), 'в садок')


def is_ready_to_throwing():
    image = img_grab.crop((530, 1020, 730, 1040))
    return searching_coincidence(recognize_the_text(image), 'снасть готова к забросу')


def similarity(str1: str, str2: str) -> float:
    ratio = SequenceMatcher(None, str1, str2).ratio()
    return round(ratio * 100, 2)


def searching_coincidence(text_lst: list, pat='движение в придонном слое.'):
    for st in text_lst:
        if similarity(st, pat) > 50:
            return True
    return False


def recognize_the_text(image):
    """ Распознает текст с помощью pytesseract """
    image_resized = image.resize((image.width * 3, image.height * 3), Image.LANCZOS)
    gray = image_resized.convert('L')
    inverted = ImageOps.invert(gray)
    bw = inverted.point(lambda x: 0 if x < 150 else 255, "L")

    variants = [gray, inverted, bw]

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(
            lambda img: pytesseract.image_to_string(
                img, lang="rus", config="--oem 3 --psm 7"
            ), variants)
        )

    return [i.strip().lower() for i in results]


def is_need_to_eat():
    img = img_grab.crop((187, 989, 188, 990)).load()[0, 0]
    return True if img[0] > img[1] else False


def is_need_to_tea():
    img = img_grab.crop((187, 1048, 188, 1049)).load()[0, 0]
    return True if img[0] > img[1] else False


def zach_trof_blue_just(arr: np.ndarray):
    mask_blue = np.all(arr == [72, 169, 255], axis=2)
    if mask_blue.any():
        return "blue"

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mask_trof = (216 <= r) & (r <= 228) & (189 <= g) & (g <= 200) & (47 <= b) & (b <= 79)
    if mask_trof.any():
        return "trof"

    mask_zach = np.all(arr == [183, 199, 56], axis=2)
    if mask_zach.any():
        return "zach"

    return None


@timeit
def is_good_fish():
    global count, zach, trof, blue

    img = ImageGrab.grab(bbox=(600, 110, 900, 130)).convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    cls = zach_trof_blue_just(arr)

    match cls:
        case "zach":
            zach += 1
        case "trof":
            trof += 1
        case "blue":
            blue += 1
        case None:
            return False

    count += 1
    return True


def trigger_to_elevate_rod_if_not_rainbow_line():
    tmp = 0 if win_size[-1] == 1050 else 2
    img = img_grab.crop((1234, 1011 - tmp, 1235, 1012 - tmp)).load()[0, 0]

    return img[0] > 170 and img[1] > 170 and img[2] > 170

@timeit
def trigger_to_elevate_rod_if_have_rainbow_line(threshold=0.9):
    tmp = 0 if win_size[-1] == 1050 else 1

    screenshot = cv2.cvtColor(np.array(ImageGrab.grab(
        bbox=(1157, 1019 - tmp, 1177, 1030 - tmp))
    ), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template_reel, cv2.TM_CCOEFF_NORMED)
    result2 = cv2.matchTemplate(screenshot, template_reel2, cv2.TM_CCOEFF_NORMED)

    _, max_val, _, _ = cv2.minMaxLoc(result)
    _, max_val2, _, _ = cv2.minMaxLoc(result2)

    return max_val >= threshold or max_val2 >= threshold


@timeit
def new_throwing():
    keyboard.press('shift')
    mouse.press(button='left')
    time.sleep(0.5)
    mouse.release(button='left')
    keyboard.release('shift')
    time.sleep(((100 / 100) * 1.9 / 0.57) + 1)


@timeit
def is_fish_on_hook(threshold=0.6):  # threshold — точность совпадения (0.8 = 80%).
    global template_fish

    screenshot = ImageGrab.grab(bbox=(532, 1008, 567, 1041))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template_fish, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val >= threshold


def do_choice_take_or_throw_away():
    if is_good_fish():
        press_take_fish()
    else:
        press_throw_away_fish()


def catching_fish(is_rainbow_line):
    global img_grab

    mouse.press('left')
    keyboard.press('shift')

    while True:
        img_grab = ImageGrab.grab()
        is_ready = is_ready_to_throwing()
        is_button_on_screen = button_v_sadok_on_screen()

        is_trigger_elevate = trigger_to_elevate_rod_if_have_rainbow_line() \
            if is_rainbow_line == 'да' else trigger_to_elevate_rod_if_not_rainbow_line()

        if is_ready:
            break

        if is_button_on_screen:
            time.sleep(0.3)
            do_choice_take_or_throw_away()
            break

        if is_trigger_elevate:
            mouse.press(button='right')
            while True:
                img_grab = ImageGrab.grab()
                is_ready = is_ready_to_throwing()
                is_button_on_screen = button_v_sadok_on_screen()
                is_trigger_elevate = trigger_to_elevate_rod_if_have_rainbow_line() \
                    if is_rainbow_line == 'да' else trigger_to_elevate_rod_if_not_rainbow_line()

                if not is_trigger_elevate and not is_button_on_screen and not is_ready:
                    trig = 1
                    break
                if is_ready:
                    trig = 1
                    break
                if is_button_on_screen:
                    trig = 2
                    break
                time.sleep(0.5)
            mouse.release(button='right')
            if trig == 2:
                time.sleep(0.3)
                do_choice_take_or_throw_away()
                break

    mouse.release(button='left')
    keyboard.release('shift')

    time.sleep(1)


def main(pause, slot_food, slot_drink, exit_button, is_rainbow_line):
    global img_grab
    t = round(time.time(), 1)
    time_for_eating = round(time.time())
    init(autoreset=True)
    print(Fore.RED + "НАЧАЛО РАБОТЫ")

    img_grab = ImageGrab.grab()

    if is_ready_to_throwing():
        release_all_button()
        new_throwing()

    while True:
        img_grab = ImageGrab.grab()

        mouse.press(button='left')
        # keyboard.press('shift')

        if is_fish_on_hook():
            release_all_button()
            catching_fish(is_rainbow_line)
            new_throwing()

        if is_ready_to_throwing():
            release_all_button()
            new_throwing()

        if time_for_eating + 200 <= time.time():
            if is_need_to_tea():
                keyboard.press_and_release(str(slot_drink))
            if is_need_to_eat():
                keyboard.press_and_release(str(slot_food))
            time_for_eating = round(time.time())

        if keyboard.is_pressed(exit_button):
            print(Fore.RED + "ПАУЗА")
            release_all_button()
            break

        if t + float(pause) <= round(time.time(), 1):
            release_all_button()
            # time.sleep(1.2)
            time.sleep(1.8)
            t = round(time.time(), 1)

    release_all_button()


if __name__ == '__main__':
    # t = round(time.time())
    # print(t)
    print(trigger_to_elevate_rod_if_have_rainbow_line())
    # main(5, '5', '4', '9', 'нет')
