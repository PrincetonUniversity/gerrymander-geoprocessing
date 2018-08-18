import pandas as pd
import geopandas as gpd
import os
import shapely as shp
import csv

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/county_transform_coordinates.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    # Import Google Drive path
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    direc_path = data[0][1]

    # Import table from CSV into pandas dataframe
    name_list = ['Locality Name', 'File Name', 'CRS']
    csv_df = pd.read_csv(csv_path, header=1, names=name_list)

    # Initialize out_df, which contains the results of the difference
    new_cols = ['Result', 'Locality Name', 'Notes']
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
            cpg_path = ''.join(path_shape.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path):
                os.remove(cpg_path)
            df = gpd.read_file(path_shape)
            
            # Check if no coordinate system and we need to treat it as a pdf
            if df.crs == {}:
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
                out_df.at[row, 'Locality Name'] = local
                out_df.at[row, 'Notes'] = 'No CRS. Treat as PDF'
            
            # Transform coordinates
            else:
                # Transform
                df = df.to_crs({'init': new_crs})
                
                # Save shapefile
                df.to_file(path_shape)
            
                # Place Results in out_df
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
                out_df.at[row, 'Notes'] = 'none'
        
        # Shapefile creation failed
        except Exception as e:
            print(e)
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Notes'] = e

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
