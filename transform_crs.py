import pandas as pd
import geopandas as gpd
import os
import helper_tools as ht

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/county_transform_coordinates.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'File Name', 'CRS']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

    # Initialize out_df, which contains the results of the difference
    new_cols = ['Result', 'Locality Name']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Convert CRS
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            # Get path and CRS for the first shape
            path_shape = direc_path + '/' + local + '/' + \
                            csv_df.at[i, 'File Name']
            new_crs = csv_df.at[i, 'CRS']
            
            # Read in shapefile
            ht.delete_cpg(path_shape)
            df = gpd.read_file(path_shape)

            # transform CRS
            df = ht.set_CRS(df, new_crs)
            
            # save shapefile
            ht.save_shapefile(df, path_shape)
            
            # batch report
            row = len(out_df)
            out_df.at[row, 'Result'] = 'SUCCESS'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Notes'] = 'none'
        
        # Shapefile creation failed
        except:
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
