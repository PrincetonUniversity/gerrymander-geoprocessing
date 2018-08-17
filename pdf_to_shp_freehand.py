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
import operator
import helper_tools as tools

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Auto CSV/TestTools2.csv"


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
        in_df = pd.read_csv(csv_path, header=2, names=name_list)

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
                shape_path = in_df.at[i, 'Census Path']
                out_folder = in_df.at[i, 'Out Folder']

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
                result = generate_precinct_shp_free(local, shape_path,\
                                                    out_folder)

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


def assign_blocks_to_regions(cb_df, reg_df):
    ''' Adds a 'region' column to dataframe of census blocks using areal
    interpolation with a dataframe with region names and geometries.
    
    Arguments:
        cb_df: dataframe with census blocks
        reg_df: dataframe with regions

    Output:
        Modified cb_df with 'region' column

    Note: this will overwrite the 'region' column in cb_df if it already
        exists.'''
        
    # construct spatial tree for precincts
    reg_df = gpd.GeoDataFrame(reg_df, geometry='geometry')
    pr_si = reg_df.sindex
    
    # instantiate empty 'region' column in cb_df
    cb_df['region'] = np.nan
    
    # iterate through every census block, i is the GEOID10 of the precinct
    for i, _ in cb_df.iterrows():

        # let census_block equal the geometry of the census_block. Note: later
        # census_block.bounds is the minimum bounding rectangle for the cb
        census_block = cb_df.at[i, 'geometry']
        
        # Find which MBRs for districts intersect with our cb MBR
        # MBR: Minimum Bounding Rectangle
        poss_pr = [reg_df.index[i] for i in \
                   list(pr_si.intersection(census_block.bounds))]
        
        # If precinct MBR only intersects one district's MBR, set the district
        if len(poss_pr) == 1:
            PR = poss_pr[0]
        else:
            # for cases with multiple matches, compare fractional area
            frac_area = {}
            found_majority = False
            for j in poss_pr:
                if not found_majority:
                    area = reg_df.at[j, 'geometry'].intersection(\
                                     census_block).area / census_block.area
                    # Majority area means, we can assign district
                    if area > .5:
                        found_majority = True
                    frac_area[j] = area
            PR = max(frac_area.items(), key=operator.itemgetter(1))[0]
    
        # Assign census block region to PR
        cb_df.at[i, 'region'] = PR
        
    # return modified cb_df
    return cb_df

def save_shapefiles(cblock_df, prec_df, cblock_file_str, prec_file_str):
    cblock_df1 = cblock_df
    if 'neighbors' in cblock_df1.columns:
        cblock_df1 = cblock_df1.drop(columns=['neighbors'])
    cblock_df1.to_file(cblock_file_str)
    
    prec_df1 = gpd.GeoDataFrame(prec_df, geometry='geometry')
    if 'neighbors' in prec_df1.columns:
        prec_df1 = prec_df1.drop(columns=['neighbors'])
    prec_df1.to_file(prec_file_str)
    
    return len(cblock_df1)
    
def generate_precinct_shp_free(local, shape_path, out_folder):
    ''' Generates a precinct level shapefile from census block data and a
    region attribute column generated from selecting features in GIS. Also 
    updates the attribute table in the census block shapefile to have a 
    precinct value.
    
    Arguments:
        local: name of the locality
        num_regions: number of precincts in the locality
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
    
    # obtain the number of regions
    num_regions = len(set(df['ID']))

    # Create a new series for the region that the census block belongs
    df['region'] = pd.Series(dtype=object)
    
    # Apply rook contiguity
    df = tools.real_rook_contiguity(df)
    

    ###########################################################################
    ###### GIVE UNASSIGNED CENSUS BLOCKS AN ID ################################
    ###########################################################################

    
    # Find indices of unassigned census blocks
    ids = list(set(df['ID']))
    df2 = df
    for i in ids:
        df2 = df2[df2['ID'] != i]
    prec_to_set_list = list(df2.index)
    
    # If there are unassigned precincts, an unwanted ID value (None) will exist
    if len(prec_to_set_list) > 0:
        num_regions -= 1

    # Iterate until every census block has an ID
    while len(prec_to_set_list) > 0:
                
        # initialize list of precincts failed to set on this round
        # (use this structure to avoid deleting from a list while
        # iterating over it)
        prec_to_set_list_new = []
            
        # Loop through the current prec_to_set_list of unassigned census blocks
        for i in prec_to_set_list:
            
            # Iterate through the neighbors of the current census block
            
            # Get neighbors with an ID not equal to None
            nb_id = [j for j in  df.at[i, 'neighbors'] if \
                         df.at[j, 'ID'] != None]
            
            # If there is a neighbor with an ID not equal to None
            # set the ID to the neighbor's ID and remove i from list
            if len(nb_id) > 0:
                df.at[i, 'ID'] = df.at[nb_id[0], 'ID']
            else:
                prec_to_set_list_new.append(i)
        
        # update prec_to_set_list
        prec_to_set_list = prec_to_set_list_new

        
    ###########################################################################
    ###### CREATE PRECINCTS USING ID ##########################################
    ###########################################################################
    
    # Get unique values in the df ID column
    prec_ID = list(df.ID.unique())
    
    # Create dataframe of precincts
    df_prec = pd.DataFrame(columns=['region', 'geometry'])
    
    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # union
    for i, elem in enumerate(prec_ID):
        df_poly = df[df['ID'] == elem]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        
    out_name = local + '_precincts'
    out_name.replace(' ', '_')
    
    # Remove noncontiguous precincts
    df_prec = tools.split_noncontiguous(df_prec)

    # Merge precincts fully contained in other precincts
    df_prec = tools.merge_fully_contained(df_prec)

    # Assign census blocks to regions
    df = tools.assign_blocks_to_regions(df, df_prec)
        
    ###########################################################################
    ###### Save Shapefiles ####################################################
    ###########################################################################
    
    out_name = local + '_precincts'
    out_name.replace(' ', '_')
    
    return save_shapefiles(df, df_prec, shape_path,\
                    out_folder + '/' + out_name + '.shp' )
            
if __name__ == '__main__':
    main()