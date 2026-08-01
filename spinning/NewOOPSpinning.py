# Бот для ловли рыбы в RussianFishing4 на спиннинг

from dataclasses import dataclass
from enum import Enum, auto
import win32gui
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from difflib import SequenceMatcher
from pytesseract import Output
import multiprocessing as mp
import queue
import time
import keyboard
import mouse
import pytesseract
from PIL import ImageGrab, Image, ImageOps
from colorama import Fore
import os
from dotenv import load_dotenv
import asyncio
import FishDataBase

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise RuntimeError(
        "Не задан TELEGRAM_BOT_TOKEN"
    )

READY_BOX = (530, 1020, 730, 1040)
STEP_DURATION = 0.18
STEP_PAUSE = 0.05
DIRECTION_KEYS = {
    "forward": "w", "back": "s", "left": "a", "right": "d",
    "вперед": "w", "назад": "s", "влево": "a", "вправо": "d",
}
GAME_WINDOW_TITLES = {
    "Russian Fishing 4",
    "Русская Рыбалка 4",
}
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

template_fish = cv2.imread('template/fish.png', cv2.IMREAD_COLOR)
template_reel = cv2.imread('template/reel.png', cv2.IMREAD_COLOR)
template_reel2 = cv2.imread('template/reel2.png', cv2.IMREAD_COLOR)
template_v_sadok = cv2.imread('template/v_sadok.png', cv2.IMREAD_COLOR)
ready_template_original = cv2.imread("template/ready_to_cast.png", cv2.IMREAD_GRAYSCALE)
ready_template_original_night = cv2.imread("template/ready_to_cast_night.png", cv2.IMREAD_GRAYSCALE)


def prepare_text_image(image: Image.Image | np.ndarray):
    if isinstance(image, Image.Image):
        image_array = np.array(image.convert("L"))
    else:
        image_array = image

    image_array = cv2.GaussianBlur(image_array, (3, 3), 0)
    _, binary = cv2.threshold(image_array, 135, 255, cv2.THRESH_BINARY)

    return binary


ready_template_prepared = prepare_text_image(ready_template_original)
ready_template_prepared_night = prepare_text_image(ready_template_original_night)

img_grab = ImageGrab.grab()


def is_game_active() -> bool:
    window = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(window).strip()

    return any(
        expected.lower() in title.lower()
        for expected in GAME_WINDOW_TITLES
    )


def normalize_text(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("ё", "е")
    )


def text_similarity(first: str, second: str) -> float:
    return SequenceMatcher(
        None,
        normalize_text(first),
        normalize_text(second),
    ).ratio()


def find_text_on_screen(frame: Image.Image, target: str, min_confidence: float = 50, min_similarity: float = 0.72):
    enlarged = frame.resize(
        (frame.width * 2, frame.height * 2),
        Image.Resampling.LANCZOS,
    )

    data = pytesseract.image_to_data(
        enlarged,
        lang="rus+eng",
        config="--oem 3 --psm 11",
        output_type=Output.DICT,
    )

    candidates = []

    for index, recognized in enumerate(data["text"]):
        recognized = recognized.strip()

        if not recognized:
            continue

        try:
            confidence = float(data["conf"][index])
        except (ValueError, TypeError):
            continue

        if confidence < min_confidence:
            continue

        similarity = text_similarity(
            recognized,
            target,
        )

        if similarity < min_similarity:
            continue

        # Координаты относятся к увеличенному изображению.
        left = data["left"][index] // 2
        top = data["top"][index] // 2
        width = data["width"][index] // 2
        height = data["height"][index] // 2

        candidates.append({
            "text": recognized,
            "confidence": confidence,
            "similarity": similarity,
            "box": (
                left,
                top,
                left + width,
                top + height,
            ),
        })

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: (
            item["similarity"],
            item["confidence"],
        ),
    )


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        match func.__name__:
            case "is_fish_on_hook":
                if result:
                    print(f"⏱ {func.__name__} выполнена за {end - start:.4f} сек \t РЫБА НА КРЮЧКЕ")
            case "press_throw_away_fish":
                print('РЫБА ВЫБРОШЕНА')
            case "press_take_fish":
                print('РЫБА В САДКЕ')
            case "check":
                if result:
                    print(f"{func.__name__} IS DONE. Снасть готова к забросу")
        return result

    return wrapper


