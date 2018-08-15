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
import helper_tools as tools

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/CSV/TestTools.csv"

def main():
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        # Import Google Drive path
        with open(csv_path) as f:
            reader = csv.reader(f)
            data = [r for r in reader]
        direc_path = data[0][1]
    
        # Import table from CSV into pandas dataframe
        name_list = ['Locality', 'Num Regions', 'Census Path', 'Out Folder',\
                     'Image Path', 'Colors']
        in_df = pd.read_csv(csv_path, header=1, names=name_list)
    
        # Initialize out_df, which contains the results of the transfers and
        # contains what will be copied into the conversion page of the Google
        # sheet
        new_cols = ['Result', 'Time Taken', 'Num Census Blocks']
        out_df = pd.DataFrame(columns=new_cols)
        
        # Iterate through each county we are creating a shapefile for
        for i, _ in in_df.iterrows():
            
            # Create shapefile out of precincts
            try:
                # Begin Start time
                start_time = time.time()
                
                # Set unique variables for the current county
                local = in_df.at[i, 'Locality']
                num_regions = in_df.at[i, 'Num Regions']
                shape_path = in_df.at[i, 'Census Path']
                out_folder = in_df.at[i, 'Out Folder']
                img_path = in_df.at[i, 'Image Path']
                num_colors = in_df.at[i, 'Colors']
        
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
                print(local)
                result = shp_from_sampling(local, num_regions, \
                                                      shape_path, out_folder, \
                                                      img_path, 
                                                      colors=num_colors)
                
                # Place Results in out_df
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Time Taken'] = time.time() - start_time
                out_df.at[row, 'Num Census Blocks'] = result
            
            # Shapefile creation failed
            except Exception as e:
                print(e)
                print('ERROR:' + in_df.at[i, 'Locality'])
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
    
        # Create path to output our results CSV file and output
        csv_out_path = csv_path[:-4] + ' RESULTS.csv'
        out_df.to_csv(csv_out_path)
    
    # CSV file could not be read in or exported
    except:
        print('ERROR: Path for csv file does not exist OR close RESULTS csv')
    
def shp_from_sampling(local, num_regions, shape_path, out_folder,\
                                img_path, colors=0, sample_limit=500):
    ''' Generates a precinct level shapefile from census block data and an 
    image cropped to a counties extents. Also updates the attribute table in
    the census block shapefile to have a precinct value.
    
    Arguments:
        local: name of the locality
        num_regions: number of precincts in the locality
        shape_path: full path to the census block shapefile
        out_folder: directory that precinct level shapefile will be saved in
        img_path: full path to image used to assign census blocks to precincts
        
    Output:
        Number of census blocks in the county
        '''        
    # Convert image to array, color reducing if specified
    img = Image.open(img_path)
    if colors > 0:
        img = tools.reduce_colors(img, colors)
    img_arr = np.asarray(img)

    # Delete CPG file if it exists
    cpg_path = ''.join(shape_path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)
    
    # read in census block shapefile
    df = gpd.read_file(shape_path)

    # Create a new color and district index series in the dataframe
    add_cols = ['color', 'region', 'area']
    for i in add_cols:
        df[i] = pd.Series(dtype=object)
    
    # Calculate boundaries of the geodataframe using union of geometries
    bounds = shp.ops.cascaded_union(list(df['geometry'])).bounds
    
    # Calculate global bounds for shape
    shp_xlen = bounds[2] - bounds[0]
    shp_ylen = bounds[3] - bounds[1]
    shp_xmin = bounds[0]
    shp_ymin = bounds[1]
    
    # Iterate through each polygon and assign its most common color
    for i, _ in df.iterrows():
        
        # Get current polygon
        poly = df.at[i, 'geometry']
        
        # Set color for census block
        df.at[i, 'color'] = tools.most_common_color(poly, img_arr, shp_xmin, \
             shp_xlen, shp_ymin, shp_ylen, sample_limit)
            
    # Assign each polygon with a certain color a district index
    for i, color in enumerate(df['color'].unique()):
        df.loc[df['color'] == color, 'region'] = i
        
    ###########################################################################
    ###### CREATE PRECINCTS USING ID ##########################################
    ###########################################################################
    
    # Get unique values in the df ID column
    prec_id = list(df.region.unique())
    
    df_prec = pd.DataFrame(columns=['region', 'geometry'])
    
    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # union
    for i in range(len(prec_id)):
        df_poly = df[df['region'] == prec_id[i]]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'region'] = prec_id[i]
        
    ###########################################################################
    ###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)#######################
    ###########################################################################
    
    # Initialize indexes to drop
    drop_ix = []
    
    # Iterate through every precinct
    for i, _ in df_prec.iterrows():
        # Check if it precinct is a MultiPolygon
        if df_prec.at[i, 'geometry'].type == 'MultiPolygon':
            # Add index as the index of a row to be dropped
            drop_ix.append(i)
            
            # get shape and area of current precinct
            precinct = df_prec.at[i, 'geometry']
    
            # Iterate through every contiguous region in the precinct
            for region in precinct.geoms:
                # Set geometry and id of new_shape
                d = {}
                d['region'] = df_prec.at[i, 'region']
                d['geometry'] = region
                df_prec = df_prec.append(d, ignore_index=True)
                
    # Remove original noncontiguous precincts
    df_prec = df_prec.drop(drop_ix)

    # Merge precincts fully contained in other precincts
    df_prec = tools.merge_fully_contained(df_prec)

    # Merge precincts until we have the right number
    df_prec = tools.merge_to_right_number(df_prec, num_regions)

    # Assign census blocks to regions
    df = tools.assign_blocks_to_regions(df, df_prec)
    
    # Save census block shapefile with updated attribute table
    tools.save_shapefile(df, shape_path, cols_to_exclude=['color'])
    
    # Save precinct shapefile
    out_name = local + '_precincts'
    out_name.replace(' ', '_')
    prec_shape_path = out_folder + '/' + out_name + '.shp'
    
    df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')
    tools.save_shapefile(df_prec, prec_shape_path, ['neighbors'])
        
    return len(df)
        
if __name__ == '__main__':
    main()