# -*- coding: utf-8 -*-
"""
Created on Wed Aug  8 15:54:21 2018

@author: Jacob
"""

import geopandas as gpd
import pandas as pd
import csv
import os

def main():
    csv_path = 'G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/num_precincts_received_shapefiles.csv'
    compare_election_results_to_shapefiles(csv_path)
    
def get_num_attributes_from_shp(path):
    # Delete CPG file if it exists
    cpg_path = ''.join(path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)
        
    df = gpd.read_file(path)
    return len(df)

def compare_election_results_to_shapefiles(csv_path):
    
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        # Import Google Drive path
        with open(csv_path) as f:
            reader = csv.reader(f)
            data = [r for r in reader]
        direc_path = data[0][1]
    
        # Import table from CSV into pandas dataframe
        name_list = ['Locality', 'Num Precincts', 'Filename']
        in_df = pd.read_csv(csv_path, header=1, names=name_list)
    

        # Iterate through each county we are creating a shapefile for
        for i, _ in in_df.iterrows():
            locality = in_df.at[i, 'Locality']
            path = direc_path + '/' + locality +'/' + in_df.at[i, 'Filename']
            num_precincts = in_df.at[i, 'Num Precincts']
            num_precincts_shp = get_num_attributes_from_shp(path)
            if (num_precincts != num_precincts_shp):
                print (locality + ' has ' + str(num_precincts) + ' precincts '\
                       'in the election results but ' + str(num_precincts_shp)\
                       + ' attributes in the shapefile.')
                
    # CSV file could not be read in or exported
    except:
        print('ERROR')
        
if __name__ == '__main__':
    main()