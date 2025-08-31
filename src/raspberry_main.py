import sys
from frontend import MainMenu
from PySide6.QtWidgets import QApplication


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_menu = MainMenu()
    main_menu.start_autoscope()
    main_menu.show()

    sys.exit(app.exec())