@timeit
def press_take_fish():
    mouse.move(
        910,
        958,
        absolute=True,
        duration=0.05,
    )

    time.sleep(0.08)

    mouse.press(button="left")
    time.sleep(0.08)
    mouse.release(button="left")

    # Даём игре полностью обработать закрытие окна.
    time.sleep(0.25)


@timeit
def press_throw_away_fish():
    mouse.move(
        1161,
        958,
        absolute=True,
        duration=0.05,
    )

    time.sleep(0.08)

    mouse.press(button="left")
    time.sleep(0.08)
    mouse.release(button="left")

    time.sleep(0.25)


def get_ready_template_score(frame: Image.Image, template) -> float:
    search_region = frame.crop(READY_BOX)
    prepared_region = prepare_text_image(search_region)

    template_height, template_width = ready_template_prepared.shape[:2]
    region_height, region_width = prepared_region.shape[:2]

    if template_width > region_width or template_height > region_height:
        return 0.0

    result = cv2.matchTemplate(prepared_region, template, cv2.TM_CCOEFF_NORMED)
    _, max_score, _, _ = cv2.minMaxLoc(result)

    return float(max_score)


@timeit
def is_fish_on_hook(threshold=0.6):  # threshold — точность совпадения (0.8 = 80%).
    global template_fish

    screenshot = ImageGrab.grab(bbox=(532, 1008, 567, 1041))
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template_fish, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val >= threshold


def is_button_v_sadok_on_screen(threshold=0.9):
    image = img_grab.crop((790, 949, 876, 970))
    screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template_v_sadok, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    return max_val >= threshold


def is_good_fish():
    img = ImageGrab.grab(bbox=(700, 50, 1200, 200)).convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    cls = zach_trof_blue_just(arr)
    if cls is None:
        return False
    FishDataBase.record_catch(cls)
    return True


def is_need_to_eat():
    img = img_grab.crop((187, 989, 188, 990)).load()[0, 0]
    return True if img[0] > img[1] else False


def is_need_to_tea():
    img = img_grab.crop((187, 1048, 188, 1049)).load()[0, 0]
    return True if img[0] > img[1] else False


def zach_trof_blue_just(arr: np.ndarray):
    mask_blue = np.all(arr == [89, 175, 251], axis=2)
    if mask_blue.any():
        return "blue"

    mask_trof = np.all(arr == [252, 196, 0], axis=2)
    if mask_trof.any():
        return "trof"

    mask_zach = np.all(arr == [155, 200, 63], axis=2)
    if mask_zach.any():
        return "zach"

    return None


def trigger_to_elevate_rod_if_not_rainbow_line():
    img = img_grab.crop((1234, 1009, 1235, 1010)).load()[0, 0]

    return img[0] > 170 and img[1] > 170 and img[2] > 170


def trigger_to_elevate_rod_if_have_rainbow_line(threshold=0.9):
    img = ImageGrab.grab(bbox=(1187, 1019 - 1, 1217, 1030 - 1))
    screenshot = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screenshot, template_reel, cv2.TM_CCOEFF_NORMED)
    result2 = cv2.matchTemplate(screenshot, template_reel2, cv2.TM_CCOEFF_NORMED)

    _, max_val, _, _ = cv2.minMaxLoc(result)
    _, max_val2, _, _ = cv2.minMaxLoc(result2)

    return max_val >= threshold or max_val2 >= threshold


def do_choice_take_or_throw_away():
    if is_good_fish():
        press_take_fish()
    else:
        press_throw_away_fish()


class BotState(Enum):
    IDLE = auto()
    THROW = auto()
    RETRIEVE = auto()
    FIGHT = auto()
    RESULT = auto()
    RECOVER_AFTER_RESULT = auto()
    REMOTE_CONTROL = auto()
    PAUSE = auto()


