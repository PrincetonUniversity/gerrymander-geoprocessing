from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
%matplotlib inline

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
        rgb = tuple(np.random.choice(range(256), size=3))
        if rgb not in used_colors:
            color_used = False
    return rgb

# Input and output paths for image being manipulated
img_path = '/Users/wtadler/Desktop/Wills/out1.png'
img_path_out = '/Users/wtadler/Desktop/Wills/out2.png'

# Define threshold for flood fill. This threshold is the 1-norm to determine
# how far away RGB values can be to be considered the same color. 0 means
# no tolerance
# (1-norm: |r1[0] - r2[0]| + |r1[1] - r2[1]| + |r1[2] - r2[2]|)
threshold = 0

# Do you want to reduce the number of colors in the current image 
# (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
# to reduce. Set to 0 if you do NOT want to reduce)
reduce_colors = 5

# Open image and convert to an array. Make old_img for reference
img = Image.open(img_path)
old_img = img

# Reduce to the desired number of colors
if reduce_colors:
    conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=reduce_colors)
    img = conv_img.convert('RGB')

# display image in IPython console to show the possibly reduced image
fig, ax = plt.subplots(figsize=(15,10))
ax.imshow(conv_img)

# Print out color palettes that are indexed for selection by user
colors = [elem[1] for elem in img.getcolors()]
for i, elem in enumerate(colors):
    print('\n\nColor ' + str(i))
    im = Image.new('RGB', (40, 40), color=elem)
    # dsplays in IPython console
    display(im)
    
# Ask for user input on which colors to remove
non_flood_color_str = input('Enter the numbers of the colors that will NOT have flood fill applied (separated by spaces if multiple): ')
print('Thank You!')
non_flood_colors = [colors[int(elem)] for elem in \
                               non_flood_color_str.split()]

# define an odd black in case (0,0,0) needs to be filled
black = (1, 2, 3)

# set used colors to the flood colors
used_colors = [(1, 2, 3)]

# Load how to access image pixels
pixel = img.load()

# Make all selected colros black
for x in range(img.size[0]):
    for y in range(img.size[1]):
        
        # If it is one of the original colors, possibly make black
        if pixel[x, y] in non_flood_colors:
            pixel[x, y] = black

for x in range(img.size[0]):
    for y in range(img.size[1]):
        # Apply flood fill if current pixel has not been used
        if pixel[x, y] not in used_colors:

            # get unique random color
            new_color = random_rgb(used_colors)
            
            # Flood fill
            ImageDraw.floodfill(img, (x,y), new_color, black, threshold)
            
            # Update used colors
            used_colors.append(new_color)

img.save(img_path_out)
