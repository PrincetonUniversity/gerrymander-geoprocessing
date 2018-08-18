# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 11:19:58 2018

@author: conno
"""

import pandas as pd
import geopandas as gpd
import os
import csv

def join_list(l, delimiter):
    ''' Takes list and returns a string containing the elements of the list
    delimited by delimiter
    
    Arguments
    l: list of elements to combine into a string
    delimiter'''
    return delimiter.join(map(str, l))

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/match_prec_num_to_name.csv"

save_shp_bool = False
convert_float_to_int_bool = True
# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    
    # Import Google Drive path
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    direc_path = data[0][1]

    # Import table from CSV into pandas dataframe
    name_list = ['Locality Name', 'Path', 'Filename', 'Match Name', \
                 'Match Val', 'Append Name', 'Append Val', 'Merge Type']
    csv_df = pd.read_csv(csv_path, header=1, names=name_list)

    # Initialize out_df, which contains the results of the difference
    new_cols = ['Result', 'Locality Name', 'Notes']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Adjust strings delimited by commas into lists
    list_col = ['Match Val', 'Append Val']
    for col in list_col:
        csv_df[col] = csv_df[col].str.split(',')
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Convert CRS
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            
            # Get path
            path_shape = csv_df.at[i, 'Path']
            
            # Get path and split
            if path_shape == 1:
                path_shape = direc_path + '/' + local + '/' + \
                                csv_df.at[i, 'Filename']
                                                
            # Read in shapefile
            cpg_path = ''.join(path_shape.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path):
                os.remove(cpg_path)
            df = gpd.read_file(path_shape)

            # get match and append names. Get a copy so we can match our values
            # to a string type from the CSV. We will later delete the copy
            # after the merge. Define original name as it will be used to 
            # determine NaN values (see which values of Append Val did not
            # match)
            orig_match_name = csv_df.at[i, 'Match Name']
            match_name = orig_match_name + 'Copy'
            append_name = csv_df.at[i, 'Append Name']

            # create copy matching column and convert to a string type
            df[match_name] = df[csv_df.at[i, 'Match Name']]
            
            # Set up to merge on object
            if convert_float_to_int_bool:
                df[match_name] = df[match_name].astype(int, errors='ignore')
            df[match_name] = df[match_name].astype(str)
            
            # Create df to merge with
            df_dict = {}
            df_dict[match_name] = csv_df.at[i, 'Match Val']
            df_dict[append_name] = csv_df.at[i, 'Append Val']
            df_merge  = pd.DataFrame.from_dict(df_dict)
            
            # Get merge how and set to lowercase
            merge_how = csv_df.at[i, 'Merge Type'].lower()
            
            # save as old if append column is in df columns
            if append_name in list(df.columns):
                old_col_new_name = 'old_' + append_name
                df[old_col_new_name] = df[append_name]
                df = df.drop(columns=[append_name])

            # get wihch vales form the original dataframe did not find a match
            # (match_miss) and which values form the appended dataframe did
            # not find a match (append_miss)
            e_df = df.merge(df_merge, on=match_name, how='outer')
            match_miss = list(e_df[e_df[append_name].isnull()][match_name])
            
            if len(match_miss) == 0:
                match_miss_str = 'none'
            else:
                match_miss_str = join_list(match_miss, ',')

            append_miss = list(e_df[e_df[orig_match_name].isnull()\
                                    ][match_name])

            if len(append_miss) == 0:
                append_miss_str = 'none'
            else:
                append_miss_str = join_list(append_miss, ',')
            # Perform Merge. Delete copy column. Save
            if save_shp_bool:
                df = df.merge(df_merge, on=match_name, how=merge_how)
                df = df.drop(columns=[match_name])
                df.to_file(path_shape)

            # Place Results and Notes in out_df
            row = len(out_df)
            out_df.at[row, 'Result'] = 'SUCCESS'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            note = 'Values in original no match: ' + match_miss_str + \
                    '; Values in append no match: ' + append_miss_str
            out_df.at[row, 'Notes'] = note
        
        # Shapefile creation failed
        except Exception as e:
            print(e)
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Notes'] = 'Failed on ' + local

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
