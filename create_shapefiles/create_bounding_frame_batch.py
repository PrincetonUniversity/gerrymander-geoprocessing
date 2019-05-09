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

# Get path to our CSV file
csv_path = ""

# Check if csv path has been entered in command line argument
if len(sys.argv) > 1:
    # If file exists then make the csv_path the second argument
    if os.path.isfile(sys.argv[1]):
        csv_path = sys.argv[1]
        print('\nUsing command argument as csv path')
    else:
        print('\nCSV path entered does not exist. Exiting.')
        sys.exit()

# Import CSV elements into dataframe
csv_col = ['Locality', 'In_Path', 'Out_Path']
csv_list = []
csv_df = fm.read_csv_to_df(csv_path, 0, csv_col, csv_list)

# Dissolve boundaries for each locality in the batch
for i, row in csv_df.iterrows():
    
    # Create shapefile out of precincts
    try:
        
        # Print Locality Name to see batch progress
        print('\n' + row['Locality'])

        # Generate bounding frame and save
        df = fm.load_shapefile(row['In_Path'])
        bounding_frame_df = sm.generate_bounding_frame(df)
        fm.save_shapefile(bounding_frame_df, row['Out_Path'])
        
    # Shapefile creation failed
    except Exception as e:
        print(e)
        print('ERROR:' + row['Locality'])