class ReadyToCastDetector:
    def __init__(
            self,
            template_threshold: float = 0.75,
            uncertain_threshold: float = 0.45,
            ocr_interval: float = 0.7,
    ):
        self.template_threshold = template_threshold
        self.uncertain_threshold = uncertain_threshold
        self.ocr_interval = ocr_interval

        self.last_ocr_time = 0.0
        self.last_ocr_result = False

    def similarity(self, str1: str, str2: str) -> float:
        ratio = SequenceMatcher(None, str1, str2).ratio()
        return round(ratio * 100, 2)

    def searching_coincidence(self, text_lst: list, pat='снасть готова к забросу'):
        for st in text_lst:
            if self.similarity(st, pat) > 50:
                return True
        return False

    def recognize_the_text(self, image):
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

    @timeit
    def check(self, frame: Image.Image) -> bool:
        score = get_ready_template_score(frame, ready_template_prepared)
        score_night = get_ready_template_score(frame, ready_template_prepared_night)

        now = time.monotonic()

        # Высокая уверенность — OCR не нужен.
        if score >= self.template_threshold or score_night >= self.template_threshold:
            self.last_ocr_result = True
            return True

        # Совпадение слишком низкое — OCR тоже обычно не нужен.
        if score <= self.uncertain_threshold and score_night <= self.uncertain_threshold:
            self.last_ocr_result = False
            return False

        # Не запускаем тяжёлый OCR каждый кадр.
        if now - self.last_ocr_time < self.ocr_interval:
            return self.last_ocr_result

        self.last_ocr_time = now

        ocr_region = frame.crop(READY_BOX)

        recognized_text = self.recognize_the_text(ocr_region)

        self.last_ocr_result = (
                self.searching_coincidence(recognized_text, "снасть готова к забросу")
                or self.searching_coincidence(recognized_text, "готова к забросу")
        )

        return self.last_ocr_result


@dataclass
class BotConfig:
    retrieve_pause_interval: float
    slot_food: str
    slot_drink: str
    exit_button: str
    is_rainbow_line: bool

    retrieve_pause_duration: float = 1.8

    cast_hold_duration: float = 0.5
    cast_settle_duration: float = 0.2
    cast_flight_duration: float = 4.3

    food_interval: float = 200.0
    tick_delay: float = 0.08


class StableFlag:
    def __init__(self, required_frames: int):
        self.required_frames = required_frames
        self.frames = 0

    def update(self, value: bool) -> bool:
        self.frames = self.frames + 1 if value else 0
        return self.frames >= self.required_frames

    def reset(self):
        self.frames = 0


class InputController:
    def __init__(self):
        self.lmb = False
        self.rmb = False
        self.shift = False

    def set_lmb(self, pressed: bool):
        if pressed == self.lmb:
            return

        if pressed:
            mouse.press(button="left")
        else:
            mouse.release(button="left")

        self.lmb = pressed

    def set_rmb(self, pressed: bool):
        if pressed == self.rmb:
            return

        if pressed:
            mouse.press(button="right")
        else:
            mouse.release(button="right")

        self.rmb = pressed

    def set_shift(self, pressed: bool):
        if pressed == self.shift:
            return

        if pressed:
            keyboard.press("shift")
        else:
            keyboard.release("shift")

        self.shift = pressed

    def reset(self):
        """
        Обычный безопасный сброс.
        Отпускает только кнопки, которые были нажаты контроллером.
        """
        if self.lmb:
            mouse.release(button="left")
            self.lmb = False

        if self.rmb:
            mouse.release(button="right")
            self.rmb = False

        if self.shift:
            keyboard.release("shift")
            self.shift = False

    def force_reset(self):
        """
        Аварийный сброс — например, при завершении программы.
        """
        mouse.release(button="left")
        mouse.release(button="right")
        keyboard.release("shift")

        self.lmb = False
        self.rmb = False
        self.shift = False


