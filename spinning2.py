# Бот для ловли рыбы в RussianFishing4 на спиннинг

import random
import sys

from PIL import ImageGrab
import time
import pyautogui
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import threading
import keyboard

count = 0
bot = Bot(token="6330587531:AAGdkhe2x3lYVaNIPtARomCQeIB266Nf_Yg")
dp = Dispatcher(bot)
zach = 0
trof = 0
blue = 0
flag = True
img_grab = None


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await bot.send_message(message.from_user.id, f'Кол-во рыб: {count}\n'
                                                 f'Зачетных: {zach}\n'
                                                 f'Трофейных {trof}\n'
                                                 f'Редких трофеев: {blue}')


@dp.message_handler(commands=["screen"])
async def screen(message: types.Message):
    img_grab.save('чпок.png')
    with open('чпок.png', 'rb') as photo:
        await bot.send_photo(message.from_user.id, photo)


@dp.message_handler(commands=[''])
async def trophy(message: types.Message):
    pass


@dp.message_handler(commands=['alt_f4'])
async def out(message: types.Message):
    await bot.send_message(message.from_user.id, 'Give me your password: ')
    print(message.text)


def eat():
    img = img_grab.crop((187, 989, 188, 990)).load()[0, 0]
    return True if img[0] > img[1] else False


def light():
    img = img_grab.crop((187, 1048, 188, 1049)).load()[0, 0]
    return True if img[0] > img[1] else False


def zach_trof_blue_just(color):
    global zach, trof, blue
    if color[0] == 183 and color[1] == 199 and color[2] == 56:
        zach += 1
        return True
    elif 216 <= color[0] <= 228 and 189 <= color[1] <= 200 and 47 <= color[2] <= 79:
        trof += 1
        return True
    elif color[0] == 72 and color[1] == 169 and color[2] == 255:
        blue += 1
        return True
    else:
        return False


def good_fish():
    global count
    t0 = time.perf_counter()
    img = ImageGrab.grab().crop((600, 97, 900, 98))
    pixels = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = pixels[i, j]
            if zach_trof_blue_just(color):
                print(time.perf_counter() - t0)
                count += 1
                return True
    print(time.perf_counter() - t0)
    return False


def press_release():
    pyautogui.mouseUp(button='right')
    pyautogui.keyUp('shift')
    pyautogui.mouseUp(button='left')
    pyautogui.leftClick(x=1161, y=958)


def press_take():
    pyautogui.mouseUp(button='right')
    pyautogui.keyUp('shift')
    pyautogui.mouseUp(button='left')
    pyautogui.leftClick(x=910, y=958)


def fish_on_hook():
    img = img_grab.crop((547, 1010, 554, 1011))
    pixels = img.load()
    res = set()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = pixels[i, j]
            if color[0] > 170 and color[1] > 170 and color[2] > 170:
                res.add(color)
    return True if len(res) == 1 else False


def new_throwing():
    with pyautogui.hold('shift'):
        pyautogui.mouseDown(button='left')
        time.sleep(0.1)
    pyautogui.mouseUp(button='left')
    time.sleep(4)  # time.sleep(4) для джиг


# def new_throwing():  # 70%
#     pyautogui.mouseDown(button='left')
#     time.sleep(1.7)
#     pyautogui.mouseUp(button='left')
#     time.sleep(3)

def ready_to_throwing():
    img = img_grab.crop((682, 1029, 683, 1030)).load()[0, 0]
    return True if img[0] > 170 and img[1] > 170 and img[2] > 170 else False


def button_press_on_screen():
    img = img_grab.crop((855, 959, 855 + 1, 959 + 1)).load()[0, 0]
    return True if img[0] > 200 and img[1] > 200 and img[2] > 200 else False


def helper():
    if good_fish():
        press_take()
    else:
        press_release()


# def pick_up():
#     with pyautogui.hold('ctrl'):
#         pyautogui.click(button='right')

def catching_fish():
    global img_grab
    # pick_up() # для джига
    pyautogui.mouseDown(button='left')
    pyautogui.keyDown('shift')
    while True:
        img_grab = ImageGrab.grab()
        if trigger():
            pyautogui.mouseDown(button='right')
            while True:
                img_grab = ImageGrab.grab()
                if ready_to_throwing():
                    trig = 1
                    break
                if button_press_on_screen():
                    trig = 2
                    break
                time.sleep(1)
            pyautogui.mouseUp(button='right')
            if trig == 2:
                time.sleep(0.3)
                helper()
            break
        time.sleep(1)
    pyautogui.mouseUp(button='left')
    pyautogui.keyUp('shift')


def trigger():  # это первоначальный рабочий12 + 1)).load()[0, 0]
    img = img_grab.crop((1235, 1009, 1236, 1010)).load()[0, 0]
    return True if img[0] > 170 and img[1] > 170 and img[2] > 170 else False


def alt_f4():
    img = img_grab.crop((1236, 1038, 1236 + 1, 1038 + 1)).load()[0, 0]
    if img[0] < 170 and img[1] < 170 and img[2] < 170:
        with pyautogui.hold('alt'):
            pyautogui.press('f4')


def main(pause, key, key1, key2):
    global flag, img_grab
    # alt_f4()
    img_grab = ImageGrab.grab()
    if ready_to_throwing():
        new_throwing()
    # pyautogui.keyDown(key='shift')
    pyautogui.mouseDown(button='left')
    count = 0
    while True:
        img_grab = ImageGrab.grab()
        if eat():
            pyautogui.typewrite([key2, key2], interval=0.2)
        if light():
            pyautogui.typewrite([key1, key1], interval=0.2)
        if keyboard.is_pressed(key):
            flag = False
            break
        elif fish_on_hook():
            pyautogui.mouseUp(button='left')
            # pyautogui.keyUp(key='shift')
            catching_fish()
            break
        elif ready_to_throwing():
            pyautogui.mouseUp(button='left')
            # pyautogui.keyUp(key='shift')
            new_throwing()
            break
        elif count % pause == 0 and count > 0:  # elif count % 100 == 0 and count > 0:
            # pyautogui.click(button='right')
            pyautogui.mouseUp(button='left')
            # pyautogui.keyUp(key='shift')
            time.sleep(1.2)
            # pyautogui.keyDown(key='shift')
            pyautogui.mouseDown(button='left')

        count += 1
    pyautogui.mouseUp(button='left')
    # pyautogui.keyUp(key='shift')


def func1(pause, key, key1, key2):
    global flag
    while flag:
        main(pause, key, key1, key2)
    flag = True
# executor.start_polling(dp, skip_updates=True)
