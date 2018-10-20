import pandas as pd
import geopandas as gpd
import os
import helper_tools as ht

# Define paths
county_fips_path = '/Users/hwheelen/Desktop/OH/national_county_fips.txt'

#census_shape_folder = '/Users/hwheelen/Documents/GitHub/ohio-precincts/shp/'

# Select state
state = 'OH'

# Define census name and path
#census_filename = '/precincts_results.shp'
census_shape_path = '/Users/hwheelen/Documents/GitHub/ohio-precincts/shp/precincts_results.shp'

# Define path to parent directory of locality folders
state_shape_folder = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Virginia precincts"

# Delete CPG file
ht.delete_cpg(census_shape_path)

no_pickle = 0

#%% THIS TAKES REALLY LONG. Should Be able to skip once pickle file is saved
# Import census state file and save to pickle
if no_pickle:
    print('Load Full')
    df = gpd.read_file(census_shape_path)
    print('Finished Load Full')
    df.to_pickle(census_shape_folder + state + '/census_df.pkl')

#%% This also only takes kinda long

# Read in df and make county fips an int
if not no_pickle:
    print('Load Pickle')
    df = pd.read_pickle(census_shape_folder + state + '/census_df.pkl')
    print('Finished Load Pickle')

#%%
df['COUNTYFP10'] = df['COUNTYFP10'].apply(int)

# Read in text file for fips codes
col_names = ['state', 'state_fips', 'county_fips', 'locality', 'H']
csv_df = pd.read_csv(county_fips_path, names=col_names)

# Delete unnecessary column from county fips file
csv_df = csv_df.drop(columns=['H'])

# Reduce dataframe to the selected state
csv_df = csv_df[csv_df['state'] == state]

# Set index into locality
csv_df = csv_df.set_index('locality')

# Get the names of all of the folders in a list in order
folder_names = os.listdir(state_shape_folder)
folder_names.sort()
locality_names = list(csv_df.index)

# Create booleans to determine whether to add every shapefile or certain ones
convert_every_locality = False
convert_list_locality = True

# List of localities to convert if convert_list_locality is True
localities_to_convert =  ['Fairfax City']

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
    num_to_convert = len(csv_df)
    # Check that every folder has a corresponding fips match
    if num_to_convert == folder_count:
        # Iterate through every locality
        for local in folder_names:
            # track the locality being created
            print(local)
            
            # Obtain FIPS code
            fips = csv_df.at[local, 'county_fips']
            
            # Save county shapefile
            df_county = df[df['COUNTYFP10'] == fips]
            df_county = gpd.GeoDataFrame(df_county, geometry='geometry')
            name = local + ' census block'
            name = name.replace(' ', '_')
            out_path = state_shape_folder + '/' + local + '/' + name + '.shp'
            ht.save_shapefile(df_county, out_path)
            
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
            print(local)
            
            # Obtain FIPS code
            fips = csv_df.at[local, 'county_fips']
        
            # Save county shapefile
            df_county = df[df['COUNTYFP10'] == fips]
            df_county = gpd.GeoDataFrame(df_county, geometry='geometry')
            name = local + ' census block'
            name = name.replace(' ', '_')
            out_path = state_shape_folder + '/' + local + '/' + name + '.shp'
            
            ht.save_shapefile(df_county, out_path)
            
    else:
        print('\nChange FIPS text file to match folders in convert list')
        print(list_missing)