import sys
from frontend import MainMenu, QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_menu = MainMenu()
    main_menu.start_autoscope()
    main_menu.show()

    sys.exit(app.exec())

'''
def main():
    autoscope = Autoscope()
    arduino_port = "/dev/ttyUSB0"
    autoscope.initialise(arduino_port)

    starting_zoom = query_starting_zoom()
    autoscope.set_exposure(starting_zoom)
    # some tweaking may be required for top and bottom limits of platform
    autoscope.focus()
    autoscope.identify_median_area()
    autoscope.move_median_area()
    # some tweaking might be required for transitioning from 10x zoom to 40x zoom
    autoscope.next_lens()
    choose(autoscope)

    autoscope.deinitialise()

def query_starting_zoom():
    starting_zoom = ""
    valid_zoom_start = ["4x", "10x"]
    while not(starting_zoom in valid_zoom_start):
        starting_zoom = input("Enter starting zoom level (4x, 10x): ")
    return starting_zoom

def choose(autoscope):
    while True:
        response = int(input("Type 1 to save an image for identification." \
                        "Type 2 to collect image data."
                        "Type 3 to take manual control of Autoscope."
                        "Type 4 to shutdown Autoscope."))
        
        match response:
            case 1:
                filename = input("Enter name for image: ")
                autoscope.capture(os.path.join(DATA_FOLDER_PATH, filename))
            case 2: 
                autoscope.collect_data()
            case 3: 
                autoscope.manual()
            case 4:
                return
            case _:
                print("Invalid input, please input a number (1 to 3)")

if __name__ == "__main__":
    main()
'''