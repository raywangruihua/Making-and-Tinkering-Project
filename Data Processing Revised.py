import cellpose
from cellpose import io, models
import numpy as np
import imageio.v2 as imageio
from skimage import color, util, measure
from tqdm import tqdm
import os

def main():
    model = models.CellposeModel(gpu=True)

    foldername = input("Enter foldername: ")
    directory = "./Dataset/Structures"
    folderpath = os.path.join(directory, foldername)
    try:
        filenames = sorted(os.listdir(folderpath))
    except FileNotFoundError:
        print("File(s) do not exist.")
        return

    newfoldername = input("Enter a folder to save cropped cell images to: ")
    directory = "./Dataset/Cells"
    newfolderpath = os.path.join(directory, newfoldername)
    try:
        os.mkdir(newfolderpath)
    except OSError:
        print("Folder already exists.")

    cellname = input("Enter cell type: ")

    maxcells = 2000
    pbar = tqdm(total=maxcells, desc="Processing")

    cellnumber = 1
    for file in filenames:
        if cellnumber > maxcells:
            break

        path = os.path.join(folderpath, file)
        img = imageio.imread(path)
        if img.ndim == 3 and img.shape[2] == 4:
            img = color.rgba2rgb(img)
        img_gray = color.rgb2gray(img)
        inp = (img_gray * 255).astype(np.uint8)
        
        masks, flows, styles = model.eval(inp)

        for prop in measure.regionprops(masks):
            label = prop.label
            minr, minc, maxr, maxc = prop.bbox

            cell_mask = (masks == label)

            cell_img = np.zeros_like(img)
            if img.ndim == 2:
                cell_img[cell_mask] = img[cell_mask]
            else:
                for c in range(img.shape[2]):
                    channel = img[...,c]
                    channel_out = np.zeros_like(channel)
                    channel_out[cell_mask] = channel[cell_mask]
                    cell_img[...,c] = channel_out

            cell_crop = cell_img[minr:maxr, minc:maxc]
            if cell_crop.dtype != np.uint8:
                cell_crop = util.img_as_ubyte(cell_crop)

            newpath = os.path.join(newfolderpath, f"{cellname}_{cellnumber:04d}.png")
            cellnumber += 1
            pbar.update(1)
            imageio.imwrite(newpath, cell_crop)
        
    pbar.close()
    print(f"Done! Extracted {cellnumber} cells.")

    return

if __name__ == "__main__":
    main()