class FishingBot:
    def __init__(self, config: BotConfig, command_queue=None, event_queue=None, heartbeat=None, stop_event=None):
        self.config = config
        self.command_queue = command_queue
        self.event_queue = event_queue
        self.heartbeat = heartbeat
        self.stop_event = stop_event

        self.input = InputController()

        self.state = BotState.IDLE
        self.state_started_at = time.monotonic()

        self.food_due = False
        self.next_food_at = time.monotonic() + config.food_interval

        self.next_retrieve_pause_at = (
                time.monotonic() + config.retrieve_pause_interval
        )

        self.pause_until = 0.0
        self.resume_state = BotState.RETRIEVE
        self.manual_stop = False

        # Этапы заброса
        self.throw_phase = 0
        self.throw_phase_until = 0.0

        # Обработка экрана результата
        self.result_clicked = False
        self.result_action_at = 0.0
        self.result_wait_until = 0.0

        # Защита от единичных ошибок распознавания
        self.ready_flag = StableFlag(1)
        self.fish_flag = StableFlag(2)
        self.result_flag = StableFlag(2)
        self.result_gone_flag = StableFlag(3)
        self.lift_on_flag = StableFlag(3)
        self.lift_off_flag = StableFlag(2)

        self.idle_wait_until = 0.0
        self.on_enter(self.state)

        self.ready_detector = ReadyToCastDetector(
            template_threshold=0.75,
            uncertain_threshold=0.45,
            ocr_interval=0.7,
        )
        self.recover_after_result_until = 0.0

    def reset_detectors(self):
        self.ready_flag.reset()
        self.fish_flag.reset()
        self.result_flag.reset()
        self.result_gone_flag.reset()
        self.lift_on_flag.reset()
        self.lift_off_flag.reset()

    def transition(self, new_state: BotState):
        if new_state is self.state:
            return

        old_state = self.state

        # Перед любой сменой режима гарантированно отпускаем кнопки.
        self.input.reset()

        self.state = new_state
        self.state_started_at = time.monotonic()
        self.reset_detectors()

        print(Fore.GREEN + f"{old_state.name} -> {new_state.name}")

        self.on_enter(new_state)

    def on_enter(self, state: BotState):
        now = time.monotonic()

        if state is BotState.IDLE:
            # Небольшое ожидание после закрытия окна рыбы.
            self.idle_wait_until = now + 0.35

        elif state is BotState.THROW:
            # Курсор убираем с кнопок «в садок/отпустить».
            mouse.move(960, 540, absolute=True, duration=0.05)

            self.throw_phase = 0
            self.throw_phase_until = now + self.config.cast_settle_duration

        elif state is BotState.RETRIEVE:
            self.input.set_lmb(True)

            self.next_retrieve_pause_at = (
                    now + self.config.retrieve_pause_interval
            )

        elif state is BotState.FIGHT:
            self.input.set_lmb(True)
            self.input.set_shift(True)

        elif state is BotState.RESULT:
            self.result_clicked = False
            self.result_action_at = now + 0.3

        elif state is BotState.PAUSE:
            self.input.reset()

        elif state is BotState.RECOVER_AFTER_RESULT:
            self.recover_after_result_until = now + 1.8

    def handle_idle(self, now: float):
        if now < self.idle_wait_until:
            return

        if self.food_due:
            self.feed_character()

            self.food_due = False
            self.next_food_at = now + self.config.food_interval
            self.idle_wait_until = now + 0.5
            return

        detected = self.ready_detector.check(img_grab)
        ready = self.ready_flag.update(detected)

        if ready:
            self.transition(BotState.THROW)
            return

        # Позволяет запустить бота, когда приманка уже находится в воде.
        if now - self.state_started_at >= 1.0:
            if self.fish_flag.update(is_fish_on_hook()):
                self.transition(BotState.FIGHT)
            else:
                self.transition(BotState.RETRIEVE)

    def feed_character(self):
        self.input.reset()

        if is_need_to_tea():
            keyboard.press_and_release(self.config.slot_drink)
            time.sleep(0.15)

        if is_need_to_eat():
            keyboard.press_and_release(self.config.slot_food)
            time.sleep(0.15)

    def handle_throw(self, now: float):
        if now < self.throw_phase_until:
            return

        # Этап 0: нажимаем Shift
        if self.throw_phase == 0:
            self.input.set_shift(True)

            self.throw_phase = 1
            self.throw_phase_until = now + 0.03
            return

        # Этап 1: зажимаем ЛКМ
        if self.throw_phase == 1:
            self.input.set_lmb(True)

            self.throw_phase = 2
            self.throw_phase_until = (
                    now + self.config.cast_hold_duration
            )
            return

        # Этап 2: отпускаем ЛКМ
        if self.throw_phase == 2:
            self.input.set_lmb(False)

            self.throw_phase = 3
            self.throw_phase_until = now + 0.03
            return

        # Этап 3: отпускаем Shift
        if self.throw_phase == 3:
            self.input.set_shift(False)

            self.throw_phase = 4
            self.throw_phase_until = (
                    now + self.config.cast_flight_duration
            )
            return

        # Этап 4: приманка долетела — начинаем проводку
        if self.throw_phase == 4:
            self.transition(BotState.RETRIEVE)

    def handle_retrieve(self, now: float):
        self.input.set_shift(False)
        self.input.set_rmb(False)
        self.input.set_lmb(True)

        # Поклёвка важнее паузы проводки.
        if self.fish_flag.update(is_fish_on_hook()):
            self.transition(BotState.FIGHT)
            return

        # Приманка полностью вернулась без рыбы.
        if self.ready_flag.update(self.ready_detector.check(img_grab)):
            self.transition(BotState.IDLE)
            return

        if now >= self.next_retrieve_pause_at:
            self.start_timed_pause(
                resume_state=BotState.RETRIEVE,
                duration=self.config.retrieve_pause_duration,
            )

    def start_timed_pause(self, resume_state: BotState, duration: float):
        self.resume_state = resume_state
        self.pause_until = time.monotonic() + duration
        self.manual_stop = False

        self.transition(BotState.PAUSE)

    def handle_fight(self, now: float):
        self.input.set_lmb(True)
        self.input.set_shift(True)

        # Появился экран пойманной рыбы.
        if self.result_flag.update(is_button_v_sadok_on_screen()):
            self.transition(BotState.RESULT)
            return

        # Снасть готова, но экран результата не появился.
        # Значит, рыба могла сорваться.
        if self.ready_flag.update(self.ready_detector.check(img_grab)):
            self.transition(BotState.IDLE)
            return

        if self.config.is_rainbow_line:
            lift_trigger = (
                trigger_to_elevate_rod_if_have_rainbow_line()
            )
        else:
            lift_trigger = (
                trigger_to_elevate_rod_if_not_rainbow_line()
            )

        # Нажимаем ПКМ только после нескольких подтверждений.
        if self.lift_on_flag.update(lift_trigger):
            self.input.set_rmb(True)
            self.lift_off_flag.reset()

        # Отпускаем ПКМ тоже не по одному случайному кадру.
        if self.lift_off_flag.update(not lift_trigger):
            self.input.set_rmb(False)
            self.lift_on_flag.reset()

    def handle_result(self, now: float):
        self.input.reset()

        if not self.result_clicked:
            if now < self.result_action_at:
                return

            do_choice_take_or_throw_away()

            self.result_clicked = True
            self.result_wait_until = now + 0.4
            return

        if now < self.result_wait_until:
            return

        result_is_gone = not is_button_v_sadok_on_screen()

        if self.result_gone_flag.update(result_is_gone):
            # Убираем курсор с области кнопок результата.
            mouse.move(960, 540, absolute=True, duration=0.05)

            self.transition(BotState.RECOVER_AFTER_RESULT)

    def handle_pause(self, now: float):
        self.input.reset()

        if self.manual_stop:
            return

        if now >= self.pause_until:
            self.transition(self.resume_state)

    def handle_recover_after_result(self, now: float):
        # В этом состоянии ничего не нажимаем.
        self.input.reset()

        detected = self.ready_detector.check(img_grab)
        ready = self.ready_flag.update(detected)

        if ready:
            self.transition(BotState.THROW)
            return

        if now >= self.recover_after_result_until:
            self.transition(BotState.RETRIEVE)

    def process_remote_commands(self):
        if self.command_queue is None:
            return

        while True:
            try:
                command = self.command_queue.get_nowait()
            except queue.Empty:
                break

            command_type = command.get("type")

            if command_type == "pause":
                self.manual_stop = True
                self.transition(BotState.PAUSE)

            elif command_type == "resume":
                self.manual_stop = False
                self.transition(BotState.IDLE)

            elif command_type == "move":
                self.execute_move_command(command)

            elif command_type == "click":
                self.execute_click_command(command)

            elif command_type == "click_text":
                self.execute_click_text_command(command)

            elif command_type == "shutdown_worker":
                self.input.force_reset()

                raise SystemExit

            elif command_type == "shutdown":
                self.input.force_reset()

                if self.stop_event is not None:
                    self.stop_event.set()

                return

    def execute_click_text_command(self, command: dict):
        target = str(command["text"]).strip()

        if not target:
            self.send_event("error", "Не передан текст")
            return

        if not is_game_active():
            self.send_event(
                "error",
                "Игра не активна. Поиск отменён.",
            )
            return

        self.begin_remote_control()

        try:
            frame = ImageGrab.grab()
            match = find_text_on_screen(frame, target)

            if match is None:
                self.send_event(
                    "text_not_found",
                    f'Текст "{target}" не найден',
                )
                return

            left, top, right, bottom = match["box"]

            x = (left + right) // 2
            y = (top + bottom) // 2

            mouse.move(
                x,
                y,
                absolute=True,
                duration=0.15,
            )

            time.sleep(0.15)
            mouse.click(button="left")

            self.send_event(
                "command_completed",
                (
                    f'Нажато "{match["text"]}" '
                    f"в ({x}, {y}), "
                    f'сходство {match["similarity"]:.2f}'
                ),
            )

        finally:
            self.finish_remote_control()

    def execute_move_command(self, command: dict):
        direction = str(command.get("direction", "")).lower()
        steps = int(command.get("steps", 1))

        steps = max(1, min(steps, 50))

        key = DIRECTION_KEYS.get(direction)

        if key is None:
            self.send_event(
                "error",
                f"Неизвестное направление: {direction}",
            )
            return

        if not is_game_active():
            self.send_event(
                "error",
                "Окно игры не активно. Перемещение отменено.",
            )
            return

        self.begin_remote_control()

        try:
            for _ in range(steps):
                keyboard.press(key)
                time.sleep(0.18)
                keyboard.release(key)
                time.sleep(0.05)

            self.send_event(
                "command_completed",
                f"Выполнено: {direction}, шагов: {steps}",
            )

        finally:
            keyboard.release(key)
            self.finish_remote_control()

    def execute_click_command(self, command: dict):
        x = int(command["x"])
        y = int(command["y"])
        button = command.get("button", "left")

        screen_width, screen_height = ImageGrab.grab().size

        if not 0 <= x < screen_width:
            self.send_event("error", "X находится за экраном")
            return

        if not 0 <= y < screen_height:
            self.send_event("error", "Y находится за экраном")
            return

        if button not in {"left", "right", "middle"}:
            self.send_event("error", "Неизвестная кнопка мыши")
            return

        if not is_game_active():
            self.send_event(
                "error",
                "Игра не активна. Клик отменён.",
            )
            return

        self.begin_remote_control()

        try:
            mouse.move(
                x,
                y,
                absolute=True,
                duration=0.15,
            )

            time.sleep(0.1)
            mouse.click(button=button)

            self.send_event(
                "command_completed",
                f"Клик {button}: ({x}, {y})",
            )

        finally:
            self.finish_remote_control()

    def send_event(self, event_type: str, message: str, **extra):
        if self.event_queue is None:
            return

        self.event_queue.put({
            "type": event_type,
            "message": message,
            "state": self.state.name,
            "created_at": time.time(),
            **extra,
        })

    def begin_remote_control(self):
        self.input.force_reset()

        self.state = BotState.REMOTE_CONTROL
        self.state_started_at = time.monotonic()

    def finish_remote_control(self):
        self.input.force_reset()

        # После перемещения персонажа невозможно знать,
        # находится ли приманка в воде.
        self.transition(BotState.IDLE)

    def state_duration(self) -> float:
        return time.monotonic() - self.state_started_at

    def tick(self) -> bool:
        global img_grab

        now = time.monotonic()

        if self.heartbeat is not None:
            with self.heartbeat.get_lock():
                self.heartbeat.value = time.time()

        # Один общий кадр на итерацию.
        img_grab = ImageGrab.grab()

        self.process_remote_commands()

        if keyboard.is_pressed(self.config.exit_button):
            print("Получена команда остановки")

            self.input.force_reset()

            if self.stop_event is not None:
                self.stop_event.set()

            return False

        if now >= self.next_food_at:
            self.food_due = True

        # noinspection PyUnreachableCode
        if self.state is BotState.IDLE:
            self.handle_idle(now)

        elif self.state is BotState.THROW:
            self.handle_throw(now)

        elif self.state is BotState.RETRIEVE:
            self.handle_retrieve(now)

        elif self.state is BotState.FIGHT:
            self.handle_fight(now)

        elif self.state is BotState.RESULT:
            self.handle_result(now)

        elif self.state is BotState.PAUSE:
            self.handle_pause(now)

        elif self.state is BotState.RECOVER_AFTER_RESULT:
            self.handle_recover_after_result(now)

        return True

    def run(self):
        print(Fore.RED + "НАЧАЛО РАБОТЫ")

        try:
            while self.tick():
                time.sleep(self.config.tick_delay)
        finally:
            self.input.force_reset()
            print(Fore.RED + "БОТ ОСТАНОВЛЕН")


