from PIL import Image
import pillow_heif
import os
import re

def file_converter_4channels():
    foldername = input("Input folder name: ")
    filenames = os.listdir(foldername)

    for filename in filenames:
        path = os.path.join(foldername, filename)
        img = Image.open(path)
        new_img = img.convert("RGBA")
        new_path = os.path.splitext(path)[0] + ".png"

        new_img.save(new_path, "PNG")
        os.remove(path)

    return

def folder_renamer():
    directory = "./Data/Structures"
    folders = os.listdir(directory)
    for folder in folders:
        seperators = r"[\s_-]+"
        newfoldername = re.split(seperators, folder)
        for i in range(len(newfoldername)):
            newfoldername[i] = newfoldername[i].capitalize()
        newfoldername = "_".join(newfoldername) # change this if there numbers
        newfolderpath = os.path.join(directory, newfoldername)
        oldfolderpath = os.path.join(directory, folder)
        try:
            os.rename(oldfolderpath, newfolderpath)
        except FileExistsError:
            continue

    return

def heic_to_png(filepath):
    image = Image.open(filepath)
    newfilepath = os.path.splitext(filepath)[0] + ".png"
    image.convert("RGB").save(newfilepath)
    os.remove(filepath)
    return

if __name__ == "__main__":
    pillow_heif.register_heif_opener()

    folder_renamer()
