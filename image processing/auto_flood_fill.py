from PIL import Image, ImageDraw
import numpy as np
from tqdm import tqdm

def random_rgb(used_colors=[]):
    ''' This function will return a random rgb list that is not in the list
    entered into the function
    
    Arguments:
        used colors is a list of rgb values that should not be selected. Takes
        the form [[0,0,0],[255,0,0]]
    '''
    color_used = True
    
    # Get random colors until we get a number not in used colors
    while color_used:
        rgb = list(np.random.choice(range(256), size=3))
        if rgb not in used_colors:
            color_used = False
    return rgb

# Load in image
# give option to convert all colors NOT to flood fill to black
# reduce colors
# display image
# print out color palettes 
# let user selct which colors NOT to flood fill
# Add selected colors too the list of used colors that will be inputted into the helper function
# Iterate through all pixels
    # If pixel value is not in used color
        # apply flood fill will new color. Add new color to used_color
    # If in don't flood fill possibly convert to black

#####
# helper function gets random RGB value that has not already been used

# Input and output paths for image being manipulated
img_path = ''
img_path_out = ''

# Define threshold for flood fill. This threshold is the 1-norm to determine
# how far away RGB values can be to be considered the same color. 0 means
# no tolerance
# (1-norm: |r1[0] - r2[0]| + |r1[1] - r2[1]| + |r1[2] - r2[2]|)
threshold = 0

#######################
img_path = 'C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/image processing/Auto Flood Fill Template.png'
img_path_out  = './auto_flood_test1.png'
######################

# Do you want to reduce the number of colors in the current image 
# (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
# to reduce. Set to 0 if you do NOT want to reduce)
reduce_colors = 5

# Do you want to convert colors that are not to be flood filled to black
convert_to_black = True

# Open image and convert to an array. Make old_img for reference
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
non_flood_color_str = input('Enter the numbers of the colors that will NOT have flood fill applied (separated by spaces if multiple): ')
non_flood_colors = [colors[int(elem)] for elem in \
                               non_flood_color_str.split()]

# Create image array and set flags to write
img_arr = np.asarray(img)
img_arr.setflags(write=1)

# define black and white
black = [0, 0, 0]

# set used colors to the flood colors
used_colors = non_flood_colors

# iterate through every pixel applying the flood fill
for y in tqdm(range(img.size[0])):
    for x in tqdm(range(img.size[1])):
        # Apply flood fill if current pixel has not been used
        if tuple(img_arr[x][y]) not in used_colors:
            # Get unique random color
            new_color = random_rgb(used_colors)
            
            # Flood fill
            ImageDraw.floodfill(img, (x,y), tuple(new_color),thresh=threshold)
            
            # Update used colors and image array
            used_colors.append(new_color)
            img_arr = np.asarray(img)
            img_arr.setflags(write=1)
            
# =============================================================================
#         # If it is one of the original colors, possibly make black
#         if tuple(img_arr[x][y]) in non_flood_colors and convert_to_black:
#             img_arr[x][y] = black
#             img = Image.fromarray(img_arr)
# =============================================================================
























