import serial, time, cv2, os
import numpy as np
from tqdm import tqdm
from picamera2 import Picamera2
from libcamera import controls
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


# track current position of platform to prevent collision
current = 0
minimum_z = 35


def calculate_sharpness(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_sq = gx**2 + gy**2
    
    return np.sum(grad_sq) # sharpness


# motor name ["x", "y", "z", "l"], direction ["+", "-"]
def move_motor(motor, direction):
    response = "Not done"
    while response != "Done":
        instruction = f"{motor} {direction}\n"
        arduino.write(instruction.encode("utf-8"))
        time.sleep(1)
        response = arduino.readline().decode("utf-8").rstrip()
    return


def move_x(steps, direction):
    for i in range(steps):
        move_motor("x", direction)


def move_y(steps, direction):
    for i in range(steps):
        move_motor("y", direction)


def focus(limit, mode):
	camera.capture_file("temp/focus.jpg") # can change to capture numpy array instead
	current_sharpness = calculate_sharpness("temp/focus.jpg") # intial sharpness

	global current
	best = [current, current_sharpness]
	print(f"{current}: {current_sharpness}")

	if mode == "downwards":
		bottom = limit + current - 1
		while current < bottom:
			move_motor("z", "+") # go to next step
			current += 1
			camera.capture_file("temp/focus.jpg")
			current_sharpness = calculate_sharpness("temp/focus.jpg")
			print(f"{current}: {current_sharpness}")
			if current_sharpness > best[1]: # save new best position
				best = [current, current_sharpness]
				
		return_steps = current - best[0]
		for i in range(return_steps): # return to best position
			move_motor("z", "-")
			current -= 1
                
	elif mode == "upwards":
		while current > minimum_z: # also make sure actual position is above minimum_z position, for last zoom we go up instead
			move_motor("z", "-") # go to next step
			current -= 1
			camera.capture_file("temp/focus.jpg")
			current_sharpness = calculate_sharpness("temp/focus.jpg")
			print(f"{current}: {current_sharpness}")
			if current_sharpness > best[1]: # save new best position
				best = [current, current_sharpness]
				
		return_steps = best[0] - current
		for i in range(return_steps): # return to best position
			move_motor("z", "+")
			current += 1

	camera.capture_file("temp/focus.jpg")
	print(best)
	print(current)

	return


def take_picture_of_sample(): # can take pictures as numpy arrays instead
    #############
    # 1 # 2 # 3 #
    #############
    # 4 # 5 # 6 #
    #############
    # 7 # 8 # 9 #
    #############
    # the sample
    # 'x' '+' goes right
    # 'y' '+' goes up
    
    camera.capture_file("temp/5.jpg")

    move_x(16, "+")
    move_y(3, "-")
    time.sleep(1)
    camera.capture_file("temp/1.jpg")

    move_x(16, "-")
    time.sleep(1)
    camera.capture_file("temp/2.jpg")

    move_x(16, "-")
    time.sleep(1)
    camera.capture_file("temp/3.jpg")

    move_y(3, "+")
    time.sleep(1)
    camera.capture_file("temp/6.jpg")

    move_y(3, "+")
    time.sleep(1)
    camera.capture_file("temp/9.jpg")

    move_x(16, "+")
    time.sleep(1)
    camera.capture_file("temp/8.jpg")

    move_x(16, "+")
    time.sleep(1)
    camera.capture_file("temp/7.jpg")

    move_y(3, "-")
    time.sleep(1)
    camera.capture_file("temp/4.jpg")

    move_x(16, "-") # return to center
    
    return


def count_cells():
	gauth = GoogleAuth()
	gauth.LocalWebserverAuth()
	drive = GoogleDrive(gauth)

	drive = GoogleDrive(gauth) # authentication

	input_folder = drive.ListFile({'q' : "'1d2YUfW8d4tL57rssurazZXXzqD_GaEK8' in parents and trashed=false"}).GetList()
	output_folder = drive.ListFile({'q' : "'1YPrlwGlUEjJe-BMzjESk201zpbyNCwLQ' in parents and trashed=false"}).GetList()

	try:
		for f in input_folder: # clear input folder
			f.Delete()
			
		for f in output_folder: # clear output folder
			f.Delete()
			
		print("Previous temporary drive data deleted.")
		
	except Exception as e:
		print(f"Error deleting temporary drive data: {e}.")
			
	files = [f"temp/{i}.jpg" for i in range(1, 10)] # can send over as .npy files instead
	for f in tqdm(files, desc="Uploading files"):
		metadata = {
			'parents': [
				{"id": "1d2YUfW8d4tL57rssurazZXXzqD_GaEK8"} # input folder id
			],
			'title': f,
			'mimeType': 'image/jpeg'
		}
		upload = drive.CreateFile(metadata=metadata)
		upload.SetContentFile(f)
		upload.Upload()

	while True:
		response = input("Please enter 'done' if images have been processed on GoogleColab: ")
		if response == "done":
			try:
				query = {'q': "title = 'cell_counts.txt' and mimeType = 'text/plain'"}
				f = drive.ListFile(query).GetList()[0]
				text = f.GetContentString()
				array = list(map(int, text.split()))

				cell_counts = []
				for i in range(1, 18, 2):
					cell_counts.append((array[i-1], array[i])) # image number, cell count

				return cell_counts
				
			except Exception as e:
				print(f"An error has occured: {e}. Try again.")


def identify_median_area():
    take_picture_of_sample()
    cell_counts = count_cells()

    sorted_cell_counts = sorted(cell_counts, key=lambda cell_count: cell_count[1])
    median = sorted_cell_counts[4][0]

    return median


def move(median_area):
    if median_area == 1:
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
    
    return


def zoom(zoom_start):
	if zoom_start == "4x": # extra focusing step
		move_motor("l", "-")
		wait = input("Press Enter when turned.")
		print("Configuring camera.")
		camera.set_controls({"ExposureTime": 500_000}) # 0.5s for 10x zoom
		time.sleep(10)
		focus(25, "downwards")
		
	global current
	while current < minimum_z: # move down to minimum z position before switching to last zoom 
		move_motor("z", "+")
		current += 1

	move_motor("l", "-")
	wait = input("Press Enter when turned.")

	print("Configuring camera.")
	camera.set_controls({"ExposureTime": 3_000_000}) # 3s for 40x zoom
	time.sleep(10)
			
	focus(25, "upwards")

	return


def collect_data():
    name = input("Input cell/folder name to store images: ")
    number = 1
    camera.capture_file(f"data/{name}_{number}.jpg")

    for i in range(5):
        if i % 2 == 0:
            for j in range(1 + i):
                move_y(1, "-")
                number += 1
                camera.capture_file(f"data/{name}_{number}.jpg")
            for j in range(1 + i):
                move_x(1, "-")
                number += 1
                camera.capture_file(f"data/{name}_{number}.jpg")
        else:
            for j in range(1 + i):
                move_y(1, "+")
                number += 1
                camera.capture_file(f"data/{name}_{number}.jpg")
            for j in range(1 + i):
                move_x(1, "+")
                number += 1
                camera.capture_file(f"data/{name}_{number}.jpg")

    return
	

if __name__ == "__main__":
	# initialise connection
	arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
	arduino.reset_input_buffer()

	zoom_start_query = ""
	while not(zoom_start_query in ["4x", "10x"]):
		zoom_start_query = input("Enter zoom level (4x, 10x): ")
	
	if zoom_start_query == "4x":
		exposure_time = 100_000 # 0.1s for 4x zoom
	else:
		exposure_time = 500_000 # 0.5s for 10x zoom

	# set camera controls
	camera = Picamera2()
	camera.configure(camera.create_still_configuration(buffer_count=1, main={"size": (1280, 970)}))
	camera.set_controls({
		"AeEnable": False,
		"ExposureTime": exposure_time,
		"AnalogueGain": 1.0,
		"AfMode": controls.AfModeEnum.Manual,
		"LensPosition": 2.0
	})
	camera.start()

	focus(50, "downwards")

	median = identify_median_area()
	move(median)

	zoom(zoom_start_query)

	while True:
		response = input("Type 1 to save an image for identification, type 2 to collect image data: ")
		try:
			response = int(response)
			if response == 1:
				camera.capture_file("data/cell_image.jpg")
				break
			elif response == 2:
				collect_data()
				break
		except ValueError:
			print("Invalid input, please input a number (1 or 2).")
		
	print("Done!")
