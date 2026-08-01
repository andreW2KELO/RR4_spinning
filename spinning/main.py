from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QValidator
from PyQt5.QtCore import QTimer
from interface import Ui_MainWindow
import sys
from NewOOPSpinning import main_app, BotConfig
import multiprocessing as mp
import asyncio


def convert_into_boolean(st: str):
    if st.lower() in ["true", "да", "yes"]:
        return True
    return False


def run_bot_process(
        config: BotConfig,
        stop_event,
):
    asyncio.run(
        main_app(
            config=config,
            stop_event=stop_event,
        )
    )


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

        valid_words = ["да", "нет", 'no', 'yes', 'false', 'true'] if not self.case_sensitive else ["да", "нет"]
        if text in valid_words:
            return QValidator.Acceptable, s, pos
        if any(w.startswith(text) for w in valid_words):
            return QValidator.Intermediate, s, pos

        return QValidator.Invalid, s, pos


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.is_rainbow_line.setValidator(YesNoValidator(self.is_rainbow_line))

        self.bot_process = None
        self.stop_event = None

        self.play.clicked.connect(self.run)

        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(
            self.check_bot_process
        )
        self.process_timer.start(300)

    def check_bot_process(self):
        if self.bot_process is None:
            self.play.setEnabled(True)
            return

        if self.bot_process.is_alive():
            return

        self.bot_process.join(timeout=0.1)
        self.bot_process = None
        self.stop_event = None

        self.play.setEnabled(True)

        print(
            "Бот остановлен. "
            "Можно изменить настройки и запустить заново"
        )

    def update_state(self):
        fields = (self.n_tips, self.throw_power)
        all_ok = all(le.hasAcceptableInput() for le in fields)

        # Подсветка неверных полей
        for le in fields:
            bad = (le.text() != "") and (not le.hasAcceptableInput())
            le.setStyleSheet("" if not bad else "border:1px solid #e00;")

        self.play.setEnabled(all_ok)

    def run(self):
        if self.bot_process and self.bot_process.is_alive():
            return

        config = BotConfig(
            retrieve_pause_interval=float(
                self.pause.text() or 5
            ),
            slot_food=self.slot_food.text() or "5",
            slot_drink=self.slot_drink.text() or "4",
            exit_button=self.exit_button.text() or "9",
            is_rainbow_line=convert_into_boolean(
                self.is_rainbow_line.text() or "нет"
            ),
        )

        self.stop_event = mp.Event()

        self.bot_process = mp.Process(
            target=run_bot_process,
            args=(
                config,
                self.stop_event,
            ),
        )

        self.bot_process.start()
        self.play.setEnabled(False)

    def stop_bot(self):
        if self.bot_process and self.bot_process.is_alive():
            self.bot_process.terminate()
            self.bot_process.join(timeout=3)

        self.bot_process = None
        self.play.setEnabled(True)

    def closeEvent(self, event):
        self.stop_bot()
        event.accept()


if __name__ == '__main__':
    mp.freeze_support()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
