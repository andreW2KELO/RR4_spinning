import time
from PIL import ImageGrab
import keyboard
import mouse


def is_need_to_eat():
    img = ImageGrab.grab(bbox=(187, 989, 188, 990)).load()[0, 0]
    return True if img[0] > img[1] else False


def is_need_to_tea():
    img = ImageGrab.grab(bbox=(187, 1048, 188, 1049)).load()[0, 0]
    return True if img[0] > img[1] else False


def is_ready_to_scoop():
    img = ImageGrab.grab(bbox=(300, 960, 301, 961)).load()[0, 0]
    return (120, 130, 30) <= img <= (183, 199, 56)


def main():
    while True:
        if keyboard.is_pressed('9'):
            break
        # mouse.move(900, 950, duration=0.1)
        mouse.click(button='left')
        time.sleep(0.1)
        # if is_ready_to_scoop():
        #     mouse.click(button='left')
        #     time.sleep(2.1)
        #     mouse.move(900, 950, duration=0.1)
        #     mouse.click(button='left')
        #     time.sleep(0.1)
        #     keyboard.press_and_release('5')

        # if is_need_to_eat():
        #     keyboard.press_and_release('5')
        #
        # if is_need_to_tea():
        #     keyboard.press_and_release('4')


if __name__ == '__main__':
    time.sleep(2)
    main()
    # img = ImageGrab.grab(bbox=(300, 960, 301, 961)).load()[0, 0]
    # print(img)
