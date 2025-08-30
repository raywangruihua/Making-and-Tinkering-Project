from backend import Autoscope
from PySide6.QtWidgets import (
    QLabel, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget, QLineEdit
)
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.autoscope = None
        self.manual_menu = None
        self.auto_menu = None
        self.setWindowTitle("Main Menu")
        self.resize(400, 200)

        layout_main_menu = QVBoxLayout()

        self.label = QLabel("Main Menu")
        self.button_auto_menu = QPushButton("Auto")
        self.button_manual_menu = QPushButton("Manual")
        self.button_exit_app = QPushButton("Exit")

        layout_main_menu.addWidget(self.label)
        layout_main_menu.addWidget(self.button_auto_menu)
        layout_main_menu.addWidget(self.button_manual_menu)
        layout_main_menu.addWidget(self.button_exit_app)

        self.button_auto_menu.clicked.connect(self.create_auto_menu)
        self.button_manual_menu.clicked.connect(self.create_manual_menu)
        self.button_exit_app.clicked.connect(self.exit_app)

        self.setLayout(layout_main_menu)

    def start_autoscope(self):
        self.autoscope = Autoscope()
        self.autoscope.initialise()

    def stop_autoscope(self):
        self.autoscope.deinitialise()

    def create_auto_menu(self):
        self.auto_menu = AutoWindow(self.autoscope)
        self.auto_menu.stacked_widget.show()

    def create_manual_menu(self):
        self.manual_menu = ManualWindow(self.autoscope)
        self.manual_menu.show()

    def exit_app(self):
        self.close()


class AutoWindow(QWidget):
    def __init__(self, autoscope: Autoscope):
        super().__init__()
        self.autoscope = autoscope

        self.setWindowTitle("Auto Window")
        self.resize(400, 200)

        self.stacked_widget = QStackedWidget()
        
        # auto window start page
        self.start_page = QWidget()
        self.layout_start_page = QVBoxLayout(self.start_page)

        self.start_button = QPushButton("Click to begin.")
        self.start_button.clicked.connect(self.go_to_query_page)

        self.layout_start_page.addWidget(self.start_button)

        # auto window query page
        self.query_page = QWidget()
        self.layout_query_page = QVBoxLayout(self.query_page)

        self.query_error = QLabel()
        self.query_label = QLabel("Enter starting zoom (4x, 10x, 40x):")
        self.zoom_query = QLineEdit()
        self.zoom_query.returnPressed.connect(self.get_zoom_query)

        self.layout_query_page.addWidget(self.query_error)
        self.layout_query_page.addWidget(self.query_label)
        self.layout_query_page.addWidget(self.zoom_query)

        # auto window working page
        self.working_page = QWidget()
        self.layout_working_page = QVBoxLayout(self.working_page)

        self.working_label = QLabel("Autoscope working...")

        self.layout_working_page.addWidget(self.working_label)

        # auto window choosing next step page
        self.choice_page = QWidget()
        self.layout_choice_page = QVBoxLayout(self.choice_page)

        self.choice_save_image = QPushButton("Save image")
        self.choice_collect_data = QPushButton("Collect data")
        self.choice_close = QPushButton("Close automatic mode")

        self.choice_save_image.clicked.connect(self.save_image)
        self.choice_collect_data.clicked.connect(self.collect_data)
        self.choice_close.clicked.connect(self.stacked_widget.close)

        self.layout_choice_page.addWidget(self.choice_save_image)
        self.layout_choice_page.addWidget(self.choice_collect_data)
        self.layout_choice_page.addWidget(self.choice_close)

        # index pages
        self.start_page_index = self.stacked_widget.addWidget(self.start_page)
        self.query_page_index = self.stacked_widget.addWidget(self.query_page)
        self.working_page_index = self.stacked_widget.addWidget(self.working_page)
        self.choice_page_index = self.stacked_widget.addWidget(self.choice_page)

        self.stacked_widget.setCurrentIndex(self.start_page_index)

    def go_to_query_page(self):
        self.stacked_widget.setCurrentIndex(self.query_page_index)

    def get_zoom_query(self):
        starting_zoom = self.zoom_query.text()
        valid_zoom = ["4x", "10x", "40x"]
        if starting_zoom in valid_zoom:
            self.workflow(starting_zoom)
        else:
            self.query_error.setText("Invalid zoom entered.")

    def workflow(self, starting_zoom):
        self.stacked_widget.setCurrentIndex(self.working_page_index)
        self.autoscope.set_exposure(starting_zoom)
        self.autoscope.focus()
        self.autoscope.identify_median_area()
        self.autoscope.next_lens()
        self.stacked_widget.setCurrentIndex(self.choice_page_index)

    def save_image(self):
        self.autoscope.

    def collect_data(self):
        self.autoscope.collect_data()


class ManualWindow(QWidget):
    def __init__(self, autoscope: Autoscope):
        super().__init__()
        self.autoscope = autoscope

        self.setWindowTitle("Manual Mode")
        self.resize(400, 200)

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