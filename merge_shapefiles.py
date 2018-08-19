import pandas as pd
import geopandas as gpd
import os
import csv

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Merge CSV/merge_shapefiles_final.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    
    # Initialize Output Dataframe
    df_final = pd.DataFrame()
    
    # Import Google Drive path
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    direc_path = data[0][1]
    out_path = data[1][1]
    col_keep = data[2][1]

    # Import table from CSV into pandas dataframe
    name_list = ['Locality Name', 'Path']
    csv_df = pd.read_csv(csv_path, header=3, names=name_list)

    # Initialize out_df, which contains the results of the difference
    new_cols = ['Result', 'Locality Name', 'Notes']
    out_df = pd.DataFrame(columns=new_cols)

    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Convert CRS
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            
            # Get path to load in
            path_shape = csv_df.at[i, 'Path']
            
            if path_shape == 'census_block':
                filename = local + '_census_block.shp'
                filename = filename.replace(' ', '_')
                path_shape = direc_path + '/' + local + '/' + filename
                                
            if path_shape == 'precinct':
                filename = local + '_precincts.shp'
                path_shape = direc_path + '/' + local + '/' + filename
                
            if path_shape == 'precinct_final':
                filename = local + '_precincts_final.shp'
                filename = filename.replace(' ', '_')
                path_shape = direc_path + '/' + local + '/' + filename
                
            print(path_shape.split('/')[-1])

            # Read in shapefile
            cpg_path = ''.join(path_shape.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path):
                os.remove(cpg_path)
            df = gpd.read_file(path_shape)

            # Append dataframe to overall dataframe
            df_final = df_final.append(df, ignore_index=True, sort=True)
        
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
           
    # Reduce to only columns to keep. Make sure columns are in df_final cols
    if col_keep != 1:
        col_keep = col_keep.split(',')
        for col in col_keep:
            # remove if not in dataframe
            if col not in df_final.columns:
                col_keep.remove(col)
        
    # Save overall shapefile
    df_final = gpd.GeoDataFrame(df_final, geometry='geometry')
    df_final.to_file(out_path)

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
