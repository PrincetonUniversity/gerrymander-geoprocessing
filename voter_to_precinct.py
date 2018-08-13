# -*- coding: utf-8 -*-
"""
Created on Sun Aug 12 10:25:14 2018

@author: conno
"""

import time
import pandas as pd
import geopandas as gpd
import math
import censusbatchgeocoder
import os
import shapely as shp
import pysal as ps
import operator
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings("ignore")


#%%

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

def real_rook_contiguity(df, struct_type='list'):
    ''' Generates neighbor list using rook contiguity for a geodataframe.
    
    Arguments:
        df: geodataframe to apply rook contiguity to
        struct_type: determines whether neighbors are returned as a list or
        as a dict'''
    
    # Obtain queen continuity for each shape in the dataframe. We will remove 
    # all point contiguity. Shapely rook contiguity sometimes assumes lines
    # with small lines are points
    w = ps.weights.Queen.from_dataframe(df, geom_col='geometry')
    
    # Initialize neighbors column
    df['neighbors'] = pd.Series(dtype=object)   
    
    # Initialize neighbors for each precinct
    for i,_ in df.iterrows():
        struct = w.neighbors[i]
        
        # Iterate through every precinct to remove all neighbors that only 
        # share a single point. Rook contiguity would asssume some lines are 
        # points, so we have to use queen and then remove points
        
        # Obtain degree (# neighbors) of precinct
        nb_len = len(struct)
        
        # Iterate through neighbor indexes in reverse order to prevent errors 
        # due
        # to the deletion of elements
        for j in range(nb_len - 1, -1, -1):
            # get the jth neighbor
            j_nb = struct[j]
            
            # get the geometry for both precincts
            i_geom = df.at[i, 'geometry']
            j_nb_geom = df.at[j_nb, 'geometry']
            
            # If their intersection is a point, delete j_nb from i's neighbor 
            # list do not delete in both directions. That will be taken care of
            # eventually when i = j_nb later in the loop or before this occurs
            geom_type = i_geom.intersection(j_nb_geom).type
            if geom_type == 'Point' or geom_type == 'MultiPoint':
                del struct[j]
        
        # Assign to dataframe according to the structure passed in
        if struct_type == 'list':
            df.at[i, 'neighbors'] = struct
        elif struct_type == 'dict':
            df.at[i, 'neighbors'] = dict.fromkeys(struct)
    return df

def get_shared_perims(df):
    ''' Return a dataframe that assigns the length of shared perimeters with
    neighbors in a dataframes neighbor list.
    
    Arguments:
        df:'''
        
    # iterate over all precincts to set shared_perims
    for i,_ in df.iterrows():
        
        # iterate over the neighbors of precinct i
        for key in df.at[i, 'neighbors']:
        
            # obtain the boundary between current precinct and its j neighbor
            shape = df.at[i, 'geometry'].intersection(df.at[key, 'geometry'])
            
            # get shared_perim length (casework)
            if shape.type == 'GeometryCollection' or \
                    shape.type == 'MultiLineString':
                length = 0
                for line in shape.geoms:
                    if line.type == 'LineString':
                        length += line.length
            elif shape.type == 'LineString':
                length = shape.length
            else:
                print(shape.type)
                print(i)
                print(key)
                print ('Unexpected boundary')
                length = -1
                
            df.at[i, 'neighbors'][key] = length
    return df

def assign_blocks(cb_df, reg_df, new_col):
    ''' Adds a new_col column to dataframe of census blocks using areal
    interpolation with a dataframe with new_col names and geometries.
    
    Arguments:
        cb_df: dataframe with census blocks
        reg_df: dataframe with regions
        new_col: the new column to create within the census block df

    Output:
        Modified cb_df with new_col

    Note: this will overwrite the new_col column in cb_df if it already
        exists.'''
        
    # construct spatial tree for precincts
    reg_df = gpd.GeoDataFrame(reg_df, geometry='geometry')
    pr_si = reg_df.sindex
    
    # instantiate empty 'region' column in cb_df
    #cb_df[new_col] = np.nan
    
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
        cb_df.at[i, new_col] = PR
        
    # return modified cb_df
    return cb_df
#%%
###############################################################################
###### INITIALIZATION #########################################################
###############################################################################

# test overall timing
total_start = time.time()

# Initialize master pickle path
pickle_path = 'G:/Team Drives/princeton_gerrymandering_project/mapping/Voter Roll/VINTON_full.pkl'

