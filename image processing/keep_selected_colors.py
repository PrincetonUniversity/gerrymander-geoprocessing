''' This script changes colors that are not selected (kept) to the color
(255,255,255). It also gives the choice to convert all non-white boundaries to 
black (0,0,0)'''

from PIL import Image
import numpy as np
from tqdm import tqdm

# Input and output paths for image being manipulated
img_path = ''
img_path_out = ''

# Do you want to reduce the number of colors in the current image 
# (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
# to reduce. Set to 0 if you do NOT want to reduce)
reduce_colors = 5

# Do you convert all non-white colors to black?
convert_non_white_to_black = False

# Open image and convert to an array
img = Image.open(img_path)
old_img = img
    
# Reduce to the desired number of colors
if reduce_colors:
    conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=reduce_colors)
    img = conv_img.convert('RGB')
    
# display image in IPython console to show the possibly reduced image
display(img)

# Print out color palettes that are indexed for selection by user
colors = [elem[1] for elem in img.getcolors()]
for i, elem in enumerate(colors):
    print('\n\nColor ' + str(i))
    im = Image.new('RGB', (40, 40), color=elem)
    # dsplays in IPython console
    display(im)
    
# Ask for user input on which colors to keep
keep_color_str = input('Enter the numbers of the colors to keep (separated by spaces if multiple): ')
keep_color_list = [int(elem) for elem in keep_color_str.split()]
keep_colors = [colors[elem] for elem in keep_color_list]

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
        
        # Check if it is a keep color
        keep = False
        for keep_color in keep_colors:
            if list(img_arr[x][y]) == list(keep_color):
                keep = True
                
        # If it is a keep color
        if keep and convert_non_white_to_black:
            img_arr[x][y] = black
        elif not keep:
            img_arr[x][y] = white


final_img = Image.fromarray(img_arr)
final_img.save(img_path_out)