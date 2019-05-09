'''
Create a bounding box around the extents of a shapefile. 

This will be used to overlay on top of a georeferenced image in GIS to allow for
automated cropping in the algorithm that converts converting precinct images to 
shapefiles. Will usually use a census block shapfile to generate this bounding
frame

Can perform for a batch
'''
import os, sys
os.chdir('..')
sys.path.append(os.getcwd())

import pandas as pd
import helper_tools.shp_manipulation as sm
import helper_tools.file_management as fm
import os.path
import sys

''' 
INPUT:

in_path: full path to input shapefile to create bounding frame for
out_path: full path to save bounding frame shapefile
'''
in_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/debug/input_noncontiguous.shp"
out_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/debug/correct_bounding_frame_noncontiguous.shp"
''' Code '''

# Generate bounding frame and save
df = fm.load_shapefile(in_path)
bounding_frame_df = sm.generate_bounding_frame(df)
fm.save_shapefile(bounding_frame_df, out_path)