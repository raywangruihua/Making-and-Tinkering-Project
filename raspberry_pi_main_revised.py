import serial, time, os, cv2
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
from tqdm import tqdm
from pyrdrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# tweak constants here to suit Autoscope and environment (exposure)
# input drive folder ids before running count_cells method in Autoscope
X4_EXPOSURE_TIME = 100_000
X10_EXPOSURE_TIME = 500_000
X40_EXPOSURE_TIME = 3_000_000
TOP_LIMIT = 35
BOTTOM_LIMIT = 50
TEMP_FOLDER_PATH = "./TEMP"
DATA_FOLDER_PATH = "./DATA"
FOCUS_PATH = "./TEMP/FOCUS.jpg"
SQUARE_GRID_PICTURES_PATHS = ["",
                              "./TEMP/1.jpg", "./TEMP/2.jpg", "./TEMP/3.jpg", 
                              "./TEMP/4.jpg", "./TEMP/5.jpg", "./TEMP/6.jpg", 
                              "./TEMP/7.jpg", "./TEMP/8.jpg", "./TEMP/9.jpg",]
DRIVE_INPUT_FOLDER_ID = ""
DRIVE_OUTPUT_FOLDER_ID = ""

# the purpose of the Arduino is to control the stepper motors
class Arduino():
    def __init__(self):
        self.__device = None
        self.__initialised = False

    def initialise_arduino(self, port):
        self.__device = serial.Serial(port, 9600, timeout=1)
        self.__device.reset_input_buffer()
        self.__initialised = True

    def deinitialise_arduino(self):
        self.__device.close()
        self.__device = None
        self.__initialised = False
    
    def check_initialisation(self):
        return self.__initialised

    # send instruction to Arduino to make it move a specific motor in a certain direction
    # finetuning should be done in this step with time.sleep() to significantly speed up the Autoscope
    def send(self, motor, direction):
        response = "Not done"
        while response != "Done":
            instruction = f"{motor} {direction}\n"
            self.__device.write(instruction.encode("utf-8"))
            time.sleep(1)
            response = self.__device.readline().decode("utf-8").rstrip()

    # move motors by chosen steps in chosen direction
    def move_x(self, steps, direction):
        if self.check_initialisation:
            for _ in range(steps):
                self.send("x", direction)
        else:
            print("Arduino not initialised.")

    def move_y(self, steps, direction):
        if self.check_initialisation:
            for _ in range(steps):
                self.send("y", direction)
        else:
            print("Arduino not initialised.")

    def move_z(self, steps, direction):
        if self.check_initialisation:
            for _ in range(steps):
                self.send("z", direction)
        else:
            print("Arduino not initialised.")

    def move_lens(self, steps, direction):
        if self.check_initialisation:
            for _ in range(steps):
                self.send("l", direction)
        else:
            print("Arduino not initialised.")

class Camera():
    def __init__(self):
        self.__device = None
        self.__initialised = False
        self.__start = False

    def initialise_camera(self):
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

    def deinitialise_camera(self):
        if self.check_start():
            self.stop()
        self.__device = None
        self.__initialised = False

    def check_intialisation(self):
        return self.__initialised

    def start(self):
        if self.check_intialisation:
            self.__device.start()
            self.__start = True
        else:
            print("Camera not initialised.")

    def check_start(self):
        return self.__start

    def capture(self, filepath):
        if self.check_start():
            self.__device.capture_file(filepath)
        else:
            print("Camera not started.")

    def stop(self):
        if self.check_start():
            self.__device.stop()
        else:
            print("Camera not started.")

    def set_exposure(self, zoom):
        if self.check_intialisation:
            if zoom == "4x":
                self.__device.set_controls({"ExposureTime": X4_EXPOSURE_TIME})
            elif zoom == "10x":
                self.__device.set_controls({"ExposureTime": X10_EXPOSURE_TIME})
            else:
                self.__device.set_controls({"ExposureTime": X40_EXPOSURE_TIME})
            
            print("Setting Exposure.")
            time.sleep(10)
        else:
            print("Camera not initialised.")

