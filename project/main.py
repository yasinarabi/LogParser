import os

from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from window import main_window

APP_PATH = os.path.join(os.getenv("HOME"), ".log_parser")

if __name__ == "__main__":
    if not os.path.exists(APP_PATH):
        os.mkdir(APP_PATH)
    app = QApplication([])
    window = main_window.Window()
    app.exec()

# sys.exit(app.exec())
