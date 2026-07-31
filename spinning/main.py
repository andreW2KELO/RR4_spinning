from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QValidator
from interface import Ui_MainWindow
import sys
from NewOOPSpinning import main
import threading
import time


class YesNoValidator(QValidator):
    def __init__(self, parent=None, case_sensitive=False):
        super(YesNoValidator, self).__init__(parent)
        self.case_sensitive = case_sensitive

    def validate(self, s, pos):
        text = s.strip()
        if not self.case_sensitive:
            text = text.lower()

        if text == "":
            return QValidator.Intermediate, s, pos

        valid_words = ["да", "нет"] if not self.case_sensitive else ["да", "нет"]
        if text in valid_words:
            return QValidator.Acceptable, s, pos
        if any(w.startswith(text) for w in valid_words):
            return QValidator.Intermediate, s, pos

        return QValidator.Invalid, s, pos


class OptionalIntValidator(QValidator):
    def __init__(self, minimum, maximum, parent=None):
        super().__init__(parent)
        self.min = minimum
        self.max = maximum

    def validate(self, s: str, pos: int):
        if s.strip() == "":
            # Пустая строка допустима
            return QValidator.Acceptable, s, pos

        if not s.isdigit():
            return QValidator.Invalid, s, pos

        val = int(s)
        if self.min <= val <= self.max:
            return QValidator.Acceptable, s, pos

        if val < self.min and len(s) < len(str(self.max)):
            return QValidator.Intermediate, s, pos

        return QValidator.Invalid, s, pos


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # self.pause.setValidator(OptionalIntValidator(1, 100, self))
        self.slot_food.setValidator(OptionalIntValidator(4, 7, self))
        self.slot_drink.setValidator(OptionalIntValidator(4, 7, self))
        self.is_rainbow_line.setValidator(YesNoValidator(self.is_rainbow_line))

        self.play.clicked.connect(self.run)

    def update_state(self):
        # hasAcceptableInput учитывает validator и inputMask
        fields = (self.n_tips, self.throw_power)
        all_ok = all(le.hasAcceptableInput() for le in fields)

        # Подсветка неверных полей
        for le in fields:
            bad = (le.text() != "") and (not le.hasAcceptableInput())
            le.setStyleSheet("" if not bad else "border:1px solid #e00;")

        self.play.setEnabled(all_ok)

    def run(self):

        pause = self.pause.text() if self.pause.text() else 5
        slot_food = self.slot_food.text() if self.slot_food.text() else '5'
        slot_drink = self.slot_drink.text() if self.slot_drink.text() else '4'
        exit_button = self.exit_button.text() if self.exit_button.text() else '9'
        is_rainbow_line = self.is_rainbow_line.text() if self.is_rainbow_line.text() else 'нет'

        main(pause, slot_food, slot_drink, exit_button, is_rainbow_line)


if __name__ == '__main__':
    # t = threading.Thread(target=run_bot_thread, daemon=True)
    # t.start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
