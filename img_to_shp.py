import time
import pandas as pd
import pysal as ps
import geopandas as gpd
from PIL import Image
import os
import numpy as np
import math
import shapely as shp
from shapely.geometry import Polygon
from shapely.geometry import Point
from collections import Counter
import csv
import helper_tools as ht

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Auto CSV/TestTools.csv"

def main():
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        
        # Import Google Drive path
        direc_path = ht.read_one_csv_elem(csv_path)
        
        # Import table from CSV into pandas df
        csv_col = ['Locality', 'Num Regions', 'Census Path', 'Out Folder',\
                     'Image Path', 'Colors']
        csv_list = []
        csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)
    
        # Initialize out_df, which contains the results of the transfers and
        # contains what will be copied into the conversion page of the Google
        # sheet
        new_cols = ['Result', 'Time Taken', 'Num Census Blocks']
        out_df = pd.DataFrame(columns=new_cols)
        
        # Iterate through each county we are creating a shapefile for
        for i, _ in csv_df.iterrows():
            
            # Create shapefile out of precincts
            try:
                # Begin Start time
                start_time = time.time()
                
                # Set unique variables for the current county
                local = csv_df.at[i, 'Locality']
                num_regions = csv_df.at[i, 'Num Regions']
                shape_path = csv_df.at[i, 'Census Path']
                out_folder = csv_df.at[i, 'Out Folder']
                img_path = csv_df.at[i, 'Image Path']
                num_colors = csv_df.at[i, 'Colors']
        
                # Change census shapefile path and out folder if set to default
                if shape_path == 1:
                    census_filename = local + '_census_block.shp'
                    census_filename = census_filename.replace(' ', '_')
                    shape_path = direc_path + '/' + local + '/' + \
                                    census_filename
                    
                if out_folder == 1:
                    out_folder = direc_path + '/' + local
                    
                # set ouput shapefile name
                out_name = local + '_precinct'
                out_name = out_name.replace(' ', '_')
                
                # Generate precinct shapefile and add corresponding precinct
                # index to the attribute field of the census block shapefile
                print('\n' + local)
                result =  ht.shp_from_sampling(local, num_regions, shape_path,\
                                               out_folder, img_path, \
                                               num_colors)
                
                # Place Results in out_df. Save time taken and number of 
                # census blocks
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Time Taken'] = time.time() - start_time
                out_df.at[row, 'Num Census Blocks'] = result
            
            # Shapefile creation failed
            except:
                print('ERROR:' + csv_df.at[i, 'Locality'])
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
    
        # Create path to output our results CSV file and output
        csv_out_path = csv_path[:-4] + ' RESULTS.csv'
        out_df.to_csv(csv_out_path)
    
    # CSV file could not be read in or exported
    except:
        print('ERROR: Path for csv file does not exist OR close RESULTS csv')
        
if __name__ == '__main__':
    main()