from PyQt5.QtWidgets import QMainWindow, QApplication
from interface import Ui_MainWindow
import sys
from bottom import main, run_bot_thread
import threading
import time


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.play.clicked.connect(self.run)

    def run(self):
        time.sleep(2)

        min_dx = self.min_dx.text() if self.min_dx.text() else '50'
        slot_food = self.slot_food.text() if self.slot_food.text() else '5'
        slot_drink = self.slot_drink.text() if self.slot_drink.text() else '4'
        n_tips = self.n_tips.text() if self.n_tips.text() else '3'
        exit_button = self.exit_button.text() if self.exit_button.text() else '9'
        throw_power = self.throw_power.text() if self.throw_power.text() else '57'
        is_rainbow_line = self.is_rainbow_line.text() if self.is_rainbow_line.text() else 'нет'

        main(min_dx, slot_food, slot_drink, n_tips, exit_button, throw_power, is_rainbow_line)


if __name__ == '__main__':
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