def fishing_worker_main(
        command_queue,
        event_queue,
        heartbeat,
        stop_event,
        config: BotConfig,
):
    if not config:
        config = BotConfig(
            retrieve_pause_interval=5,
            slot_food="5",
            slot_drink="4",
            exit_button="9",
            is_rainbow_line=True,
        )

    bot = FishingBot(
        config=config,
        command_queue=command_queue,
        event_queue=event_queue,
        heartbeat=heartbeat,
        stop_event=stop_event,
    )

    bot.run()


class FishingSupervisor:
    def __init__(self, config: BotConfig, stop_event):
        self.config = config
        self.stop_event = stop_event

        self.command_queue = mp.Queue()
        self.event_queue = mp.Queue()
        self.heartbeat = mp.Value("d", time.time())

        self.worker_process = None

    def start_worker(self):
        if self.worker_process is not None and self.worker_process.is_alive():
            return

        with self.heartbeat.get_lock():
            self.heartbeat.value = time.time()

        self.worker_process = mp.Process(
            target=fishing_worker_main,
            args=(
                self.command_queue,
                self.event_queue,
                self.heartbeat,
                self.stop_event,
                self.config
            ),
            daemon=True,
            name="FishingWorker",
        )

        self.worker_process.start()

    def stop_worker(self):
        process = self.worker_process

        if process is None:
            return

        if process.is_alive():
            self.command_queue.put({
                "type": "shutdown_worker",
            })

            process.join(timeout=3)

        if process.is_alive():
            process.terminate()
            process.join(timeout=2)

        if process.is_alive():
            process.kill()
            process.join(timeout=1)

        self.worker_process = None

    def restart_worker(self):
        self.stop_worker()

        self.command_queue = mp.Queue()

        self.start_worker()


