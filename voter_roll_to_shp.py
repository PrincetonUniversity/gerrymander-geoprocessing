import time
import pandas as pd
import geopandas as gpd
import math
import censusbatchgeocoder
import shapely as shp
from collections import Counter
import warnings
warnings.filterwarnings("ignore")
import helper_tools as ht

# test overall timing
total_start = time.time()

# import original CSV voter file as DataFrame
raw_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/Voter Roll/VINTON_full.csv"
raw_cols = ['id', 'address', 'city', 'state', 'zipcode', 'precinct']
df_raw = pd.read_csv(raw_path, names=raw_cols, header=0)
df_raw = df_raw.set_index('id')

# Define how large and many batches to use. Maximum batch size for cenus 
# geocoding is 1000. However, there will sometimes be a timeout request
batch_size = 500
batches = math.ceil(len(df_raw) / batch_size)

# initialize single calls indexes. List of lists where the first
# element is the starting index and the second element is the ending index
missed_ix = []

# initialize geocoded dataframe
df_geo =  pd.DataFrame()

# Iterate through the necessary number of batches
for batch_ix in range(batches):
    print('Batch Index: ' + str(batch_ix) + '/' + str(batches))
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
        
        print('Batch Time: ' + str(time.time() - batch_time))

    except:
        print('Above batch did not run')
        print(batch_ix)
        missed_ix.append([batch_start, batch_end])

# iterate through all the missed indexes individaully and call
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

# Convert geocoded dataframe into our desired geodataframe

# Only keep rows that matches were found
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

# create dataframe by dropping unnecessary columns in df_geo dataframe
# df just has the GEOID and the most common precinct
df = df_geo.drop(columns=geo_drop_cols)
df = df.groupby(['GEOID']).agg(lambda x:x.value_counts().index[0])

# get census block shapefile and col to merge on
shp_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_census_block.shp"
shp_merge_col = 'BLOCKID10'

# load shapefile and delete precinct column if it exists
ht.delete_cpg(shp_path)
df_shp = gpd.read_file(shp_path)
if 'precinct' in df_shp.columns:
    df_shp.drop(columns=['precinct'])
    
# left match precinct name on GEOID
df.index = pd.to_numeric(df.index)
df_shp[shp_merge_col] = pd.to_numeric(df_shp[shp_merge_col])
df_shp = df_shp.merge(df, how='left', left_on=shp_merge_col, right_on='GEOID')

# Assign NaN values to None
df_shp = df_shp.where((pd.notnull(df_shp)), None)

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



# get rook contiguity

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

# Save census block shapefile
block_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_block_smooth_perimeters.shp"
prec_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_precinct_smooth_perimeters.shp"

# generate precinct shapefile and save
ht.majority_areal_interpolation(local, block_path, prec_path, 'precinct')  

# 
df = majority_areal_interpolation(df, df_prec, [('precinct', 'precinct', 0)])
    

# Assign precincts to census blocks. Save precinct names for GIS
df_prec['precinct_id'] = df_prec['precinct']
df_prec = df_prec.set_index('precinct_id')
df_shp = assign_blocks(df_shp, df_prec, 'precinct')

# Save shapefiles
ht.save_shapefile(df, block_path, ['neighbors'])
ht.save_shapefile(df_prec, prec_path, ['neighbors'])
