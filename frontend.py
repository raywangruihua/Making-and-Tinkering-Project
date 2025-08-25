from backend import Autoscope
from PySide6.QtWidgets import (QLabel, QPushButton, QApplication, QVBoxLayout, QDialog)
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt

class MainMenu(QDialog):
    def __init__(self, parent=None):
        super(MainMenu, self).__init__(parent)

        self.autoscope = None

        self.label = QLabel("Autoscope")
        self.button_auto_mode = QPushButton("Auto")
        self.button_manual_mode = QPushButton("Manual")
        self.button_exit_app = QPushButton("Exit")

        layout = QVBoxLayout()
        layout.addWidget(self.button_auto_mode)
        layout.addWidget(self.button_manual_mode)
        self.addWdiget(self.button_exit_app)
        self.setLayout(layout)

        self.button_auto_mode.clicked.connect(self.auto_mode)
        self.button_manual_mode.clicked.connect(self.manual)
        self.button_exit_app.clicked.connect(self.exit_app)

    def start_autoscope(self):
        self.autoscope = Autoscope()
        self.autoscope.initialise()

    def auto_mode(self):
        self.close()
        auto_menu = AutoMenu(self.autoscope)
        auto_menu.show()

    def manual_mode(self):
        self.close()
        manual_menu = ManualMenu(self.autoscope)
        manual_menu.show()

    def exit_app(self):
        self.close()

class AutoMenu(QDialog):
    def __init__(self, autoscope: Autoscope, parent=None):
        super(AutoMenu, self).__init__(parent)
        self.autoscope = autoscope

class ManualMenu(QDialog):
    def __init__(self, autoscope: Autoscope, parent=None):
        super(ManualMenu, self).__init__(parent)
        self.autoscope = autoscope

        self.label = QLabel("Autoscope Manual Mode")
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_W:
            self.autoscope.smart_move_y(1, "-")
        elif event.key() == Qt.Key_S:
            self.autoscope.smart_move_y(1, "+")
        elif event.key() == Qt.Key_A:
            self.autoscope.smart_move_x(1, "-")
        elif event.key() == Qt.Key_D:
            self.autoscope.smart_move_x(1, "+")
        elif event.key() == Qt.Key_O:
            self.autoscope.smart_move_z(1, "+")
        elif event.key() == Qt.Key_I:
            self.autoscope.smart_move_z(1, "-")
