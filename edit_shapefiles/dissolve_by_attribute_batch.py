'''
Dissolve boundaries for shapefile(s) according to a given attribute. we will
also check for contiguity after boundaries have been dissolved.

Can perform for a batch
'''

import pandas as pd
import shapefile_manipulation as sm
import shapefile_calculations as sc
import file_management as fm
import os.path
import sys

# Get path to our CSV file
csv_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/CSV/Blocks to Precincts/ blocks_to_precincts_02_08.csv"

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
csv_df = ht.read_csv_to_df(csv_path, 0, csv_col, csv_list)

# Dissolve boundaries for each locality in the batch
for i, row in csv_df.iterrows():
    
    # Create shapefile out of precincts
    try:
        
        # Print Locality Name to see batch progress
        print('\n' + row['Locality'])
        
        # Generate dissolved shapefile
        geo_df = sm.dissolve(row['In_Path'], row['Dissolve_Attribute'])

        # Check for noncontiguous and contained geometries
        sc.check_contiguity_and_contained(geo_df, row['Dissolve_Attribute'])

        # Save shapefile
        fm.save_shapefile(geo_df, row['Out_Path'])
        
    # Shapefile creation failed
    except Exception as e:
        print(e)
        print('ERROR:' + row['Locality'])

