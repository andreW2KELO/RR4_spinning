# Бот для изготовления и копания червей в RussianFishing4

import time
import pyautogui
from PIL import ImageGrab, Image
import threading


def func2():
    def eat():
        img = ImageGrab.grab().crop((306, 989, 307, 990)).load()[0, 0]
        return True if img[1] < img[0] else False

    def light():
        img = ImageGrab.grab().crop((306, 1048, 307, 1049)).load()[0, 0]
        return True if img[1] < img[0] else False

    while True:
        if eat():
            pyautogui.typewrite(['5'])
        if light():
            pyautogui.typewrite(['4'])
        time.sleep(60)


def func1():
    while True:
        pyautogui.click(button='left')
        pyautogui.press('space')
        time.sleep(0.01)


if __name__ == '__main__':
    time.sleep(1)
    e1 = threading.Event()
    # e2 = threading.Event()
    t1 = threading.Thread(target=func1)
    # t2 = threading.Thread(target= func2)
    t1.start()
    # t2.start()
