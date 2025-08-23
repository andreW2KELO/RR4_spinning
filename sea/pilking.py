# Бот для ловли рыбы в RussianFishing4 на пилкерное удилище


from PIL import ImageGrab
import time
import random
import sys
import pyautogui
import threading
import keyboard
import pytesseract

count = 0
zach = 0
trof = 0
blue = 0
flag = True
img_grab = None


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
    img = ImageGrab.grab().crop((600, 97, 900, 98))
    pixels = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = pixels[i, j]
            if zach_trof_blue_just(color):
                count += 1
                return True
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
    img = ImageGrab.grab().crop((545, 1022, 550, 1027))
    pixels = img.load()
    res = set()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = pixels[i, j]
            if color[0] > 170 and color[1] > 170 and color[2] > 170:
                res.add(color)
    return True if len(res) == 1 else False


def new_throwing():
    pyautogui.leftClick()
    while_not_in_the_bottom_layer()
    pyautogui.leftClick()


# опускает приманку на дно до придонного слоя
def while_not_in_the_bottom_layer():
    while True:
        if move_in_the_bottom_layer():
            return
        if fish_on_hook():
            return
        time.sleep(0.1)


def ready_to_throwing():
    if searching_coincidence(recognize_the_text(), 'снасть готова к забросу'):
        return True
    return False



def button_press_on_screen():
    img = img_grab.crop((855, 959, 855 + 1, 959 + 1)).load()[0, 0]
    return True if img[0] > 200 and img[1] > 200 and img[2] > 200 else False


def helper():
    if good_fish():
        press_take()
    else:
        press_release()


def catching_fish():
    global img_grab
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


# return true if coincidence > 70%
def searching_coincidence(st: str, pat='движение в придонном слое.'):
    string = st.lower()
    count = 0
    for i in range(len(min(string, pat, key=len))):
        if string[i] == pat[i]:
            count += 1
    if (count / len(pat)) * 100 > 50:
        return True
    return False


# return text from image
def recognize_the_text():
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    image = ImageGrab.grab().crop((530, 1020, 730, 1040))
    text = pytesseract.image_to_string(image, lang='rus')
    # print(text)
    return text


# return True if move in the bottom layer
def move_in_the_bottom_layer():
    if searching_coincidence(recognize_the_text()):
        return True
    return False


def trigger():
    img = img_grab.crop((1235, 1009, 1236, 1010)).load()[0, 0]
    return True if img[0] > 170 and img[1] > 170 and img[2] > 170 else False


def main(pause, key, key1, key2):
    global flag, img_grab
    img_grab = ImageGrab.grab()

    if ready_to_throwing():
        print('new_throwing')
        new_throwing()
    count = 0
    test_count = 0
    while True:
        img_grab = ImageGrab.grab()
        if eat():
            pyautogui.typewrite(['5', '5'], interval=0.2)
        if light():
            pyautogui.typewrite(['4', '4'], interval=0.2)
        if keyboard.is_pressed(key):
            flag = False
            break
        elif fish_on_hook():
            print('fish on hook')
            catching_fish()
            print('fish on hook END')
            break
        elif ready_to_throwing():
            print('new_throwing')
            new_throwing()
            break
        # elif not move_in_the_bottom_layer():
        #     print('move_in_the_bottom_layer')
        #     pyautogui.typewrite(['enter'])
        #     while_not_in_the_bottom_layer()
        #     pyautogui.typewrite(['enter'])

        elif count % pause == 0 and count > 0:
            pyautogui.mouseDown(button='right')
            time.sleep(0.22)
            pyautogui.mouseUp(button='right')
            time.sleep(1)
        count += 1


def func1(pause, key, key1, key2):
    global flag
    while flag:
        main(pause, key, key1, key2)
    flag = True


if __name__ == '__main__':
    time.sleep(3)
    func1(12, '4', '5', '9')
