import time
import pandas as pd
import pysal as ps
import geopandas as gpd
import os
import numpy as np
import shapely as shp
from shapely.geometry import Polygon
from collections import Counter
import csv
import pickle
# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Second Pass/Nottoway_Sussex_Aug_18.csv"

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
        name_list = ['Locality', 'Census Path', 'Out Folder']
        csv_df = pd.read_csv(csv_path, header=1, names=name_list)

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
                shape_path = csv_df.at[i, 'Census Path']
                out_folder = csv_df.at[i, 'Out Folder']

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
                
                # Print Locality Name to see where errors are from
                print('\n' + local)
                
                # Generate precinct shapefile and add corresponding precinct
                # index to the attribute field of the census block shapefile
                result = generate_precinct_shp_edited(local, shape_path, \
                                                      out_folder)
                
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Time Taken'] = time.time() - start_time
                out_df.at[row, 'Num Census Blocks'] = result
                
            # Shapefile creation failed
            except Exception as e:
                print(e)
                print('ERROR:' + csv_df.at[i, 'Locality'])
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
        
        # Create path to output our results CSV file and output
        csv_out_path = csv_path[:-4] + ' RESULTS.csv'
        out_df.to_csv(csv_out_path)
    
    # CSV file could not be read in or exported
    except:
        print('ERROR: Path for csv file does not exist OR close RESULTS csv')
    
def generate_precinct_shp_edited(local, shape_path, out_folder):
    ''' Generates a precinct level shapefile from census block data and an 
    an updated region attribute column. Also updates the attribute table in
    the census block shapefile to have a precinct value.
    
    Arguments:
        local: name of the locality
        shape_path: full path to the census block shapefile
        out_folder: directory that precinct level shapefile will be saved in
        
    Output:
        Number of census blocks in the county
        '''        
    # Delete CPG file if it exists
    cpg_path = ''.join(shape_path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)

    # read in census block shapefile
    df = gpd.read_file(shape_path)
    
    ###########################################################################
    ###### CREATE PRECINCTS USING ID ##########################################
    ###########################################################################
    
    # Get unique values in the df ID column
    prec_region = list(df.region.unique())
    
    # Create dataframe of precincts
    df_prec = pd.DataFrame(columns=['region', 'geometry', 'noncontiguous',\
                                    'contains_another_precinct', 'locality'])

    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # union
    for i, elem in enumerate(prec_region):
        df_poly = df[df['region'] == elem]
        polys = list(df_poly['geometry'])
        
        geometry = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'geometry'] = geometry
        df_prec.at[i, 'region'] = elem
        
        # check if precinct is noncontiguous
        if geometry.type == 'Polygon':
            
            # check if precinct contains another precinct. Only make this
            # check if the geometry type is a polygon
            poly_coords = list(geometry.exterior.coords)
            poly = Polygon(poly_coords)
            # If poly is within the geometry then no neighbors are contained
            if  geometry.contains(poly):
                df_prec.at[i, 'contains_another_precinct'] = 0
            else:
                df_prec.at[i, 'contains_another_precinct'] = 1
                print('Contains Another : ' + str(int(elem)))
        
        # Precinct is noncontiguous
        else:
            df_prec.at[i, 'noncontiguous'] = 1
            print('\nNoncontiguous: ' + str(int(elem)))
            print('Num Non-Contiguous Pieces to Fix: ' + str(len(geometry.geoms) - 1))
            
            # Check if any of the polygons in the MultiPolygon are donuts
            for sub_polygon in geometry.geoms:
                if sub_polygon.type == 'Polygon':
                    
                    # check if precinct contains another precinct.
                    poly_coords = list(sub_polygon.exterior.coords)
                    poly = Polygon(poly_coords)
                    
                    # If poly is within the geometry then no neighbors are 
                    # contained
                    if  geometry.contains(poly):
                        df_prec.at[i, 'contains_another_precinct'] = 0
                    else:
                        df_prec.at[i, 'contains_another_precinct'] = 1
                        print('\nContains Another : ' + str(int(elem)))

    # Initialize Locality Name
    df_prec['locality'] = local
    
    ###########################################################################
    ###### Save Shapefiles ####################################################
    ###########################################################################
    
# =============================================================================
#     # Save Precinct Shapefile
#     out_name = local + '_precincts'
#     out_name.replace(' ', '_')
#     
#     df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')
#     df_prec['region'] = pd.to_numeric(df_prec['region'], \
#            downcast='integer')
#     df_prec.to_file(out_folder + '/' + out_name + '.shp')
#         
# =============================================================================
    return len(df)
        
if __name__ == '__main__':
    main()