# Бот для пилкинга на море RussianFishing4

import time
from PIL import ImageGrab
import pyautogui


def fish_on_hook():
    img = ImageGrab.grab().crop((545, 1022, 550, 1027))
    pixels = img.load()
    res = set()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = pixels[i, j]
            res.add(color)
    return True if len(res) == 1 else False


def pick_up():
    with pyautogui.hold('ctrl'):
        pyautogui.click(button='right')


def func_for_sea():
    while True:
        if fish_on_hook():
            pick_up()
            break
        pyautogui.mouseDown(button='right')
        time.sleep(0.4)
        pyautogui.mouseUp(button='right')
        time.sleep(1.5)


if __name__ == '__main__':
    time.sleep(1)
    func_for_sea()