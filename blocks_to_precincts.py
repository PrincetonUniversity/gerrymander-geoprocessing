import time
import pandas as pd
import helper_tools as ht
import os.path
import sys

# Get path to our CSV file
csv_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/blocks_to_precincts_10_24.csv"

# Check if the length is greater than 1
if len(sys.argv) > 1:
    # If file exists then make the csv_path the second argument
    if os.path.isfile(sys.argv[1]):
        csv_path = sys.argv[1]
        print('\nUsing command argument as csv path')
    else:
        print('\nTerminal argument does not exist. Exiting.')
        sys.exit()
        
# Initial try and except to catch improper csv_path or error exporting the
# results of the transfer
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['Locality', 'Census Path', 'Out Path', 'Precinct_Col']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)
    
    # Initialize out_df, which contains the batch output
    new_cols = ['Result', 'Time Taken', 'Num Census Blocks']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Iterate through each locality we are creating a shapefile for
    for i, _ in csv_df.iterrows():
        
        # Create shapefile out of precincts
        try:
            # Begin Start time
            start_time = time.time()
            
            # Set unique variables for the current county
            local = csv_df.at[i, 'Locality']
            prec_col = csv_df.at[i, 'Precinct_Col']
            # set census and out path
            census_path = ht.default_path(csv_df.at[i, 'Census Path'], \
                                          local, direc_path)
            out_path = ht.default_path(csv_df.at[i, 'Out Path'], local, \
                                       direc_path)
            
            # Print Locality Name to see where errors are from
            print('\n' + local)
            
            # Generate precinct shapefile and add corresponding precinct
            # index to the attribute field of the census block shapefile
            result = ht.generate_precinct_shp(local, census_path, out_path,\
                                              prec_col)
            
            # Batch output
            row = len(out_df)
            out_df.at[row, 'Result'] = 'SUCCESS'
            out_df.at[row, 'Time Taken'] = time.time() - start_time
            out_df.at[row, 'Num Census Blocks'] = result
            
        # Shapefile creation failed
        except Exception as e:
            print(e)
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
    
    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')