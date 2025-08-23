from PyQt5.QtWidgets import QMainWindow, QApplication
from interface import Ui_MainWindow
import sys
from spinning import func1
import time


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.play.clicked.connect(self.run)

    def run(self):
        time.sleep(2)
        default = [80, '5', '4', '9']
        pause, food, food2, key = self.pause.text(), self.food.text(), self.food2.text(), self.lineEdit.text()
        lst = [pause, food, food2, key]
        for i in range(len(lst)):
            if not lst[i]:
                lst[i] = default[i]

        func1(int(lst[0]), lst[3], lst[1], lst[2])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
