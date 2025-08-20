import serial, time, os, cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

X4_EXPOSURE_TIME = 100_000
X10_EXPOSURE_TIME = 500_000
X40_EXPOSURE_TIME = 1_500_000
TOP_LIMIT = 35
BOTTOM_LIMIT = 50
FOCUS_PATH = "./TEMP/FOCUS.jpg"
TEMP_FOLDER_PATH = "./TEMP"
DATA_FOLDER_PATH = "./DATA"

class Arduino():
    def __init__(self):
        self.__device = None
        self.__initialised = False

    def initialise(self, port):
        self.__device = serial.Serial(port, 9600, timeout=1)
        self.__device.reset_input_buffer()
        self.__initialised = True
    
    def check_initialisation(self):
        return self.__initialised

    def move_motor(self, motor, direction):
        if self.check_initialisation:
            response = "Not done"
            while response != "Done":
                instruction = f"{motor} {direction}\n"
                self.__device.write(instruction.encode("utf-8"))
                time.sleep(1)
                response = self.__device.readline().decode("utf-8").rstrip()
        else:
            print("Arduino not initialised.")
    
    def move_x(self, steps, direction):
        if self.check_initialisation:
            for i in range(steps):
                self.move_motor("x", direction)
        else:
            print("Arduino not initialised.")

    def move_y(self, steps, direction):
        if self.check_initialisation:
            for i in range(steps):
                self.move_motor("y", direction)
        else:
            print("Arduino not initialised.")

    def move_z(self, direction):
        self.move_motor("z", direction)

class Camera():
    def __init__(self):
        self.__device = None
        self.__initialised = False

    def initalise(self):
        self.__device = Picamera2()

        configuration = self.__device.create_still_configuration(
            buffer_count = 1,
            main = {"size": (1280, 970)}
        )
        self.__device.configure(configuration)

        self.__device.set_controls({
            "AeEnable": False,
            "ExposureTime": X4_EXPOSURE_TIME,
            "AnalogueGain": 1.0,
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": 2.0
        })

        self.__initialised = True

    def check_intialisation(self):
        return self.__initialised

    def start(self):
        if self.check_intialisation:
            self.__device.start()
        else:
            print("Camera not initialised.")

    def stop(self):
        if self.check_intialisation:
            self.__device.stop()
        else:
            print("Camera not initialised.")

    def capture(self, filepath):
        if self.check_intialisation:
            self.__device.capture_file(filepath)
        else:
            print("Camera not initialised.")

    def set_exposure(self, zoom):
        if zoom == "4x":
            self.__device.set_controls(X4_EXPOSURE_TIME)
        elif zoom == "10x":
            self.__device.set_controls(X10_EXPOSURE_TIME)
        else:
            self.__device.set_controls(X40_EXPOSURE_TIME)
        
        print("Setting Exposure.")
        time.sleep(10)

