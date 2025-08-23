# Бот для ловли рыбы в RussianFishing4 на фидер

"""Идеи
1) Чтобы лучше различались пиксели (ночью белые пиксели темнее) разделить прочтение текса на ночь и день
2) Анализировать чат (вести подсчет сходов)
"""

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
from PIL import ImageGrab, Image, ImageOps

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

TOKEN = "6330587531:AAGdkhe2x3lYVaNIPtARomCQeIB266Nf_Yg"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

template = cv2.imread('fish.png', cv2.IMREAD_COLOR)

router = Router()

zach = 0
trof = 0
blue = 0
count = 0
img_grab = ImageGrab.grab()


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
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

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
    imgage = ImageGrab.grab().crop((790, 949, 876, 970))
    return searching_coincidence(recognize_the_text(imgage), 'в садок')


def is_ready_to_throwing():
    image = ImageGrab.grab().crop((530, 1020, 730, 1040))
    return searching_coincidence(recognize_the_text(image), 'снасть готова к забросу')


def similarity(str1: str, str2: str) -> float:
    ratio = SequenceMatcher(None, str1, str2).ratio()
    return round(ratio * 100, 2)


def searching_coincidence(text_lst: list, pat='движение в придонном слое.'):
    print(f'Распознанные текста: {text_lst}\n'
          f'Заданный патерн: {pat}\n'
          )
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
def good_fish():
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


def trigger_to_elevate_rod():
    img = img_grab.crop((1235, 1009, 1236, 1010)).load()[0, 0]
    img2 = img_grab.crop((1235, 1011, 1236, 1012)).load()[0, 0]

    return ((img[0] > 170 and img[1] > 170 and img[2] > 170)
            or (img2[0] > 170 and img2[1] > 170 and img2[2] > 170))


@timeit
def new_throwing():
    mouse.press(button='left')
    time.sleep(1.2)
    mouse.release(button='left')
    time.sleep(2)
    mouse.press(button='left')
    time.sleep(0.1)
    mouse.release(button='left')
    keyboard.press_and_release('0')
    time.sleep(1)
    keyboard.press_and_release('z')


def put_the_rod_back():
    keyboard.press_and_release('0')
    time.sleep(1)
    keyboard.press_and_release('z')


def is_bite_indicator_on_image(img, threshold=10):
    arr = np.array(img.convert("RGB"), dtype=np.uint8)
    mask = (arr[..., 0] > 190) & (arr[..., 1] > 190) & (arr[..., 2] > 190)

    return np.count_nonzero(mask) < threshold


@timeit
def catching_fish():
    global img_grab
    mouse.press(button='left')
    keyboard.press('shift')
    while True:
        img_grab = ImageGrab.grab()
        if trigger_to_elevate_rod():
            mouse.press(button='right')
            while True:
                img_grab = ImageGrab.grab()
                if is_ready_to_throwing():
                    trig = 1
                    break
                if button_v_sadok_on_screen():
                    trig = 2
                    break
                time.sleep(1)
            mouse.release(button='right')
            if trig == 2:
                time.sleep(0.3)
                if good_fish():
                    press_take_fish()
                else:
                    press_throw_away_fish()
            break

    mouse.release(button='left')
    keyboard.release('shift')

    time.sleep(1)


@timeit
def first_white_px_detected(img, x=0, y=0, thr=200):
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    mask = (arr[..., 0] > thr) & (arr[..., 1] > thr) & (arr[..., 2] > thr)
    mp = mask[:, :-1] & mask[:, 1:]
    mp_trans = mp.T
    idxs = np.flatnonzero(mp_trans.ravel())
    if idxs.size == 0:
        return None

    row_mp_trans, col_mp_trans = divmod(idxs[0], mp_trans.shape[1])
    i = row_mp_trans
    j = col_mp_trans

    return i + 1 + x, j + y, i + x, j + y


@timeit
def detected_rod(n_tips=3, min_dx=50):
    img = ImageGrab.grab()
    size = 15
    lst = [400, 400]
    res = []

    for i in range(n_tips):
        temp = img.crop((lst[0], lst[1], 1700, 900))
        is_detected_rod = first_white_px_detected(temp, x=lst[0], y=lst[1])
        if is_detected_rod is not None:
            x, y, i, j = is_detected_rod
            res.append([x - size, y - size, x + size, y + size])
            lst[0] = i + min_dx
        else:
            res.append(None)

    if None in res:
        print(f"{res}\n"
              f"Какая то из удочек не была зафиксирована")

    return res


@timeit
def is_fish_on_hook(threshold=0.6):  # threshold — точность совпадения (0.8 = 80%).
    global template

    screenshot = ImageGrab.grab().crop((532, 1008, 567, 1041))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    print(max_val >= threshold)
    return max_val >= threshold


def main():
    global img_grab
    coord_rods = detected_rod(n_tips=3)

    while True:
        img_grab = ImageGrab.grab()

        for i in range(len(coord_rods)):
            if is_bite_indicator_on_image(img_grab.crop(coord_rods[i])):
                release_all_button()
                keyboard.press_and_release(str(i + 1))
                time.sleep(1)
                if is_fish_on_hook():
                    catching_fish()
                    new_throwing()
                else:
                    put_the_rod_back()
                time.sleep(1)
                coord_rods = detected_rod()
                break

        if is_need_to_tea():
            keyboard.press_and_release('4')
            time.sleep(0.2)
            keyboard.press_and_release('4')
        if is_need_to_eat():
            keyboard.press_and_release('5')
            time.sleep(0.2)
            keyboard.press_and_release('5')


if __name__ == '__main__':
    import threading

    time.sleep(2)
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()

    try:
        main()
    except KeyboardInterrupt:
        pass
