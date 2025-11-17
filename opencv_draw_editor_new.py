"""
OpenCV HUD Editor - головний файл додатку

Редактор для створення оверлеїв HUD з експортом у OpenCV код
"""
import sys
from PyQt5 import QtWidgets

from main_window import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.setFocus()  # Явно встановлюємо фокус на вікно
    win.activateWindow()  # Активуємо вікно
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