class Autoscope():
    def __init__(self):
        self.__arduino = Arduino()
        self.__camera = Camera()
        self.__current_zoom = ""
        self.__x_position = 0
        self.__y_position = 0
        self.__z_position = 0
        self.__median_area = 0
        # whether or not we have zoomed and focused to the max
        self.__status = False

    def get_current_zoom(self):
        return self.__current_zoom
    
    def get_x_position(self):
        return self.__x_position
    
    def get_y_position(self):
        return self.__y_position
    
    def get_z_position(self):
        return self.__z_position
    
    def set_current_zoom(self, zoom):
        self.__current_zoom = zoom

    def set_x_position(self, x):
        self.__x_position = x

    def set_y_position(self, y):
        self.__y_position = y

    def set_z_position(self, z):
        self.__z_position = z

    def initialise(self, arduino_port):
        self.initialise_arduino(arduino_port)
        self.initalise_camera()

        try:
            os.mkdir(TEMP_FOLDER_PATH)
            os.mkdir(DATA_FOLDER_PATH)
        except FileExistsError:
            pass

    def initialise_arduino(self, port):
        self.__arduino.initialise(port)

    def initalise_camera(self):
        self.__camera.initalise()

    def start_camera(self):
        self.__camera.start()

    def capture_image(self, filepath):
        self.__camera.capture(filepath)

    def stop_camera(self):
        self.__camera.stop()

    def set_exposure_time(self):
        self.__camera.set_exposure(self.get_current_zoom())

    # Tenengrad method
    def calculate_sharpness(self):
        image = cv2.imread(FOCUS_PATH)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_sq = gx**2 + gy**2
        
        return np.sum(grad_sq)
    
    def move_x(self, steps, direction):
        self.__arduino.move_x(steps, direction)

    def move_y(self, steps, direction):
        self.__arduino.move_y(steps, direction)

    def move_z(self, steps, direction):
        if direction == "+":
            for i in range(steps):
                self.__arduino.move_z(direction)
                self.increment_position()
        else:
            for i in range(steps):
                self.__arduino.move_z(direction)
                self.decrement_position()

    def check_status(self):
        return self.__status

    def get_position(self):
        return self.__z_position

    def increment_position(self):
        self.__z_position += 1
    
    def decrement_position(self):
        self.__z_position -= 1

    def focus_4x_10x(self):
        self.capture_image(FOCUS_PATH)
        current_sharpness = self.calculate_sharpness()
        best = [self.get_position, current_sharpness]
        print(f"{best[0]}: {best[1]}")

        while self.get_position() < BOTTOM_LIMIT:
            self.move_z(1, "+")
            self.capture_image(FOCUS_PATH)
            current_sharpness = self.calculate_sharpness()
            print(f"{best[0]}: {best[1]}")
            if current_sharpness > best[1]:
                best = [self.get_position, current_sharpness]

        return_steps = self.get_position - best[0]
        self.move_z(return_steps, "-")
        self.capture_image(FOCUS_PATH)
        print(f"{self.get_position}: {self.calculate_sharpness()}")

    def focus_40x(self):
        self.capture_image(FOCUS_PATH)
        current_sharpness = self.calculate_sharpness()
        best = [self.get_position, current_sharpness]
        print(f"{best[0]}: {best[1]}")

        while self.get_position > TOP_LIMIT:
            self.move_z(1, "-")
            self.capture_image(FOCUS_PATH)
            current_sharpness = self.calculate_sharpness()
            print(f"{best[0]}: {best[1]}")
            if current_sharpness > best[1]:
                best = [self.get_position, current_sharpness]
        
        return_steps = best[0] - self.get_position()
        self.move_z(return_steps, "+")
        self.capture_image(FOCUS_PATH)
        print(f"{self.get_position}: {self.calculate_sharpness()}")

    def focus(self):
        if self.check_status():
            return
        
        if self.get_current_zoom in ["4x", "10x"]:
            self.focus_4x_10x()
        else:
            self.focus_40x()

    def take_picture_of_sample(self):

    def count_cells(self):

    def identify_median_area(self):
        self.take_picture_of_sample()
        cell_counts = self.count_cells()

        sorted_cell_counts = sorted(cell_counts, key=lambda cell_count: cell_count[1])
        median = sorted_cell_counts[4][0]

        return median
    
    def get_median_area(self):
        return self.__median_area

    def move_median_area(self):
        median_area = self.get_median_area()
        if median_area == 0:
            print("Median area not found.")
        elif median_area == 1:
            move_x(16, "+")
            move_y(3, "-")
        elif median_area == 2:
            move_y(3, "-")
        elif median_area == 3:
            move_x(16, "-")
            move_y(3, "-")
        elif median_area == 4:
            move_x(16, "+")
        elif median_area == 5:
            return
        elif median_area == 6:
            move_x(16, "-")
        elif median_area == 7:
            move_x(16, "+")
            move_y(3, "+")
        elif median_area == 8:
            move_y(3, "+")
        elif median_area == 9:
            move_x(16, "-")
            move_y(3, "+")

def main():
    autoscope = Autoscope()

    arduino_port = "/dev/ttyUSB0"
    autoscope.initialise(arduino_port)

    starting_zoom = query_starting_zoom()
    autoscope.set_current_zoom(starting_zoom)
    autoscope.set_exposure_time()
    autoscope.start_camera()

    autoscope.focus()
    autoscope.identify_median_area()
    autoscope.move_median_area()

    return 0

def query_starting_zoom():
    starting_zoom = ""
    valid_zoom = ["4x", "10x"]

    while not(starting_zoom in valid_zoom):
        starting_zoom = input("Enter starting zoom level (4x, 10x): ")
    
    return starting_zoom
