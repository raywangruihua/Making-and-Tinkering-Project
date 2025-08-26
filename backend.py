import serial, time, os, cv2, sys
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
from tqdm import tqdm
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# tweak constants here to suit Autoscope and environment (exposure)
# input drive folder ids before running count_cells method in Autoscope
DEFAULT_ARDUINO_PORT = "/dev/ttyUSB0"
X4_EXPOSURE_TIME  = 100_000
X10_EXPOSURE_TIME = 500_000
X40_EXPOSURE_TIME = 3_000_000
TOP_LIMIT         = 35
BOTTOM_LIMIT      = 50
TEMP_FOLDER_PATH  = "./TEMP"
DATA_FOLDER_PATH  = "./DATA"
FOCUS_PATH        = "./TEMP/FOCUS.jpg"
SQUARE_GRID_PICTURES_PATHS = ["",
                              "./TEMP/1.jpg", "./TEMP/2.jpg", "./TEMP/3.jpg", 
                              "./TEMP/4.jpg", "./TEMP/5.jpg", "./TEMP/6.jpg", 
                              "./TEMP/7.jpg", "./TEMP/8.jpg", "./TEMP/9.jpg",]
DRIVE_INPUT_FOLDER_ID  = "1d2YUfW8d4tL57rssurazZXXzqD_GaEK8"
DRIVE_OUTPUT_FOLDER_ID = "1YPrlwGlUEjJe-BMzjESk201zpbyNCwLQ"


# the purpose of the Arduino is to control the stepper motors
class Arduino():
    def __init__(self):
        self.arduino_device = None
        self.arduino_initialised = False

    # we used "/dev/ttyUSB0" as our default port for our set up
    def initialise_arduino(self, port=DEFAULT_ARDUINO_PORT):
        if self.arduino_initialised: 
	        sys.exit("Arduino already connected, please disconnect Arduino first before making new connection.")

        self.arduino_device = serial.Serial(port, 9600, timeout=1)
        self.arduino_device.reset_input_buffer()
        # add hand shake here to ensure arduino is connected
        self.arduino_initialised = True
        print("Arduino connected.")

    def deinitialise_arduino(self):
        if not self.arduino_initialised: 
            sys.exit("Arduino not connected, unable to disconnect.")

        self.arduino_device.close()
        self.arduino_device = None
        self.arduino_initialised = False
        print("Arduino disconnected.")

    # send instruction to Arduino to make it move a specific motor in a certain direction
    # finetuning should be done in this step with time.sleep() to significantly speed up the Autoscope
    def send(self, motor, direction):
        if not self.arduino_initialised: 
            sys.exit("Arduino not connected, unable to move motors.")

        response = "Not done"
        while response != "Done":
            instruction = f"{motor} {direction}\n"
            self.arduino_device.write(instruction.encode("utf-8"))
            time.sleep(1)
            response = self.arduino_device.readline().decode("utf-8").rstrip()

    # move motors by chosen steps in chosen direction
    def move_x(self, steps, direction):
        for _ in range(steps): self.send("x", direction)

    def move_y(self, steps, direction):
        for _ in range(steps): self.send("y", direction)

    def move_z(self, steps, direction):
        for _ in range(steps): self.send("z", direction)

    def move_lens(self, steps, direction):
        for _ in range(steps): self.send("l", direction)


class Camera():
    def __init__(self):
        self.camea_device = None
        self.camera_initialised = False
        self.camera_start = False

    def initialise_camera(self):
        if self.camera_initialised: 
            sys.exit("Camera already initialised.")

        self.camera_device = Picamera2()
        
        configuration = self.camera_device.create_still_configuration(
            buffer_count = 1,
            main = {"size": (1280, 970)}
        )
        self.camera_device.configure(configuration)

        self.camera_device.set_controls({
            "AeEnable"    : False,
            "ExposureTime": X4_EXPOSURE_TIME,
            "AnalogueGain": 1.0,
            "AfMode"      : controls.AfModeEnum.Manual,
            "LensPosition": 2.0
        })
        self.camera_initialised = True
        print("Camera initialised.")

    def deinitialise_camera(self):
        if not self.camera_initialised: 
            sys.exit("Camera not initialised, unable to deinitialise.")

        if self.camera_start: self.stop_camera()
        self.camera_device = None
        self.camera_initialised = False

    def start_camera(self):
        if not self.camera_initialised: 
            sys.exit("Camera not initialised, unable to start.")

        self.camera_device.start()
        self.camera_start = True
        print("Camera started.")

    def capture(self, filepath):
        if not self.camera_start: 
            sys.exit("Camera not started, unable to capture images.")

        if os.path.exists(filepath):
            query = ""
            while not(query in ["Y", "N"]):
                query = input("Image with same name already exists, override? (Y/N): ")
                if query == "Y": break 
                else: return
        self.camera_device.capture_file(filepath)

    def stop_camera(self):
        if not self.camera_start: 
            sys.exit("Camera not started, unable to stop.")
        self.camera_device.stop()
        print("Camera stopped")


