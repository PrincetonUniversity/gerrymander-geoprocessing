import time
import pandas as pd
import helper_tools as ht
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import matplotlib.pyplot as plt
from tqdm.autonotebook import tqdm
import folium

''' This script changes colors that are not selected (kept) to the color
(255,255,255). It also gives the choice to convert all non-white boundaries to 
black (0,0,0)'''

def flood_fill(img_in="/Users/wtadler/Desktop/Wills/AlexandriaCity.png", img_out="/Users/wtadler/Desktop/Wills/filled.png"):

    # Input and output paths for image being manipulated

    # Do you want to reduce the number of colors in the current image 
    # (HIGHLY RECOMMENDED TO SET TO A VALUE. Set to any natural number if you want
    # to reduce. Set to 0 if you do NOT want to reduce)
    reduce_colors = 4

    # Do you convert all non-white colors to black?
    convert_non_white_to_black = False

    # Open image and convert to an array
    img = Image.open(img_in)
    old_img = img
        
    # Reduce to the desired number of colors
    if reduce_colors:
        conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=reduce_colors)
        img = conv_img.convert('RGB')
        
    # Print out color palettes that are indexed for selection by user
    colors = [elem[1] for elem in img.getcolors()]
    #%%
    # fig, ax = plt.subplots(reduce_colors, 1, figsize=(2,4))
    for i, elem in enumerate(colors):
        print('Color ' + str(i) + ':')
        im = Image.new('RGB', (40, 40), color=elem)
        im = ImageOps.expand(im, border=2)
        
        # dsplays in IPython console
        display(im)
    #%%
    
    print('\n\n')
    # Ask for user input on which colors to keep
    keep_color_str = input('Which color are the precinct boundaries?\n') # DO 1
    
    print('\nOkay! Finding precinct boundaries...')
    
    time.sleep(.5)

    #%%
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
    # final_img.save(img_path_out)


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
    # img_path = '/Users/wtadler/Desktop/Wills/out1.png'
    # img_path_out = '/Users/wtadler/Desktop/Wills/out2.png'

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
    # img = Image.open(img_path)
    img = final_img
    old_img = img

    # Reduce to the desired number of colors
    if reduce_colors:
        conv_img = img.convert('P', palette=Image.ADAPTIVE, colors=reduce_colors)
        img = conv_img.convert('RGB')

    # display image in IPython console to show the possibly reduced image
    #%%
    # fig, ax = plt.subplots(figsize=(15,10))
    # ax.imshow(conv_img)
    #%%

    # Print out color palettes that are indexed for selection by user
    # colors = [elem[1] for elem in img.getcolors()]
    # for i, elem in enumerate(colors):
    #     print('\n\nColor ' + str(i))
    #     im = Image.new('RGB', (40, 40), color=elem)
    #     # dsplays in IPython console
    #     display(im)
        
    # Ask for user input on which colors to remove
    non_flood_color_str = '1' #input('Enter the numbers of the colors that will NOT have flood fill applied (separated by spaces if multiple): ')
    # print('Thank You!')
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


    print('Flood filling with random colors...')
    for x in tqdm(range(img.size[0])):
        for y in range(img.size[1]):
            # Apply flood fill if current pixel has not been used
            if pixel[x, y] not in used_colors:

                # get unique random color
                new_color = random_rgb(used_colors)
                
                # Flood fill
                ImageDraw.floodfill(img, (x,y), new_color, black, threshold)
                
                # Update used colors
                used_colors.append(new_color)

    display(img)
    img.save(img_out)
    
    return img

#%%



def find_blocks(img, blocks_path, out_path):
    cropped = ht.cropped_bordered_image(img)
    
    # Generate precinct shapefile and add corresponding precinct
    # index to the attribute field of the census block shapefile
    
    blocks, precincts = ht.shp_from_sampling('Alexandria City ', 28, blocks_path,\
                                   out_path, cropped, \
                                   0)
    blocks.crs = {'init': 'epsg:4269'}
    precincts.crs = {'init': 'epsg:4269'}
    # df = ht.set_CRS(df)
    
    return blocks, precincts
    
    
def make_map(blocks, precincts):
    m = folium.Map(tiles=None, control_scale=True, location=(38.815, -77.09), min_zoom=13)

    folium.features.GeoJson(precincts['geometry'], overlay=False, show=True, name='Auto-traced precincts').add_to(m)
    folium.features.GeoJson(blocks['geometry'], overlay=False, show=False, name='Census blocks').add_to(m)
    
    folium.raster_layers.TileLayer(control=False, overlay=True, show=True, min_zoom=13).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    
    return m