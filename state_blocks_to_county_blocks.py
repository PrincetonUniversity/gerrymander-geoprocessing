import pandas as pd
import pysal as ps
import numpy as np
import geopandas as gpd
import shapely as shp
from shapely.geometry import MultiLineString
from shapely.geometry import Point
from shapely.geometry import LinearRing
from shapely.geometry import LineString
from shapely.geometry import Polygon
import re
import operator
import pickle
import os
import shutil

# Define paths
county_fips_path = 'G:/Team Drives/princeton_gerrymandering_project/mapping/' \
'2010 Census Block shapefiles/national_county_fips.txt'

census_shape_folder = 'G:/Team Drives/princeton_gerrymandering_project/' \
'mapping/2010 Census Block shapefiles/'

# Select state
state = 'VA'

# Define census name and path
census_filename = '/tabblock2010_51_pophu.shp'
census_shape_path = census_shape_folder + state + census_filename

# Define path to state folders
state_shape_folder = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts"

# Delete CPG file
cpg_path = ''.join(census_shape_path.split('.')[:-1]) + '.cpg'
if os.path.exists(cpg_path):
    os.remove(cpg_path)

# Define projection path and check if it exists
prj_exists = False
prj_path = ''.join(census_shape_path.split('.')[:-1]) + '.prj'
if os.path.exists(prj_path):
    prj_exists = True
    

#%% THIS TAKES REALLY LONG. Should Be able to skip once pickle file is saved
# Import census state file and save to pickle
no_pickle = 0
    
if no_pickle:
    df = gpd.read_file(census_shape_path)
    df.to_pickle(census_shape_folder + state + '/census_df.pkl')

#%% This also only takes kinda long

# Read in df and make county fips an int
df = pd.read_pickle(census_shape_folder + state + '/census_df.pkl')

#%%
df['COUNTYFP10'] = df['COUNTYFP10'].apply(int)

# Read in text file for fips codes
col_names = ['state', 'state_fips', 'county_fips', 'locality', 'H']
in_df = pd.read_csv(county_fips_path, names=col_names)

# Delete unnecessary column
in_df = in_df.drop(columns=['H'])

# Reduce dataframe to the selected state
in_df = in_df[in_df['state'] == state]

# Set index into locality
in_df = in_df.set_index('locality')

# Get the names of all of the folders in a list in order
folder_names = os.listdir(state_shape_folder)
folder_names.sort()
locality_names = list(in_df.index)

# Create booleans to determine whether to add every shapefile or certain ones
convert_every_locality = False
convert_list_locality = True
localities_to_convert =  ['Lunenburg County']

# Get the number of folder name matches
folder_count = 0
folder_missing = []
for name in folder_names:
    if name in locality_names:
        folder_count += 1
    else:
        folder_missing.append(name)

# Get the number of locality name matches
list_count = 0
list_missing = []
for name in localities_to_convert:
    if name in locality_names:
        list_count += 1
    else:
        list_missing.append(name)

# Perform for every county
if convert_every_locality:
    num_to_convert = len(in_df)
    # Check that every folder has a corresponding fips match
    if num_to_convert == folder_count:
        # Iterate through every locality
        for local in folder_names:
            # track how many counties remaining
            print(num_to_convert)
            num_to_convert -= 1
            
            # Obtain FIPS code
            fips = in_df.at[local, 'county_fips']
            
            # Save county shapefile
            df_county = df[df['COUNTYFP10'] == fips]
            df_county = gpd.GeoDataFrame(df_county, geometry='geometry')
            filename = local + ' census block'
            filename = filename.replace(' ', '_')
            out_path = state_shape_folder + '/' + local + '/' + filename

            out_path_shp = out_path + '.shp'
            df_county.to_file(out_path_shp)
            
            # Copy PRJ file if it exists
            out_path_prj = out_path + '.prj'
            if prj_exists:
                shutil.copy(prj_path, out_path_prj)
    else:
        print('\nChange FIPS text file to match folders')
        print(folder_missing)

# Perform for list of localities
elif convert_list_locality:
    num_to_convert = len(localities_to_convert)
    # Check that every folder has a corresponding fips match
    if num_to_convert == list_count:
        # Iterate through every locality
        for local in localities_to_convert:
            # track how many counties remaining
            print(num_to_convert)
            num_to_convert -= 1
            
            # Obtain FIPS code
            fips = in_df.at[local, 'county_fips']
        
            # Save county shapefile
            df_county = df[df['COUNTYFP10'] == fips]
            df_county = gpd.GeoDataFrame(df_county, geometry='geometry')
            filename = local + ' census block'
            filename = filename.replace(' ', '_')
            out_path = state_shape_folder + '/' + local + '/' + filename
            
            out_path_shp = out_path + '.shp'
            df_county.to_file(out_path_shp)
            
            # Copy PRJ file if it exists
            out_path_prj = out_path + '.prj'
            if prj_exists:
                shutil.copy(prj_path, out_path_prj)
    else:
        print('\nChange FIPS text file to match folders in convert list')
        print(list_missing)