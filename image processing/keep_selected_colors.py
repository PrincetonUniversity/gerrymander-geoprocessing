# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 04:17:02 2018

@author: conno
"""

from PIL import Image
import numpy as np

# Get the image path
# Ask if you want to reduce the number of colors HIGHLY Recommended
# 


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


