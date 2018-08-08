import pandas as pd
import pysal as ps
import numpy as np
import geopandas as gpd
import shapely as shp
import operator
import os
import csv
import shutil
import time

def main():
    # Get path to our CSV file
    csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Areal Interpolation/Areal Interpolate CSV/interpolate_Aug_7_debug.csv"
    
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        
        # Import table from CSV into pandas dataframe
        csv_df_names = ['locality', 'out_df path', 'out_df cols', \
                        'in_df path', 'in_df cols']
        csv_df = pd.read_csv(csv_path, header=0, names=csv_df_names)
        
        # Adjust strings delimited by commas into lists
        list_col = ['out_df cols', 'in_df cols']
        for col in list_col:
            csv_df[col] = csv_df[col].str.split(',')
            
        # Iterate through all of the interpolations
        for i, _ in csv_df.iterrows():
            
            print(csv_df.at[i, 'locality'])
            try: 
                # Check runtime
                start = time.time()
                
                # Set adjust cols
                adjust_cols = []
                in_cols = csv_df.at[i, 'in_df cols']
                out_cols = csv_df.at[i, 'out_df cols']
                
                if len(in_cols) != len(out_cols):
                    raise Exception('# of in and out cols are unequal')
            
                for ix, elem in enumerate(out_cols):
                    adjust_cols.append((elem, in_cols[ix]))
                    
                # set paths
                out_path = csv_df.at[i, 'out_df path']
                in_path = csv_df.at[i, 'in_df path']
                
                # Delete CPG files. Throws incorrect encoding error due to 
                # ArcGIS incorrectly writing the encoding type
                cpg_path_out = ''.join(out_path.split('.')[:-1]) + '.cpg'
                if os.path.exists(cpg_path_out):
                    os.remove(cpg_path_out)
                    
                cpg_path_in = ''.join(in_path.split('.')[:-1]) + '.cpg'
                if os.path.exists(cpg_path_in):
                    os.remove(cpg_path_in)
                
                print('BEFORE')
                
                # run majority areal interpolation
                new_df_out = majority_areal_interpolation(out_path, in_path, \
                                                          adjust_cols)
                
                
                print('HERE')
                new_cols = new_df_out.columns
                print(new_cols)
                print('New Cols')
                #print(new_cols)
                for col in new_cols:
                    new_df_out[col] = new_df_out[col].astype(str)
                    print(col)
                    print(new_df_out[col].dtype)
                    
                print('Change Column Types')
                # save new out dataframe
                
                new_df_out.to_file(out_path)
                
                # print runtime
                print(time.time() - start)
                
            except Exception as e:
                print('exception')
                print(e)

    # CSV file could not be read in or exported
    except:
        print('ERROR: Reading in CSV file')
        
def majority_areal_interpolation(out_df_path, in_df_path, adjust_cols):
    ''' Perform majority area areal interpolation on two dataframes. Returns
    the modified dataframe (out_df)
    
    Arguments:
        out_df_path: path to the shapefile containing the dataframe to be 
        modified
        in_df_path: path to the shapefile used to modify out_df
        adjust_cols: list of tuples that determine which df_out columns are
        set equal to which df_in cols. [(df_out_col1, df_in_col1),
        (df_out_col2, df_in_col2),...]'''
    print('IN HERE')
    # Read in input dataframe
    df_in = gpd.read_file(in_df_path)
    df_in.index = df_in.index.astype(int)
    print('AFTER INDEX')
    # Read in output dataframe
    print(out_df_path)
    df_out = gpd.read_file(out_df_path)
    print('AFTER READ')
    # Create necessary output columns in the out_df
    df_out_cols = list(df_out.columns)
    for tup in adjust_cols:
        if tup[0] not in df_out_cols:
            df_out[tup[0]] = pd.Series(dtype=object)
    
    # construct r-tree spatial index. Creates minimum bounding rectangle about
    # each geometry in df_in
    si = df_in.sindex
    
    
    # iterate through every geometry in the out_df to match with in_df and set
    # target values
    for i, _ in df_out.iterrows():
    
        # initialize current element's geometry and check which for minimum
        # bounding rectangle intersections
        df_out_elem_geom = df_out.at[i, 'geometry']
        poss_df_in_elem = [df_in.index[i] for i in \
                      list(si.intersection(df_out_elem_geom.bounds))]
        
        # If precinct's MBR only in_df geometry. Set it equal
        if len(poss_df_in_elem) == 1:
            df_in_elem = poss_df_in_elem[0]
        else:
            # for cases with multiple matches, compare fractional area
            frac_area = {}
            found_majority = False
            for j in poss_df_in_elem:
                if not found_majority:
                    area = df_in.at[j, 'geometry'].intersection(\
                                   df_out_elem_geom).area / \
                                   df_out_elem_geom.area
                    # Majority area means, we can assign
                    if area > .5:
                        found_majority = True
                    frac_area[j] = area
            #print(i)
            #print(frac_area)
            df_in_elem = max(frac_area.items(), key=operator.itemgetter(1))[0]
    
        # Set corresponding df_out values to df_in values if the column exist
        # in in_df
        df_in_cols = df_in.columns
        for tup in adjust_cols:
            if tup[1] in df_in_cols:
                df_out.at[i, tup[0]] = df_in.at[df_in_elem, tup[1]]
        
    print('Finish')
    # Return output dataframe
    return df_out

if __name__ == '__main__':
    main()