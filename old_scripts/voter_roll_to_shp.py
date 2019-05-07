import time
import pandas as pd
import geopandas as gpd
import math
import censusbatchgeocoder
import shapely as shp
import warnings
warnings.filterwarnings("ignore")
import helper_tools as ht

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
    if df_prec.at[i, 'precinct'].split('_')[0] == 'None':
        precincts_to_merge.append(i)
        
# merge geometries
df_prec = ht.merge_geometries(df_prec, precincts_to_merge)

# Save census block shapefile
block_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_block_smooth_perimeters.shp"
prec_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/OH/Ohio Counties/Vinton County/Vinton_County_precinct_smooth_perimeters.shp"

# Save precinct assignments down to the block
df = ht.majority_areal_interpolation(df, df_prec, [('precinct', 'precinct', 0)])

# Save shapefiles
ht.save_shapefile(df, block_path, ['neighbors'])
ht.save_shapefile(df_prec, prec_path, ['neighbors'])
