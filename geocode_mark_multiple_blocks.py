import time
import pandas as pd
import geopandas as gpd
import shapely as shp
import warnings
warnings.filterwarnings("ignore")
import helper_tools as ht

#counties = ['Barbour', 'Berkeley']

counties = ['Vinton']


for cty in counties:
    # get census block shapefile and col to merge on
    shp_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/Precinct Data/Vinton County/Vinton_County_census_block.shp"
    shp_merge_col = 'BLOCKID10'
    
    # Save census block shapefile
    block_path = "./Vinton_County_census_block_precincts_assigned.shp"
    prec_path = "./Vinton_County_precincts.shp"
    
    # Convert geocoded dataframe into our desired geodataframe
    geo_path = "/Users/jessicanyquist/Desktop/gerrymander-geoprocessing/output_1.csv"
    df_geo = pd.read_csv(geo_path, header=0)
    
    # Only keep rows that matches were found
    df_geo = df_geo[df_geo['is_match'] == 'Match']
    
    # create cenus block geoid
    df_geo['GEOID'] = df_geo['state_fips'].astype(int).map(str).str.zfill(2) + \
                        df_geo['county_fips'].astype(int).map(str).str.zfill(3) + \
                        df_geo['tract'].astype(int).map(str).str.zfill(6) + \
                        df_geo['block'].astype(int).map(str).str.zfill(4)
                        


    # drop unnecessary columns from df_geo and df_raw
    geo_drop_cols = ['address', 'city', 'state', 'zipcode', 'geocoded_address', \
                     'is_match', 'is_exact', 'returned_address', 'coordinates', \
                     'tiger_line', 'side', 'state_fips', 'county_fips', 'tract', \
                     'block', 'latitude', 'longitude', 'id']
    
    # create dataframe by dropping unnecessary columns in df_geo dataframe
    # df just has the GEOID and the most common precinct
    df = df_geo.drop(columns=geo_drop_cols)
 
    # record the number of each precinct in each census block
    precincts = list(set(df['precinct']))
    blocks = list(set(df['GEOID']))
    count_df = pd.DataFrame(columns = precincts)
    count_df['blocksID'] = blocks
    count_df[:] = 0
    count_df['blocksID'] = blocks

    # tally number of voters in each block in each precinct
    for x in df.index:
        block = df.at[x,'GEOID']
        precinct = df.at[x,'precinct']
        block_index = int(count_df[count_df['blocksID']==block].index[0])
        col_index = count_df.columns.get_loc(precinct)
        count_df.iloc[block_index, col_index]= count_df.iloc[block_index, col_index] + 1
    
    # create new dataframe with top 3 precinct matches per census block
    columns = ['blockID','Precinct_1', 'percent_1','Precinct_2', 'percent_2','Precinct_3', 'percent_3']
    top_df = pd.DataFrame(columns = columns)
    top_df['blockID'] = blocks
    top_df.blockID = top_df.blockID.astype(float)
    # for each census block, record the top three counting precincts
    for x in top_df.index:
        top_df.loc[x,'blockID'] = blocks[x]
        total = count_df.sum(axis = 1)[x]
        max = count_df.max(axis = 1)[x]
        length = len(precincts)
        # find the precinct with this max value
        for i in range(0,length):
            if count_df.iloc[x,i] == max:
                column_match = i
        top_df.loc[x,'Precinct_1'] = precincts[column_match]
        top_df.loc[x,'percent_1'] = max/total
        # remove this max column from the dataframe, find the new max
        small_df = count_df.drop(count_df.columns[column_match], axis=1)
        max = small_df.max(axis = 1)[x]
        # if there is a second precinct with 1 or more values
        if max != 0:
            for i in range(0,length - 1):
                if small_df.iloc[x,i] == max:
                    column_match2 = i
            top_df.loc[x,'Precinct_2'] = precincts[column_match2]
            top_df.loc[x,'percent_2'] = max/total
            small_df = small_df.drop(small_df.columns[column_match2], axis=1)
        max = small_df.max(axis = 1)[x]
        # if there is a third precinct with 1 or more values
        if max != 0:
            print(len(small_df.columns))
            print(max)
            for i in range(0,length - 2):
                if small_df.iloc[x,i] == max:
                    column_match3 = i
            top_df.loc[x,'Precinct_3'] = precincts[column_match3]
            top_df.loc[x,'percent_3'] = max/total
    
        
    

    df = df.groupby(['GEOID']).agg(lambda x:x.value_counts().index[0])
    
    
    

    print('CPG')
    # load shapefile and delete precinct column if it exists
    ht.delete_cpg(shp_path)
    df_shp = gpd.read_file(shp_path)
    if 'precinct' in df_shp.columns:
        df_shp.drop(columns=['precinct'])
        
    
    # left match precinct name on GEOID
    df.index = pd.to_numeric(df.index)
    df_shp[shp_merge_col] = pd.to_numeric(df_shp[shp_merge_col])
    df_shp = df_shp.merge(df, how='left', left_on=shp_merge_col, right_on='GEOID')
    print('left_match')
    # Assign NaN values to None
    df_shp = df_shp.where((pd.notnull(df_shp)), None)



    
    # Save original merge precincts
    df_shp['orig_prec'] = df_shp['precinct']
    
    # Get unique values
    prec_name = list(set(df_shp['precinct']))
    

    
    # Replace None precinct with a unique character
    for i, _ in df_shp.iterrows():
        # replace None with a unique character
        if df_shp.at[i, 'precinct'] == None:
            df_shp.at[i, 'precinct'] = 'None_' + str(i)
     
            
    print('Replace None')
    # Get unique values
    prec_name = list(set(df_shp['precinct']))
    
    # Initalize precinct dataframe
    df_prec = gpd.GeoDataFrame(columns=['precinct','geometry'],geometry='geometry')
    print(df_prec.columns)
    
    

    
    # Iterate through all of the precinct IDs and set geometry for df_prec
    for i, elem in enumerate(prec_name):
        df_poly = df_shp[df_shp['precinct'] == elem]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'precinct'] = elem
    

    start_combine =  time.time()
    
    print('Precinct Manipulation')
    # reset index
    df_prec = df_prec.reset_index(drop=True)
    
    # get rook contiguity and calculate shared perims
    df_prec = ht.get_shared_perims(df_prec)
    print('Shared Perims')
    # get list of precinct indexes to merge
    precincts_to_merge = []
    for i, _ in df_prec.iterrows():
        if df_prec.at[i, 'precinct'].split('_')[0] == 'None':
            precincts_to_merge.append(i)
            
    # merge geometries
    df_prec = ht.merge_geometries(df_prec, precincts_to_merge)
    print('Merge Geometries')
    # Split noncontiguous precincts
    #df_prec = ht.split_noncontiguous(df_prec)
    print('Noncontiguous')
    # Merge precincts fully contained in other precincts
    #df_prec = ht.merge_fully_contained(df_prec)
    print('fully contained')
    df = gpd.read_file(shp_path)
    # Save precinct assignments down to the block
    df = ht.interpolate_label(df, df_prec, [('precinct', 'precinct', 0)], label_type='greatest area')
    print('interpolate')
    # add precinct columns to dataframe
    top_df['blockID'] = pd.to_numeric(top_df['blockID'])
    df['BLOCKID10'] = pd.to_numeric(df['BLOCKID10'], downcast = 'integer')
    df = df.merge(top_df, how='left', left_on='BLOCKID10', right_on='blockID')
    # Save shapefiles
    ht.save_shapefile(df, block_path, ['neighbors'])
    #ht.save_shapefile(df_prec, prec_path, ['neighbors'])

    print('HERE')