# import original CSV file as DataFrame
raw_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/Voter Roll/VINTON_full.csv"
raw_cols = ['id', 'address', 'city', 'state', 'zipcode', 'precinct']
df_raw = pd.read_csv(raw_path, names=raw_cols, header=0)
df_raw = df_raw.set_index('id')
    

#%%
###############################################################################
###### BATCH GEOCODING ########################################################
###############################################################################

start_batch = time.time()

# Define how large and many batches to use
batch_size = 500
batches = math.ceil(len(df_raw) / batch_size)

# initialize single calls indexes. List of lists where the first
# element is the starting index and the second element is the ending index
missed_ix = []


# initialize geocoded dataframe
df_geo =  pd.DataFrame()

print('How many batches: ' + str(batches))
# Iterate through the necessary number of batches
for batch_ix in range(batches):
    print('Batch Index: ' + str(batch_ix))
    batch_time = time.time()
    try:
        # Get starting and ending rows in the batch. Loc does not care if index
        # is greater than  length
        batch_start = batch_ix * batch_size
        batch_end = (batch_ix + 1) * batch_size - 1
        
        # Initialize the batch dataframe
        
        batch_df = df_raw.loc[batch_start:batch_end][:]

        # create dummy csv to load batches into the census API wrapper
        filename = './dummy.csv'
        batch_df.to_csv(filename)
    
        # reset result dataframe
        result_df = pd.DataFrame()
    
        # Put batch through census API
        result_dict = censusbatchgeocoder.geocode(filename)
        result_df = pd.DataFrame.from_dict(result_dict)
        
        # append to the geo dataframe
        df_geo = df_geo.append(result_df)
        print('Result Length: ' + str(len(result_df)))
        print('Geo Length: ' + str(len(df_geo)))
    except Exception as e:
        print(batch_ix)
        print(e)
        missed_ix.append([batch_start, batch_end])
    
    print('Batch Time: ' + str(time.time() - batch_time))

print(missed_ix)
# iterate through all hte missed indexes individaully and call
for missed in missed_ix:
    print(missed)
    for i in range(missed[0], missed[1] + 1):
        batch_df = df_raw.loc[i][:]
        
        filename = './dummy.csv'
        batch_df.to_csv(filename)
        
        # reset result dataframe
        result_df = pd.DataFrame()
        
        # Put single element through census API
        result_dict = censusbatchgeocoder.geocode(filename)
        result_df = pd.DataFrame.from_dict(result_dict)
        
        df_geo = df_geo.append(result_df)
    
    # Split into groups of 1000
    # Add try except to repeat if the server runs out of time
    # After returning a batch convert to a dataframe and append to our 
        # master dataframe
    # test timing

print('How long to perform census API batches: ' + str(time.time() - start_batch))

#%%

###############################################################################
###### GENERATE MASTER DATAFRAME ##############################################
###############################################################################

start_processing = time.time()

# Only keep rows that matches were found
print(len(df_geo))
df_geo = df_geo[df_geo['is_match'] == 'Match']

# create cenus block geoid
df_geo['GEOID'] = df_geo['state_fips'].map(str) + \
                    df_geo['county_fips'].map(str) + \
                    df_geo['tract'].map(str) + df_geo['block'].map(str)

# drop unnecessary columns from df_geo and df_raw
geo_drop_cols = ['address', 'city', 'state', 'zipcode', 'geocoded_address', \
                 'is_match', 'is_exact', 'returned_address', 'coordinates', \
                 'tiger_line', 'side', 'state_fips', 'county_fips', 'tract', \
                 'block', 'latitude', 'longitude', 'id']

# create master dataframe by dropping unnecessary columns in geo dataframe and
# save to the pickle path. Master column just has the GEOID and the most
# common precinct
df_master = df_geo.drop(columns=geo_drop_cols)
df_master = df_master.groupby(['GEOID']).agg(lambda x:x.value_counts()\
                              .index[0])
df_master.to_pickle(pickle_path)
print('How long to process dataframe: ' + str(time.time() - start_processing))
        
#%%

###############################################################################
###### MERGE KNOWN CENSUS BLOCKS ##############################################
###############################################################################

# read in master dataframe
df_master = pd.read_pickle(pickle_path)

start_known_precinct = time.time()

# read in shapefile
shp_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_census_block.shp"
shp_merge_col = 'BLOCKID10'

