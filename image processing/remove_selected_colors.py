''' This script changes colors that are selected (kept) nearby colors'''

from PIL import Image
import numpy as np
from tqdm import tqdm

# Input and output paths for image being manipulated
img_path = ''
img_path_out = ''

#################
img_path_amherst = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Amherst County/Amherst Screenshot Cropped.png"
img_path = img_path_amherst
img_path_out = './Test_img3.png'
################
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
    
# Ask for user input on which colors to remove
remove_color_str = input('Enter the numbers of the colors to remove (separated by spaces if multiple): ')
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
                
        # If it is a remove color
        if remove and convert_non_white_to_black:
            img_arr[x][y] = black
        elif not remove:
            img_arr[x][y] = white


final_img = Image.fromarray(img_arr)
final_img.save(img_path_out)



#######################################################################3
for y in range(back_conv_img.size[0]):
    for x in range(back_conv_img.size[1]):
        
        #  Check if it a boundary color. Boundary color is saved
        boundary = False
        for boundary_color in boundary_colors:
            if list(back_arr[x][y]) == list(boundary_color):
                boundary = True
                
                
                
        # Change color of pixel
        if boundary:
            # iterate to the right until you find a different color
            shift_x = x + 1
            while shift_x < back_conv_img.size[1]:
                if tuple(back_arr[shift_x][y]) in boundary_colors:
                    shift_x += 1
                else:
                    back_arr[x][y] = back_arr[shift_x][y]
                    shift_x = back_conv_img.size[1]



