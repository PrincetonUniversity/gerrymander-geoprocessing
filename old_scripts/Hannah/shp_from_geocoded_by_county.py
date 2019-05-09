import time
import pandas as pd
import geopandas as gpd
import math
import censusbatchgeocoder
import shapely as shp
import warnings
import numpy as np
warnings.filterwarnings("ignore")
import helper_tools as ht
import sys
sys.path.append('/Users/hwheelen/Documents/GitHub/gerrymander-geoprocessing/areal_interpolation')
import areal_interpolation as ai
from collections import Counter

"""
This script loops through every county in a state and adds geocoded precinct to census block file
The input is a geocoded voter roll and census block shapefile for each county stored in folders
named after the counties exactly as they appear in the list below
"""
#list of counties in state, exactly as names appear in folders
counties=[]

#Column info for shapefile
state_fips = ''
county_fips_col = ''
tract_col = ''
block_col = ''

#path to Utah county folders
start_path = ''

for county in counties:
    print(county)
    #make file paths
    shp_path = start_path + county + '/' + county.replace(' ','_')+ '_census_block.shp'
    geo_path = start_path + county+ '/' + county.replace(' ','_')+ '_geocoded_VR.csv'
    final_path = start_path  + county+ '/' + county.replace(' ','_')+ '_blocks_VR_Precincts.shp'
    # load shapefile and delete precinct column if it exists
    ht.delete_cpg(shp_path)
    df_shp = gpd.read_file(shp_path) 
    #format columns, make geoid, and delete precinct column if it already exists
    df_shp[county_fips_col] = df_shp[county_fips_col].map(lambda x: str(x)[:-2])
    df_shp[county_fips_col] = df_shp[county_fips_col].apply(lambda x: '{0:0>3}'.format(x))
    df_shp[tract_col] = df_shp[tract_col].map(lambda x: str(x).split('.')[0])
    df_shp[tract_col] = df_shp[tract_col].apply(lambda x: '{0:0>6}'.format(x))
    df_shp[block_col] = df_shp[block_col].map(lambda x: str(x).split('.')[0])
    df_shp[block_col] = df_shp[block_col].apply(lambda x: '{0:0>4}'.format(x))
    df_shp['GEOID10'] = state_fips + df_shp[county_fips_col] + df_shp[tract_col].map(str) + df_shp[block_col].map(str)
    df_shp.GEOID10 = df_shp.GEOID10.astype(int)
    df_shp = df_shp.set_index('GEOID10')
    if 'precinct' in df_shp.columns:
        df_shp = df_shp.drop(columns=['precinct'])
        
        
    #load in geocoded voter roll for this county
    geo_df = gpd.read_file(geo_path)
    #format columns
    geo_df['tract'] = geo_df['tract'].map(lambda x: str(x)[:-2])
    geo_df['tract'] = geo_df['tract'].apply(lambda x: '{0:0>6}'.format(x))
    geo_df['block'] = geo_df['block'].map(lambda x: str(x)[:-2])
    geo_df['block'] = geo_df['block'].apply(lambda x: '{0:0>4}'.format(x))
    geo_df['county_fips'] = geo_df['county_fips'].apply(lambda x: '{0:0>3}'.format(x))
    geo_df['precinct'] = geo_df['precinct_name']
    #make geoid to match above
    geo_df['GEOID10'] = state_fips + geo_df['county_fips'] + geo_df['tract'] + geo_df['block']
    geo_df['GEOID10'] = geo_df['GEOID10'].astype(int)
    geo_df = geo_df.set_index('GEOID10')
    #make temp df of most common precinct name per block
    geo_df['BLOCKID']=geo_df.index
    df_temp = geo_df[['BLOCKID','county_fips','precinct']]
    df_temp = df_temp.groupby('BLOCKID')['precinct'].apply(list).apply(Counter)
    df_temp = pd.DataFrame(df_temp)
    df_temp = df_temp.dropna()
    for index, row in df_temp.iterrows():
        df_temp['precinct'][index]= df_temp['precinct'][index].most_common()[0][0]
    
    #join these together to get precinct name
    df_shp = df_shp.join(df_temp)
    
    # Assign NaN values to None
    df_shp = df_shp.where((pd.notnull(df_shp)), None)
    
    # Save original merge precincts
    df_shp['orig_prec'] = df_shp['precinct']
    
    # Replace None precinct with a unique character
    for i, _ in df_shp.iterrows():
        # replace None with a unique character
        if df_shp.at[i, 'precinct'] == None:
            df_shp.at[i, 'precinct'] = 'None_' + str(i)
            
    # Get unique values
    prec_name = list(set(df_shp['precinct']))
    
    # Initalize precinct dataframe
    df_prec = pd.DataFrame(columns=['precinct', 'geometry'])
    
    
    prec_name = list(set(df_shp['precinct']))
    # Iterate through all of the precinct IDs and set geometry for df_prec
    for i, elem in enumerate(prec_name):
        df_poly = df_shp[df_shp['precinct'] == elem]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'precinct'] = elem
    
    start_combine =  time.time()
    
    # reset index
    df_prec = df_prec.reset_index(drop=True)
    
    # get rook contiguity and calculate shared perims
    df_prec = ht.get_shared_perims(df_prec)
    
    # get list of precinct indexes to merge
    precincts_to_merge = []
    for i, _ in df_prec.iterrows():
        if str(df_prec.at[i, 'precinct']).split('_')[0] == 'None':
            precincts_to_merge.append(i)
            
    # merge geometries
    df_prec = ht.merge_geometries(df_prec, precincts_to_merge)
    
    # Save census block shapefile
    block_path = start_path + county + ' County/' + county.replace(' ','_')+ '_County_census_block.shp'
    # Save precinct assignments down to the block
    df = ai.aggregate(df_shp, df_prec, target_columns =['precinct'], spatial_index = False)[0]
    
    # Save shapefile
    df.to_file(final_path)
