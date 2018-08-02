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

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/CSV/Freehand_Conversion_Digitization_Russell.csv"

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
    print ('saved')
    
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
    df = real_rook_contiguity(df)
    

    ###########################################################################
    ###### SETTING PRECINCT IDs ###############################################
    ###########################################################################
    
    # Initialize List to all elements with an ID
    prec_set_list = list(df[df['ID'] != None].index)
    
    # Iterate until every census block has an ID
    while len(prec_set_list) > 0:
        
        # Initialize new prec_set_list to be empty
        prec_set_list_new = []
        
        # Loop through the current prec_set_list of assigned census blocks
        for i in prec_set_list:
            # Iterate through the neighbors of the current census block
            
            # Get neighbors with an ID equal to None
            nb_idnone = [j for j in  df.at[i, 'neighbors'] if \
                         df.at[j, 'ID'] == None]
            
            #  Get ID of census block i and set unassigned neighbors to this 
            # value
            i_id = df.at[i, 'ID']
            for k in nb_idnone:
                df.at[k, 'ID'] = i_id
        
            # Add these elements to the new queue
            prec_set_list_new += nb_idnone
            
        # set new prec_set_list
        prec_set_list = prec_set_list_new
        
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
    save_shapefiles(df, df_prec, shape_path,\
                    out_folder + '/' + out_name + 'after_assignment' + '.shp' )
        
    ###########################################################################
    ###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)#######################
    ###########################################################################
    
    # Initialize indexes to drop
    drop_ix = []
    
    # Iterate through every precinct
    for i, _ in df_prec.iterrows():
        # Check if it precinct is a MultiPolygon
        if df_prec.at[i, 'geometry'].type == 'MultiPolygon':
            # Add index as the index of a row to be dropped
            drop_ix.append(i)
            
            # get shape and area of current precinct
            precinct = df_prec.at[i, 'geometry']
    
            # Iterate through every contiguous region in the precinct
            for region in precinct.geoms:
                # Set geometry and id of new_shape
                d = {}
                d['geometry'] = region
                df_prec = df_prec.append(d, ignore_index=True)
                
    # Remove original noncontiguous precincts
    df_prec = df_prec.drop(drop_ix)
    
    save_shapefiles(df, df_prec, shape_path,\
                    out_folder + '/' + out_name + 'after_noncontig' + '.shp' )
    
    ###########################################################################
    ###### MERGE PRECINCTS FULLY CONTAINED IN OTHER PRECINCTS #################
    ###########################################################################
    df_prec = real_rook_contiguity(df_prec)

    # Multiple Contained Precincts Check
    # Create list of rows to drop at the end of the multiple contained check
    ids_to_drop = []
    
    # Iterate over all precincts
    for i,_ in df_prec.iterrows():
        
        # Create polygon Poly for this precinct from its exterior coordinates. 
        # This polygon is currently without an interior. The purpose of filling
        # the interior is to allow for an intersection to see if a neighbor is
        # fully contained
        
        geometry = df_prec.at[i, 'geometry']
        
        if geometry.type == 'Polygon':
            poly_coords = list(geometry.exterior.coords)
            poly = Polygon(poly_coords)
        else:
            print('Geometry is not a polygon during contained precincts check')

        # Create list of contained neighbor id's to delete
        nb_ix_del = []
    
        # Define a list that contains possibly contained precincts. If a 
        # precinct is nested witin other contained precincts, we will need to 
        # add it to this list
        possibly_contained = df_prec.at[i, 'neighbors']
        for j in possibly_contained:        
            
            # Check if the intersection of Poly (precint i's full polygon) and 
            # the current neighbor is equal to the current neighbor. This 
            # demonstrates that the current neighbor is fully contained within 
            # precinct i
            j_geom = df_prec.at[j, 'geometry']
            
            if j_geom == j_geom.intersection(poly):
                # j is fully contained within i. To account for nested 
                # precincts we append any neighbor of j that is not already in 
                # possibly_contained not including i
                for j_nb in df_prec.at[j, 'neighbors']:
                    if j_nb not in possibly_contained and j_nb != i:
                        possibly_contained.append(j_nb)
    
                # Add geometry of j to geometry of i
                polys = [df_prec.at[i, 'geometry'], 
                         df_prec.at[j, 'geometry']]
                df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
                            
                # add neighbor reference from precinct i to delete if a nb
                if j in df_prec.at[i, 'neighbors']:
                    nb_ix = df_prec.at[i, 'neighbors'].index(j)
                    nb_ix_del.append(nb_ix)
                
                # add neighbor precinct to the ID's to be dropped
                ids_to_drop.append(j)
                
        # Delete neighbor references from precinct i
        if len(nb_ix_del) > 0:
            # iterate through ixs in reverse to prevent errors through deletion
            for nb_ix in reversed(nb_ix_del):
                del(df_prec.at[i, 'neighbors'][nb_ix])
    
    # Drop contained precincts from the dataframe
    df_prec = df_prec.drop(ids_to_drop)
    
    save_shapefiles(df, df_prec, shape_path,\
                    out_folder + '/' + out_name + 'after_merge_contained' + '.shp' )

    ###########################################################################
    ###### MERGE PRECINCTS UNTIL WE HAVE THE RIGHT NUMBER #####################
    ###########################################################################

    # reset index for df_prec
    df_prec = df_prec.reset_index(drop=True)
    
    # Get rook contiguity through a dictionary and calculate the shared_perims
    df_prec = real_rook_contiguity(df_prec, 'dict')
    
    df_prec.to_pickle(out_folder + '/before_shared_perims.pkl')
    df_prec = get_shared_perims(df_prec)
    
    # get list of precinct indices to keep
    for i, _ in df_prec.iterrows():
        df_prec.at[i, 'area'] = df_prec.at[i, 'geometry'].area
    arr = np.array(df_prec['area'])
    precincts_to_merge = arr.argsort()[ : -num_regions]
    
    print (precincts_to_merge)
    # Iterate through indexes of small "fake" precincts
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
        for key in cur_prec:
            df_prec.at[key, 'neighbors'].pop(i)
            
            ##-----------------------------------------------------------------
            # get perimeter length for key in merge and set in 
            # neighbor list
            key_dist = df_prec.at[ix, 'neighbors'][key]
            df_prec.at[key, 'neighbors'][ix] = key_dist
            
    # delete current precinct
    df_prec = df_prec.drop(precincts_to_merge)
        
    # Set precinct values to be between 0 and num_regions - 1
    df_prec = df_prec.reset_index(drop=True)

    # set region values
    for i in range(len(df_prec)):
        df_prec.at[i, 'region'] = i

    ###########################################################################
    ###### Assign Census Blocks to Regions ####################################
    ###########################################################################
    
    df = assign_blocks_to_regions(df, df_prec)
    
    ###########################################################################
    ###### Save Shapefiles ####################################################
    ###########################################################################
    
    out_name = local + '_precincts'
    out_name.replace(' ', '_')
    
    return save_shapefiles(df, df_prec, shape_path,\
                    out_folder + '/' + out_name + '.shp' )
            
if __name__ == '__main__':
    main()