''' This script changes colors that are selected (kept) nearby colors'''

from PIL import Image
import numpy as np
from tqdm import tqdm

# Input and output paths for image being manipulated
img_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/image processing/Auto Flood Fill Template.png"
img_path_out = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/image processing/Auto Flood Fill Template Removed Color.png"

# Do you want to reduce the number of colors in the current image 
# (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
# to reduce. Set to 0 if you do NOT want to reduce)
reduce_colors = 4

# Open image and convert to an array
img = Image.open(img_path)
old_img = img
    
# Reduce to the desired number of colors
if reduce_colors:
    conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=reduce_colors)
    img = conv_img.convert('RGB')
    
# display image in IPython console to show the possibly reduced image
display(img)
img.save(img_path_out)

# Print out color palettes that are indexed for selection by user
colors = [elem[1] for elem in img.getcolors()]
for i, elem in enumerate(colors):
    print('\n\nColor ' + str(i))
    im = Image.new('RGB', (40, 40), color=elem)
    # dsplays in IPython console
    display(im)
    
# Ask for user input on which colors to remove
remove_color_str = input('Enter the numbers of the colors to remove (separated by spaces if multiple): ')
print('Thank You')
remove_color_list = [int(elem) for elem in remove_color_str.split()]
remove_colors = [colors[elem] for elem in remove_color_list]

# Create image array and set flags to write
img_arr = np.asarray(img)
img_arr.setflags(write=1)

# define black and white
black = [0, 0, 0]
white = [255, 255, 255]

# Iterate through pixels vertically
for y in tqdm(range(img.size[0])):
    # Iterate through pixels horizontally
    for x in range(img.size[1]):
        
        # Check if it is a remove color
        remove = False
        for remove_color in remove_colors:
            if list(img_arr[x][y]) == list(remove_color):
                remove = True
            
        # Try to find other pixel to the right
        if remove:
            # iterate to the right until you find a different color
            shift = x + 1
            while shift < img.size[1]:
                if tuple(img_arr[shift][y]) in remove_colors:
                    shift += 1
                else:

                    img_arr[x][y] = img_arr[shift][y]
                    shift = img.size[1]
                    remove = False
            
            
        # try to find other pixel to the left if one is not found to the right
        if remove:
            # iterate to the left until you find another color
            shift = x - 1
            while shift > 0:
                if tuple(img_arr[shift][y]) in remove_colors:
                    shift -= 1
                else:
                    img_arr[x][y] = img_arr[shift][y]
                    shift = 0
                    remove = False
        
        # try to find other pixel down if one has not been found
        if remove:
            # iterate down until you find another color
            shift = y + 1
            while shift < img.size[0]:
                if tuple(img_arr[x][shift]) in remove_colors:
                    shift += 1
                else:
                    img_arr[x][y] = img_arr[x][shift]
                    shift = img.size[0]
                    remove = False
            
        
        # try to find other pixel up if one has not been found
        if remove:
            # iterate up until you find another color
            shift = y - 1
            while shift > 0:
                if tuple(img_arr[x][shift]) in remove_colors:
                    shift -= 1
                else:
                    img_arr[x][y] = img_arr[x][shift]
                    shift = 0

final_img = Image.fromarray(img_arr)
final_img.save(img_path_out)

