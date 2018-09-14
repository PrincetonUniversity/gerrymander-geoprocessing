# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 04:17:02 2018

@author: conno
"""

from PIL import Image
import numpy as np
from matplotlib.pyplot import imshow
from queue import *



img_path_hampton = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Hampton County Test Image Cropped.jpg"
img_path_grayson = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Grayson County Test Image.PNG"
img_path_covington = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Covington City Test Image.tif"

img_path_goochland = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/No Color/Goochland_original.PNG"
img_path_amherst = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Amherst County/Amherst Screenshot Cropped.png"
img_path_russell ="G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Russell County/Capture.PNG"
img_path_alleghany = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Alleghany County/Alleghany Screenshot.PNG"
img_path_hanover = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts/Hanover County/0001.png"

img_path = img_path_hanover

N = 15
# Convert image to array
img = Image.open(img_path)
img_arr = np.asarray(img)

conv_img = img.convert('P', palette=Image.ADAPTIVE, colors = N)

back_conv_img = conv_img.convert('RGB')
back_arr = np.asarray(back_conv_img)

colors = [elem[1] for elem in back_conv_img.getcolors()]

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

# make back_arr writeable
back_arr.setflags(write=1)

# Convert to black and white image
black = (0,0,0)
white = (255,255,255)



import time
start = time.time()
current = start
for y in range(back_conv_img.size[0]):
    for x in range(back_conv_img.size[1]):
        boundary = False
        for boundary_color in boundary_colors:
            if list(back_arr[x][y]) == list(boundary_color):
                boundary = True
                
        # Change color of pixel
        if boundary:
            back_arr[x][y] = black
        else:
            back_arr[x][y] = white
            
    if y % 100 ==0:
        print(y)
        print(time.time() - current)
        current= time.time()


binary_img = Image.fromarray(back_arr)

#%%
binary_img.save('./alleghany_original_black_white2.bmp')
back_conv_img.save('./alleghany_back_convert2.jpg')

print(time.time() - start)
        
#%%

def flood_fill(img_arr, x, y, target_color, replace_color):
    ''' This algorithm will run flood fill on an image'''
    
    # set flags to allow editing of img_arr
    img_arr.setflags(write=1)
    
    pixel_color = list(img_arr[x][y])
    target_color = list(target_color)
    replace_color =  list(replace_color)
    
    # Nothing to be done if target color is the replace color
    if target_color == replace_color:
        return 0 
    
    # Nothing to be done if pixel does not have the target color
    elif pixel_color != target_color:
        return 0 
    
    else:
        # Set pixel color
        img_arr[x][y] = replace_color
        
        # Initialize queue to have a list containing x, y
        q = Queue(maxsize=0)
        q.put([x,y])
        
        count = 0
        while not q.empty():
            
            # pop set of coordinates from front of queue
            n = q.get()
            count += 1
            # Above
            if y > 0:
                if list(img_arr[n[0], n[1] - 1]) == target_color:
                    img_arr[n[0], n[1] - 1] = replace_color
                    q.put([n[0], n[1] - 1])
            
            # Below
            if y < len(img_arr) - 1:
                    img_arr[n[0], n[1] + 1] = replace_color
                    q.put([n[0], n[1] + 1])       
                    
            # Left
            if x > 0:
                    img_arr[n[0] - 1, n[1]] = replace_color
                    q.put([n[0] - 1, n[1]])            
            # Right
            if x < len(img_arr[y]) - 1:
                    img_arr[n[0] + 1, n[1]] = replace_color
                    q.put([n[0] + 1, n[1]])        
        # return that a change occurred
        return 1
    
    
def random_rgb(used_colors=[]):
    ''' This function will return a random rgb tuple that is not in the list
    entered into the function
    
    Arguments:
        used colors is a list of rgb values that should not be selected'''
    color_used = True
    
    # Get random colors until we get a number not in used colors
    while color_used:
        rgb = list(np.random.choice(range(256), size=3))
        color_used = False
        for color in used_colors:
            if rgb == color:
                color_used = True
            
    return rgb
    
# Get binary array
binary_arr = np.asarray(binary_img)

print('Flood Fill')
start = time.time()
current = start

# Initialize empty list of used colors
used_colors = []

# get initial random color
replace = random_rgb()
used_colors.append(replace)

# initialize target color (white)
target = [255, 255, 255]

# iterate through every pixel
for y in range(binary_img.size[0]):
    for x in range(binary_img.size[1]):
        print(replace)
        # start fill flood
        flood_result = flood_fill(binary_arr, x, y, target, replace)
        
        # change colors if color was used in fill flood
        if flood_result:
            replace = random_rgb()
            used_colors.append(replace)
        break
    break
    if y % 100 == 0:
        print(y)
        print(time.time() - current)
        current= time.time()

print('Final Flood Fill Time')
print(time.time() - start)  


filled_img = Image.fromarray(binary_arr)
filled_img.save('./hampton_filled_new.jpg')


