# Delete CPG file if it exists to prevent encoding error
cpg_path = ''.join(shp_path.split('.')[:-1]) + '.cpg'
if os.path.exists(cpg_path):
    os.remove(cpg_path)
    
# load shapefile and delete precinct column if it exists
df_shp = gpd.read_file(shp_path)
if 'precinct' in df_shp.columns:
    df_shp.drop(columns=['precinct'])
    
# left match precinct name on GEOID
df_master.index = pd.to_numeric(df_master.index)
df_shp[shp_merge_col] = pd.to_numeric(df_shp[shp_merge_col])
df_shp = df_shp.merge(df_master, how='left', left_on=shp_merge_col, \
                      right_on='GEOID')
# Assign NaN values to None
df_shp = df_shp.where((pd.notnull(df_shp)), None)

print('How long known precincts: ' + str(time.time() - start_known_precinct))


###############################################################################
###### CREATE INITIAL PRECINCTS ###############################################
###############################################################################
# Save original merge precincts
df_shp['merge_prec'] = df_shp['precinct']

# Replace None precinct with a unique character
for i, _ in df_shp.iterrows():
    # replace None with a unique character
    if df_shp.at[i, 'precinct'] == None:
        df_shp.at[i, 'precinct'] = 'None_' + str(i)
        
# Get unique values
prec_name = list(set(df_shp['precinct']))

# Initalize precinct dataframe
df_prec = pd.DataFrame(columns=['precinct', 'geometry'])

# Iterate through all of the precinct IDs and set geometry for df_prec
for i, elem in enumerate(prec_name):
    df_poly = df_shp[df_shp['precinct'] == elem]
    polys = list(df_poly['geometry'])
    df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
    df_prec.at[i, 'precinct'] = elem
        
#%%
    
###############################################################################
###### Combine Precincts By Shared Perimeter ##################################
###############################################################################
start_combine =  time.time()
# reset index
df_prec = df_prec.reset_index(drop=True)

# get rook contiguity and calculate shared perims
df_prec = real_rook_contiguity(df_prec, 'dict')
df_prec = get_shared_perims(df_prec)

# get list of precinct indexes to merge
precincts_to_merge = []
for i, _ in df_prec.iterrows():
    if df_prec.at[i, 'precinct'].split('_')[0] == 'None':
        precincts_to_merge.append(i)
        
# Iterate through indexes of precincts to merge
for i in precincts_to_merge:

    # update neighbors and shared_perims
    cur_prec = df_prec.at[i, 'neighbors']
    ix = max(cur_prec, key=cur_prec.get)
    merge_prec = df_prec.at[ix, 'neighbors']

    # merge dictionaries
    merge_prec = Counter(merge_prec) + Counter(cur_prec)

    # remove key to itself
    merge_prec.pop(ix)

    # set neighbor dictionary in dataframe
    df_prec.at[ix, 'neighbors'] = merge_prec
    
    # merge geometry
    df_prec.at[ix, 'geometry'] = df_prec.at[ix, 'geometry'].union\
        (df_prec.at[i, 'geometry'])
    
    # delete neighbor reference to i and add reference for merge to key
    for key in list(cur_prec):
        df_prec.at[key, 'neighbors'].pop(i)
        
        # get perimeter length for key in merge and set in neighbor list
        key_dist = df_prec.at[ix, 'neighbors'][key]
        df_prec.at[key, 'neighbors'][ix] = key_dist
    
# delete all merged precincts
df_prec = df_prec.drop(precincts_to_merge)
    
# reset index for df_prec
df_prec = df_prec.reset_index(drop=True)
    
print('How long to combine precinct: ' + str(time.time() - start_combine))
       

#%%
###############################################################################
###### CREATE PRECINCT SHAPEFILE AND SAVE #####################################
###############################################################################

start_create_and_save = time.time()

# Assign precincts to census blocks. Save precinct names for GIS
df_prec['precinct_id'] = df_prec['precinct']
df_prec = df_prec.set_index('precinct_id')
df_shp = assign_blocks(df_shp, df_prec, 'precinct')

# Save shapefiles
block_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_block_smooth_perimeters.shp"
prec_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_precinct_smooth_perimeters.shp"
block_len = save_shapefiles(df_shp, df_prec, block_path, prec_path)


# Delete the dummy csv used to pass in batches
#os.remove('./dummy.csv')

print('How long to create precinct shp and save files: ' + str(time.time() - start_create_and_save))

print('Total Census Blocks: ' + str(block_len))
print('Number of Matched Census Blocks: ' + str(len(df_master)))

