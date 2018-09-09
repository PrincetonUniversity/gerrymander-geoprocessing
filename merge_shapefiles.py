import pandas as pd
import geopandas as gpd
import os
import helper_tools as ht

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Merge CSV/merge_shapefiles_names_fixed_Aug_21.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    out_path = ht.read_one_csv_elem(csv_path, 1, 1)
    col_keep = ht.read_one_csv_elem(csv_path, 2, 1)
    
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'Path']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 3, csv_col, csv_list)
    
    # Initialize Output Dataframe
    df_final = pd.DataFrame()

    # Initialize out_df, which contains the batch output
    new_cols = ['Result', 'Locality Name']
    out_df = pd.DataFrame(columns=new_cols)

    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Convert CRS
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            
            # Get path to load in
            path_shape = ht.default_path(local, csv_df.at[i, 'Path'], \
                                         direc_path)

            # Read in shapefile
            ht.delete_cpg(path_shape)
            df = gpd.read_file(path_shape)

            # Append dataframe to overall dataframe
            df_final = df_final.append(df, ignore_index=True, sort=True)
        
            # Place Results in out_df
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
           
    # Reduce to only columns to keep. Make sure columns are in df_final cols
    if col_keep != 1:
        col_keep = col_keep.split(',')
        for col in col_keep:
            # remove if not in dataframe
            if col not in df_final.columns:
                col_keep.remove(col)
        
    # Save final shapefile
    df_final = gpd.GeoDataFrame(df_final, geometry='geometry')
    ht.save_shapefile(df_final, out_path)

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
