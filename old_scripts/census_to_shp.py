import time
import pandas as pd
import geopandas as gpd
import math
import censusbatchgeocoder
import shapely as shp
import warnings
warnings.filterwarnings("ignore")
import helper_tools as ht

counties = ['Barbour',
 'Berkeley',
 'Boone',
 'Braxton',
 'Brooke',
 'Cabell',
 'Calhoun',
 'Clay',
 'Doddridge',
 'Fayette',
 'Gilmer',
 'Grant',
 'Greenbrier',
 'Hampshire',
 'Hancock',
 'Hardy',
 'Harrison',
 'Jackson',
 'Jefferson',
 'Kanawha',
 'Lewis',
 'Lincoln',
 'Logan',
 'Marion',
 'Marshall',
 'Mason',
 'McDowell',
 'Mercer',
 'Mineral',
 'Mingo',
 'Monongalia',
 'Monroe',
 'Morgan',
 'Nicholas',
 'Ohio',
 'Pendleton',
 'Pleasants',
 'Pocahontas',
 'Preston',
 'Putnam',
 'Raleigh',
 'Randolph',
 'Ritchie',
 'Roane',
 'Summers',
 'Taylor',
 'Tucker',
 'Tyler',
 'Upshur',
 'Wayne',
 'Webster',
 'Wetzel',
 'Wirt',
 'Wood',
 'Wyoming']

for cty in counties:
    # get census block shapefile and col to merge on
    shp_path = "G:/My Drive/WV/" + cty + " County/" + cty + "_County_census_blocks.shp"
    shp_merge_col = 'BLOCKID10'
    
    # Save census block shapefile
    block_path = "G:/My Drive/WV/" + cty + " County/" + cty + "_County_census_blocks_precincts_assigned.shp"
    prec_path = "G:/My Drive/WV/" + cty + " County/" + cty + "_County_precincts.shp"
    
    # Convert geocoded dataframe into our desired geodataframe
    geo_path = "G:/My Drive/WV/" + cty + " County/census_" + cty + ".csv"
    df_geo = pd.read_csv(geo_path, header=0)
    
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
    
    # Split noncontiguous precincts
    df_prec = ht.split_noncontiguous(df_prec)
    
    # Merge precincts fully contained in other precincts
    df_prec = ht.merge_fully_contained(df_prec)
    
    # Save precinct assignments down to the block
    df = ht.interpolate_label(df, df_prec, [('precinct', 'precinct', 0)], label_type='greatest area')
    
    # Save shapefiles
    ht.save_shapefile(df, block_path, ['neighbors'])
    ht.save_shapefile(df_prec, prec_path, ['neighbors'])
