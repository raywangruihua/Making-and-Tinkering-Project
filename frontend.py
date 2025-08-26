from backend import Autoscope
from PySide6.QtWidgets import (
    QApplication, QLabel, QDialog,
    QPushButton, QVBoxLayout, QWidget,
    QStackedWidget
)
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt

class MainWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.stacked_widget = QStackedWidget()

        self.main_menu = MainMenu()
        self.auto_menu = AutoMenu()
        self.manual_menu = ManualMenu()

        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.auto_menu)
        self.stacked_widget.addWidget(self.manual_menu)

    def start_autoscope(self):
        self.autoscope = Autoscope()
        self.autoscope.initialise()

    def stop_autoscope(self):
        self.autoscope.deinitialise()


class MainMenu(QWidget):
    navigate = Signal(str)
    def __init__(self):
        self.setWindowTitle("Main Menu")

        layout_main_menu = QVBoxLayout()

        self.label = QLabel("Main Menu")
        self.button_auto_menu = QPushButton("Auto")
        self.button_manual_menu = QPushButton("Manual")
        self.button_exit_app = QPushButton("Exit")

        self.button_auto_menu.clicked.connect(lambda: self.navigate.emit("auto"))
        self.button_manual_menu.clicked.connect(lambda: self.navigate.emit("manual"))
        self.button_exit_app.clicked.connect(lambda: self.navigate.emit("exit"))

        layout_main_menu.addWidget(self.label)
        layout_main_menu.addWidget(self.button_auto_menu)
        layout_main_menu.addWidget(self.button_manual_menu)
        layout_main_menu.addWidget(self.button_exit_app)


class AutoMenu(QWidget):
    def __init__(self, autoscope: Autoscope, parent=None):
        super(AutoMenu, self).__init__(parent)
        self.autoscope = autoscope

        self.setWindowTitle("Auto Mode")
        self.setGeometry(100, 100, 400, 200)

        self.stacked_widget = QStackedWidget()

        self.widget_start = QWidget()
        self.widget_query_zoom = QWidget()
        self.widget_working = QWidget()
        self.widget_upload = QWidget()
        self.widget_choose_


        self.label_start = self.QLabel("Press start to begin.")

        self.button_start = QPushButton("Start")

        self.layout_start = QVBoxLayout(self.widget_start)
        self.layout_start.addWidget(self.label_start)
        self.layout_start.addWidget(self.button_start)
        self.setLayout(self.layout_start)

        self.button_start.clicked.connect(self.start())

    def start(self):
        self.stacked_widget.setCurrentIndex(0)
        self.query_zoom()

    def query_zoom(self):

   
class ManualMenu(QWidget):
    def __init__(self, autoscope: Autoscope, parent=None):
        super(ManualMenu, self).__init__(parent)
        self.autoscope = autoscope

        self.setWindowTitle("Manual Mode")
        self.resize(800, 600)
        self.label = QLabel("Autoscope Manual Mode.\n" \
        "Use WASD for movement.\n" \
        "Use I and O keys to zoom in and out of the image.\n" \
        "Press Escape to quit manual mode.")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_W:
            self.autoscope.smart_move_y(1, "-")
        elif event.key() == Qt.Key_S:
            self.autoscope.smart_move_y(1, "+")
        elif event.key() == Qt.Key_A:
            self.autoscope.smart_move_x(1, "-")
        elif event.key() == Qt.Key_D:
            self.autoscope.smart_move_x(1, "+")
        elif event.key() == Qt.Key_I:
            self.autoscope.smart_move_z(1, "+")
        elif event.key() == Qt.Key_O:
            self.autoscope.smart_move_z(1, "-")
        elif event.key() == Qt.Key_Escape:
            self.close()
