'''
Dissolve boundaries for shapefile(s) according to a given attribute. we will
also check for contiguity after boundaries have been dissolved.

Can perform for a batch
'''
import os, sys
os.chdir('..')
sys.path.append(os.getcwd())

import pandas as pd
import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm
import os.path
import sys

# Get path to our CSV file
csv_path = ""

# Check if csv path has been entered in command line argument
if len(sys.argv) > 1:
    # If file exists then make the csv_path the second argument
    if os.path.isfile(sys.argv[1]):
        csv_path = sys.argv[1]
        print('\nUsing command argument as csv path')
    else:
        print('\nCSV path entered does not exist. Exiting.')
        sys.exit()

# Import CSV elements into dataframe
csv_col = ['Locality', 'In_Path', 'Out_Path', 'Dissolve_Attribute']
csv_list = []
csv_df = fm.read_csv_to_df(csv_path, 0, csv_col, csv_list)

# Dissolve boundaries for each locality in the batch
for i, row in csv_df.iterrows():
    
    # Create shapefile out of precincts
    try:
        
        # Print Locality Name to see batch progress
        print('\n' + row['Locality'])

        # load and dissolve shapefile
        geo_df = load_shapefile(row['In_Path'])
        geo_df = sm.dissolve(geo_df, row['Dissolve_Attribute'])

        # Print potential errors
        sc.check_contiguity_and_contained(geo_df, row['Dissolve_Attribute'])

        # Save shapefile
        fm.save_shapefile(geo_df, row['Out_Path'])
        
    # Shapefile creation failed
    except Exception as e:
        print(e)
        print('ERROR:' + row['Locality'])

