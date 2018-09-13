''' This script changes colors that are not selected (kept) to the color
(255,255,255). It also gives the choice to convert all non-white boundaries to 
black (0,0,0)'''

from PIL import Image
import numpy as np

# Get the image path
# Ask if you want to reduce the number of colors HIGHLY Recommended
# Convert with boolean initialized at top
# extension to save as.'bmp' recommended would be at top
# output path to save as
# Reduce and convert if boolean is set to true
# get colors in converted image
# display img in ipython console for user to evaluate
# print out the different colors in the current picture
# ask the user to input the numbers of colors too keep
# remove colors not in this slist
# convert array to image
# save in paht as desired

# Input and output paths for image being manipulated
img_path = ''
img_path_out = ''

#################
img_path_amherst = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Amherst County/Amherst Screenshot Cropped.png"
img_path = img_path_amherst
################

# Do you want to reduce the number of colors in the current image 
# (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
# to reduce. Set to 0 if you do NOT want to reduce)
reduce_colors = 5

# Do you convert non-white to black?
convert_non_white_to_black = True

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
keep_color_str = input('Enter the numbers of the colors that make up the\
boundary (separated by spaces if multiple): ')

keep_color_str = input('Enter the numbers of the colors to keep (separated by spaces if multiple): ')
keep_color_list = [int(elem) for elem in keep_color_str.split()]
keep_colors = [colors[elem] for elem in keep_color_list]

# Create image array and set flags to write
img_arr = np.asarray(img)
img_arr.setflags

# define black and white
black = [0, 0, 0]
white = [255, 255, 255]

# Iterate through pixels vertically
for y in range(img.size[0]):
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
            
    if y % 100 ==0:
        print(y)
        print(time.time() - current)
        current= time.time()

remove_img = Image.fromarray(back_arr)






#%%



img_path_hampton = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Hampton County Test Image Cropped.jpg"
img_path_grayson = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Grayson County Test Image.PNG"
img_path_covington = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Covington City Test Image.tif"

img_path_goochland = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Goochland_original.PNG"
img_path_amherst = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Amherst County/Amherst Screenshot Cropped.png"
img_path_russell ="G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Russell County/Capture.PNG"
img_path_alleghany = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Alleghany County/Alleghany Screenshot.PNG"
img_path_hanover = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Hanover County/0001.png"

img_path = img_path_amherst

N = 10
# Convert image to array
img = Image.open(img_path)
img_arr = np.asarray(img)

conv_img = img.convert('P', palette=Image.ADAPTIVE, colors = N)

back_conv_img = conv_img.convert('RGB')
back_arr = np.asarray(back_conv_img)

colors = [elem[1] for elem in back_conv_img.getcolors()]

display(img)

#%%

for i, elem in enumerate(colors):
    print('\n\nColor ' + str(i))
    im = Image.new('RGB', (40, 40), color=elem)
    display(im)
    #imshow(np.asarray(im))
    
# Enter the color(s) that represent the border
boundary_color_str = input('Enter the numbers of the colors that make up the\
boundary (separated by spaces if multiple): ')

boundary_color_list = [int(elem) for elem in boundary_color_str.split()]

boundary_colors = [colors[elem] for elem in boundary_color_list]
    
#boundary_colors = [list(colors[9])]

#%%

# change colors that are in boundary colors to color on the right
print(back_conv_img.size[0])
back_arr.setflags(write=1)

import time
start = time.time()
current = start
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
            
    if y % 100 ==0:
        print(y)
        print(time.time() - current)
        current= time.time()

remove_img = Image.fromarray(back_arr)

#%%

# Save the image
remove_img.save('./hanover_removed.png')