class Autoscope(Arduino, Camera):
    def __init__(self):
        self.__initialisation = False
        self.__current_zoom = ""
        self.__x_position = 0
        self.__y_position = 0
        self.__z_position = 0
        self.__median_area = 5 # take center of sample as default

    def initialise(self, arduino_port):
        self.initialise_arduino(arduino_port)
        self.initialise_camera()

        try:
            os.mkdir(TEMP_FOLDER_PATH)
            os.mkdir(DATA_FOLDER_PATH)
        except FileExistsError:
            pass

        self.__initialisation = True

    def check_initialisation(self):
        return self.__initialisation

    def set_current_zoom(self, zoom):
        self.__current_zoom = zoom

    def get_current_zoom(self):
        return self.__current_zoom
    
    def get_x_position(self):
        return self.__x_position
    
    def get_y_position(self):
        return self.__y_position
    
    def get_z_position(self):
        return self.__z_position

    def smart_move_x(self, steps, direction):
        self.move_x(steps, direction)
        if direction == "+":
            self.__x_position += steps
        else:
            self.__x_position -= steps

    def smart_move_y(self, steps, direction):
        self.move_y(steps, direction)
        if direction == "+":
            self.__y_position += steps
        else:
            self.__y_position -= steps

    def smart_move_z(self, steps, direction):
        self.move_z(steps, direction)
        if direction == "+":
            self.__z_position += steps
        else:
            self.__z_position -= steps

    def set_median_area(self, median):
        self.__median_area = median

    def get_median_area(self):
        return self.__median_area

    def focus(self):
        if self.get_current_zoom in ["4x", "10x"]:
            self.focus_4x_10x()
        else:
            self.focus_40x()

    def focus_4x_10x(self):
        self.start()
        self.capture(FOCUS_PATH)
        current_sharpness = self.calculate_sharpness()
        best = [self.get_z_position, current_sharpness]
        print(f"{'{:0>2}'.format(best[0])}: {best[1]}")

        while self.get_z_position() < BOTTOM_LIMIT:
            self.smart_move_z(1, "+")
            self.capture(FOCUS_PATH)
            current_sharpness = self.calculate_sharpness()
            print(f"{'{:0>2}'.format(self.get_z_position)}: {current_sharpness}")
            if current_sharpness > best[1]:
                best = [self.get_z_position, current_sharpness]

        return_steps = self.get_z_position - best[0]
        self.smart_move_z(return_steps, "-")
        self.capture(FOCUS_PATH)
        print(f"{'{:0>2}'.format(self.get_z_position)}: {self.calculate_sharpness()}")
        self.stop()

    def focus_40x(self):
        self.start()
        self.capture(FOCUS_PATH)
        current_sharpness = self.calculate_sharpness()
        best = [self.get_z_position, current_sharpness]
        print(f"{'{:0>2}'.format(best[0])}: {best[1]}")

        while self.get_z_position > TOP_LIMIT:
            self.smart_move_z(1, "-")
            self.capture(FOCUS_PATH)
            current_sharpness = self.calculate_sharpness()
            print(f"{'{:0>2}'.format(self.get_z_position)}: {current_sharpness}")
            if current_sharpness > best[1]:
                best = [self.get_z_position, current_sharpness]
        
        return_steps = best[0] - self.get_z_position()
        self.smart_move_z(return_steps, "+")
        self.capture(FOCUS_PATH)
        print(f"{'{:0>2}'.format(self.get_z_position)}: {self.calculate_sharpness()}")
        self.stop()

    # Tenengrad method
    def calculate_sharpness(self):
        image = cv2.imread(FOCUS_PATH)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_sq = gx**2 + gy**2

        return np.sum(grad_sq)

    def identify_median_area(self):
        self.take_picture_of_sample()
        cell_counts = self.count_cells()
        sorted_cell_counts = sorted(cell_counts, key=lambda cell_count: cell_count[1])
        median = sorted_cell_counts[4][0]
        self.set_median_area = median

    def take_picture_of_sample(self):
        self.start()
        self.capture(SQUARE_GRID_PICTURES_PATHS[5])

        self.smart_move_x(16, "+")
        self.smart_move_y(3, "-")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[1])

        self.smart_move_x(16, "-")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[2])

        self.smart_move_x(16, "-")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[3])

        self.smart_move_y(3, "+")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[6])

        self.smart_move_y(3, "+")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[9])

        self.smart_move_x(16, "+")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[8])

        self.smart_move_x(16, "+")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[7])

        self.smart_move_y(3, "-")
        time.sleep(1)
        self.capture(SQUARE_GRID_PICTURES_PATHS[4])

        self.smart_move_x(16, "-")
        self.stop()

    # square grid images can be sent over as npy files instead to reduce upload time
    def count_cells():
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth) # authentication, requires client_secrets.json to function

        if DRIVE_INPUT_FOLDER_ID == "":
            DRIVE_INPUT_FOLDER_ID = input("Please enter drive input folder id: ")
        if DRIVE_OUTPUT_FOLDER_ID == "":
            DRIVE_OUTPUT_FOLDER_ID = input("Please enter drive output folder id: ")

        input_folder = drive.ListFile({'q' : f"'{DRIVE_INPUT_FOLDER_ID}' in parents and trashed=false"}).GetList()
        output_folder = drive.ListFile({'q' : f"'{DRIVE_OUTPUT_FOLDER_ID}' in parents and trashed=false"}).GetList()

        try:
            for f in input_folder:
                f.Delete()
            for f in output_folder:
                f.Delete()
            print("Previous temporary drive data deleted.")
        except Exception as e:
            print(f"Error deleting temporary drive data: {e}.")
                
        for f in tqdm(SQUARE_GRID_PICTURES_PATHS[1:10], desc="Uploading files"):
            metadata = {
                'parents': [
                    {"id": f"{DRIVE_INPUT_FOLDER_ID}"}
                ],
                'title': f,
                'mimeType': 'image/jpeg'
            }
            upload = drive.CreateFile(metadata=metadata)
            upload.SetContentFile(f)
            upload.Upload()

        while True:
            if input("Please enter 'done' if images have been processed on GoogleColab: ") == "done":
                try:
                    query = {'q': "title = 'cell_counts.txt' and mimeType = 'text/plain'"}
                    f = drive.ListFile(query).GetList()[0]
                    text = f.GetContentString()
                    array = list(map(int, text.split()))

                    cell_counts = []
                    for i in range(1, 18, 2):
                        cell_counts.append((array[i-1], array[i]))

                    return cell_counts
                except Exception as e:
                    print(f"An error has occured: {e}. Try again.")
    
    def move_median_area(self):
        median = self.get_median_area()

        if median == 1:
            self.smart_move_x(16, "+")
            self.smart_move_y(3, "-")
        elif median == 2:
            self.smart_move_y(3, "-")
        elif median == 3:
            self.smart_move_x(16, "-")
            self.smart_move_y(3, "-")
        elif median == 4:
            self.smart_move_x(16, "+")
        elif median == 6:
            self.smart_move_x(16, "-")
        elif median == 7:
            self.smart_move_x(16, "+")
            self.smart_move_y(3, "+")
        elif median == 8:
            self.smart_move_y(3, "+")
        elif median == 9:
            self.smart_move_x(16, "-")
            self.smart_move_y(3, "+")

    def next_lens(self):
        if self.get_current_zoom == "4x":
            self.move_lens(1, "-")
            self.set_current_zoom = "10x"
            self.focus_4x_10x()
        elif self.get_current_zoom == "10x":
            self.move_lens(1, "-")
            self.set_current_zoom = "40x"
            self.focus_40x()
        else:
            self.move_lens(1, "-")
            self.set_current_zoom = "10x"
            print("Please load next sample.")

def main():
    autoscope = Autoscope()
    arduino_port = "/dev/ttyUSB0"
    autoscope.initialise(arduino_port)

    starting_zoom = query_starting_zoom()
    autoscope.set_exposure(starting_zoom)
    autoscope.focus()
    autoscope.identify_median_area()
    autoscope.move_median_area()
    autoscope.next_lens()
    choose(autoscope)

def query_starting_zoom():
    starting_zoom = ""
    valid_zoom_start = ["4x", "10x"]
    
    while not(starting_zoom in valid_zoom_start):
        starting_zoom = input("Enter starting zoom level (4x, 10x): ")
    
    return starting_zoom

def choose(autoscope):
    while True:
        response = input("Type 1 to save an image for identification, type 2 to collect image data: ")
        try:
            response = int(response)
            if response == 1:
                autoscope.capture("data/cell_image.jpg")
                break
            elif response == 2:
                autoscope.collect_data()
                break
        except ValueError:
            print("Invalid input, please input a number (1 or 2).")

if __name__ == "__main__":
    main()