"""
Helper methods to make cumbersome file management tasks easier
"""

import os
import geopandas as gpd
import datetime


def set_CRS(gdf, new_crs='epsg:4269'):
    ''' This function will set a coordinate reference system (CRS) for a
    geodataframe.

    Arguments:
        gdf:
            This is the geodataframe that we are converting to a different
            coordinate reference systems

        new_crs:
            This is the CRS we are converting to. This is usually in the
            form epsg:####

    Output:
        geodataframe with a converted CRS
    '''

    # If no CRS set, set it with .crs
    if gdf.crs == {}:
        gdf.crs = {'init': new_crs}
    # Transform CRS
    else:
        gdf = gdf.to_crs({'init': new_crs})
    return gdf


def delete_cpg(path):
    '''Deletes the CPG with a corresponding SHP. ArcGIS sometimes incorrectly
    encodes a shapefile and incorrectly saves the CPG. Before running most
    of the scripts, it is beneficially to ensure an encoding error does throw
    an error.

    Argument:
        path:
            path to a file that has the same name as the .cpg file. Usually
            the shapefile
    '''

    cpg_path = '.'.join(path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)


def load_shapefile(file_path):
    '''Loads shapefile given a path. Also deletes the CPG file to ensure an
    encoding error is not raised

    Argument:
        file_path:
            path to .shp file to load

    Output:
        df:
            geodataframe that is being loaded
    '''
    delete_cpg(file_path)
    return gpd.read_file(file_path)


def save_shapefile(df, file_path, cols_to_exclude=[]):
    ''' Saves a geodataframe to shapefile, deletes columns specified by user.
    If the path already exists a backup will be created in the path ./Backup/

    Arguments:
        df:
            geodataframe to be written to file

        file_str:
            string file path

        cols_to_exclude:
            columns from df to be excluded from attribute table
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
        except Exception:
            pass

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
