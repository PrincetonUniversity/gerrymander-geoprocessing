"""
Helper methods to make cumbersome file management tasks easier
"""

import os
import geopandas as gpd
import pandas as pd
import datetime

# import helper tools as if running from parent directory
from helper_tools.shp_manipulation import set_CRS
from helper_tools.basic import delete_cpg


def load_shapefile(file_path):
    '''Loads shapefile given a path. Also deletes the CPG file to ensure an
    encoding error is not raised

    Argument:
        file_path: path to .shp file to load

    Output:
        df: geodataframe that is being loaded
    '''
    delete_cpg(file_path)
    return gpd.read_file(file_path)

        
def save_shapefile(df, file_path, cols_to_exclude=[]):
    ''' Saves a geodataframe to shapefile, deletes columns specified by user.
    If the path already exists a backup will be created in the path ./Backup/
    
    Arguments:
        df: geodataframe to be written to file
        file_str: string file path
        cols_to_exclude: columns from df to be excluded from attribute table
            (possibly because it cannot be written, like an array)
    '''
    # make temporary dataframe so we can exclude columns
    actual_cols_to_exclude = []
    
    # Check to make sure drop columns are in dataframe
    for elem in cols_to_exclude:
        if elem in df.columns:
            actual_cols_to_exclude.append(elem)

    # Ensure geometry column is not being dropped
    if 'geometry' in actual_cols_to_exclude:
        actual_cols_to_exclude.remove('geometry')
            
    df = df.drop(columns=actual_cols_to_exclude)

    # Add Coordinate Reference System if one does not already exist
    if df.crs == {}:
        df = set_CRS(df)
    
    # Attempt to fix object types in dataframe by converting to float if
    # possible
    for col in df.columns:
        try:
            df[col] = df[col].astype(float)
        except:
            continue

    # Create backup if path already exists
    if os.path.exists(file_path):
        backup_dir = '/'.join(file_path.split('/')[:-1]) + '/Backup'

        # Create backup folder if it does not already exist
        if not os.path.exists(backup_dir):
            os.mkdir(backup_dir)

        # Get current date
        t = datetime.datetime.now()
        d = str(t.month) + '-' + str(t.day) + '-' + str(t.year) + '_' + \
            str(t.hour) + '-' + str(t.minute)        
        
        # Save old file to backup folder
        filename = file_path.split('/')[-1]
        file_no_ext = '.'.join(filename.split('.')[:-1])
        file_ext = filename.split('.')[-1]
        backup_path = backup_dir + '/' + file_no_ext + '_' + d + '.' + file_ext
        
        # load in backup dataframe
        delete_cpg(file_path)
        backup_df = gpd.read_file(file_path)
        backup_df.to_file(backup_path)
        
        # Save the new file to the folder
        df.to_file(file_path)

    # Save file if the file does not already exist
    else:
        df.to_file(file_path)
    
def default_path(path, local, direc_path):
    '''If the path is a keyword, the path to a designated shapefile will be
    returned. The possible default keywords are census_block, precinct,
    precinct_final
    
    Arguments:
        path: current path to the shapefile. Might be a default keyword
        local: name of the locality, which will be the parent directory
        direc_path: directory path to all of the locality folders
        
    Output:
        Path to a default file or the original file path
    '''
    
    if path == 'census_block':
        filename = local + '_census_block.shp'
        filename = filename.replace(' ', '_')
        path = direc_path + '/' + local + '/' + filename
                        
    if path == 'precinct':
        filename = local + '_precincts.shp'
        filename = filename.replace(' ', '_')
        path = direc_path + '/' + local + '/' + filename
        
    if path == 'precinct_final':
        filename = local + '_precincts_final.shp'
        filename = filename.replace(' ', '_')
        path = direc_path + '/' + local + '/' + filename
        
    if path == 'bounding_frame':
        filename = local + '_bounding_frame.shp'
        filename = filename.replace(' ', '_')
        path = direc_path + '/' + local + '/' + filename
        
    if path == 'census_block_removed':
        filename = local + '_census_block_removed.shp'
        filename = filename.replace(' ', '_')
        path = direc_path + '/' + local + '/' + filename

    return path

def read_one_csv_elem(csv_path, row=0, col=1):
    ''' This function will return one element of the csv
    
    Arguments:
        csv_path: path to read in the csv_file
        row: row of the text to read in
        col: col of the text to read in
    
    Output:
        Desired element in the csv
    '''
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    return data[row][col]

def read_csv_to_df(csv_path, head, col_names, list_cols):
    ''' Read in a csv for batching for other processes
    
    Arguments:
        csv_path: path to read in the csv file
        head: the header row to read in the csv as a pandas df
        col_names: list column names in order as headers for the pandas df
        list_cols: columns to convert to lists from comma delimited strings
    
    Output:
        The csv dataframe to run batching process through
    '''
    # Read in csv as df
    csv_df = pd.read_csv(csv_path, header=head, names=col_names)
    
    # Convert comma delimited string columns to lists
    for col in list_cols:
        if col in col_names:
            csv_df[col] = csv_df[col].str.split(',')
            
    return csv_df