class Autoscope(Arduino, Camera):
    def __init__(self):
        Arduino.__init__(self)
        Camera.__init__(self)
        self.initialisation = False
        self.current_zoom = ""
        self.x_position = 0
        self.y_position = 0
        self.z_position = 0
        self.median_area = 5 # take center of sample as default

    def initialise(self, arduino_port=DEFAULT_ARDUINO_PORT):
        self.initialise_arduino(arduino_port)
        self.initialise_camera()
        try:
            os.mkdir(TEMP_FOLDER_PATH)
            os.mkdir(DATA_FOLDER_PATH)
        except FileExistsError: pass
        
        self.initialisation = True
        print("Autoscope started.")

    def deinitialise(self):
        self.deinitialise_arduino()
        self.deinitialise_camera()
        self.initialisation = False
        print("Autoscope shutting down.")

    def smart_move_x(self, steps, direction):
        self.move_x(steps, direction)
        if direction == "+":
            self.x_position += steps
        else:
            self.x_position -= steps

    def smart_move_y(self, steps, direction):
        self.move_y(steps, direction)
        if direction == "+":
            self.y_position += steps
        else:
            self.y_position -= steps

    def smart_move_z(self, steps, direction):
        self.move_z(steps, direction)
        if direction == "+":
            self.z_position += steps
        else:
            self.z_position -= steps
    
    def set_current_zoom(self, zoom):
        self.current_zoom = zoom
    
    def set_exposure(self):
        if not self.camera_initialised: 
            sys.exit("Camera not initialised.")

        if self.current_zoom == "4x":
            self.camera_device.set_controls({"ExposureTime": X4_EXPOSURE_TIME})
        elif self.current_zoom == "10x":
            self.camera_device.set_controls({"ExposureTime": X10_EXPOSURE_TIME})
        elif self.current_zoom == "40x":
            self.camera_device.set_controls({"ExposureTime": X40_EXPOSURE_TIME})
        else:
            sys.exit("Invalid zoom level entered when setting exposure")
        
        print("Setting Exposure.")
        time.sleep(10)
        print(f"Exposure set for {self.current_zoom} zoom.")

    def focus(self):
        if self.current_zoom == "":
            sys.exit("Current zoom not set.")

        if self.current_zoom in ["4x", "10x"]:
            self.focus_4x_10x()
        elif self.current_zoom == "40x":
            self.focus_40x()
        else:
            sys.exit("Unrecognised zoom level.")

    def focus_4x_10x(self):
        print(f"Focusing at {self.current_zoom}")
        self.start_camera()
        self.capture_focus_image()
        current_sharpness = self.calculate_sharpness()
        best = [self.z_position, current_sharpness]
        print(f"{'{:0>2}'.format(best[0])}: {best[1]}")

        while self.z_position < BOTTOM_LIMIT:
            self.smart_move_z(1, "+")
            self.capture_focus_image()
            current_sharpness = self.calculate_sharpness()
            print(f"{'{:0>2}'.format(self.z_position)}: {current_sharpness}")
            if current_sharpness > best[1]:
                best = [self.z_position, current_sharpness]

        return_steps = self.z_position - best[0]
        self.smart_move_z(return_steps, "-")
        self.capture_focus_image()
        print(f"{'{:0>2}'.format(self.z_position)}: {self.calculate_sharpness()}")
        self.stop_camera()
        print("Focusing complete")

    def focus_40x(self):
        print(f"Focusing at {self.current_zoom}")
        self.start_camera()
        self.capture_focus_image()
        current_sharpness = self.calculate_sharpness()
        best = [self.z_position, current_sharpness]
        print(f"{'{:0>2}'.format(best[0])}: {best[1]}")

        while self.z_position > TOP_LIMIT:
            self.smart_move_z(1, "-")
            self.capture_focus_image()
            current_sharpness = self.calculate_sharpness()
            print(f"{'{:0>2}'.format(self.z_position)}: {current_sharpness}")
            if current_sharpness > best[1]:
                best = [self.z_position, current_sharpness]
        
        return_steps = best[0] - self.z_position
        self.smart_move_z(return_steps, "+")
        self.capture_focus_image()
        print(f"{'{:0>2}'.format(self.z_position)}: {self.calculate_sharpness()}")
        self.stop_camera()
        print("Focusing complete")
        
    def capture_focus_image(self):
        if not self.camera_start:
            sys.exit("Camera not started, unable to capture focus image.")
        self.camera_device.capture_file(FOCUS_PATH)

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
        self.median_area = sorted_cell_counts[4][0]

    def take_picture_of_sample(self):
        self.start_camera()
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
        self.stop_camera()

    # square grid images can be sent over as npy files instead to reduce upload time
    def count_cells(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth) # authentication, requires client_secrets.json to function

        input_folder = drive.ListFile({'q' : f"'{DRIVE_INPUT_FOLDER_ID}' in parents and trashed=false"}).GetList()
        output_folder = drive.ListFile({'q' : f"'{DRIVE_OUTPUT_FOLDER_ID}' in parents and trashed=false"}).GetList()

        try:
            for f in input_folder: f.Delete()
            for f in output_folder: f.Delete()
            print("Previous temporary drive data deleted.")
        except Exception:
            print(f"Error deleting temporary drive data. Continuing")
                
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
        if self.median_area == 1:
            self.smart_move_x(16, "+")
            self.smart_move_y(3, "-")
        elif self.median_area == 2:
            self.smart_move_y(3, "-")
        elif self.median_area == 3:
            self.smart_move_x(16, "-")
            self.smart_move_y(3, "-")
        elif self.median_area == 4:
            self.smart_move_x(16, "+")
        elif self.median_area == 6:
            self.smart_move_x(16, "-")
        elif self.median_area == 7:
            self.smart_move_x(16, "+")
            self.smart_move_y(3, "+")
        elif self.median_area == 8:
            self.smart_move_y(3, "+")
        elif self.median_area == 9:
            self.smart_move_x(16, "-")
            self.smart_move_y(3, "+")

    def next_lens(self):
        if self.current_zoom == "4x":
            self.move_lens(1, "-")
            self.current_zoom = "10x"
            self.focus_4x_10x()
        elif self.current_zoom == "10x":
            self.move_lens(1, "-")
            self.current_zoom = "40x"
            self.focus_40x()
        elif self.current_zoom == "40x":
            self.move_lens(1, "-")
            self.current_zoom = "10x"
            print("Please load next sample.")
        else:
            sys.exit("Unrecognised zoom level.")

    def collect_data(self):
        folder_name = input("Input cell/folder name to store images: ")
        number = 1
        folder_path = os.path.join(DATA_FOLDER_PATH, folder_name)
        self.capture(os.path.join(folder_path, f"{number}.jpg"))

        for i in range(5):
            if i % 2 == 0:
                for _ in range(1 + i):
                    self.smart_move_y(1, "-")
                    number += 1
                    self.capture(os.path.join(folder_path, f"{number}.jpg"))
                for _ in range(1 + i):
                    self.smart_move_x(1, "-")
                    number += 1
                    self.capture(os.path.join(folder_path, f"{number}.jpg"))
            else:
                for _ in range(1 + i):
                    self.smart_move_y(1, "+")
                    number += 1
                    self.capture(os.path.join(folder_path, f"{number}.jpg"))
                for _ in range(1 + i):
                    self.smart_move_x(1, "+")
                    number += 1
                    self.capture(os.path.join(folder_path, f"{number}.jpg"))

        print(f"Data collection complete: {number} images collected.")