async def wait_for_stop_event(stop_event):
    while not stop_event.is_set():
        await asyncio.sleep(0.2)


async def main_app(config: BotConfig = None, stop_event=None):
    import telegramBot

    FishDataBase.initialize_database()

    supervisor = FishingSupervisor(config=config, stop_event=stop_event)
    bot, dispatcher = telegramBot.run_telegram_bot(supervisor)
    supervisor.start_worker()

    # Проверяем и удаляем старый webhook
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        await bot.delete_webhook(drop_pending_updates=True)

    await bot.delete_webhook(
        drop_pending_updates=True,
    )

    supervisor.start_worker()

    polling_task = asyncio.create_task(
        dispatcher.start_polling(
            bot,
            handle_signals=False,
            allowed_updates=(
                dispatcher.resolve_used_update_types()
            ),
        )
    )

    stop_task = asyncio.create_task(
        wait_for_stop_event(stop_event)
    )

    try:
        done, pending = await asyncio.wait(
            {
                polling_task,
                stop_task,
            },
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        await asyncio.gather(
            *pending,
            return_exceptions=True,
        )

    finally:
        print("Останавливаю всё приложение")

        if not polling_task.done():
            polling_task.cancel()

        await asyncio.gather(
            polling_task,
            return_exceptions=True,
        )

        await asyncio.to_thread(
            supervisor.stop_worker
        )

        await bot.session.close()


if __name__ == "__main__":
    mp.freeze_support()
    asyncio.run(main_app(config=None))
