import pandas as pd
import geopandas as gpd
import helper_tools as ht

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/received_check_name_matches_Sep_11.csv"

# Import Google Drive path
direc_path = ht.read_one_csv_elem(csv_path)

# Import table from CSV into pandas df
csv_col = ['Locality Name', 'Path', 'Filename', 'Col to Check', \
           'List to Check']
csv_list = ['List to Check']
csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

# Initialize out_df, which contains the batching output
new_cols = ['Result', 'Locality Name', 'Match', 'SHP No Match', 'Num SHP', \
            'Input No Match', 'Num Input']
out_df = pd.DataFrame(columns=new_cols)

# Iterate through each county we are finding the difference for
for i, _ in csv_df.iterrows():
    
    try:
        # Define the locality
        local = csv_df.at[i, 'Locality Name']
        print(local)

        # If path is default 1 then use Filename
        if csv_df.at[i, 'Path'] == 1:
            path_shape = direc_path + '/' + local + '/' + \
                            csv_df.at[i, 'Filename']
                            
        path_shape = ht.default_path(path_shape, local, direc_path)

        # Read in shapefile
        ht.delete_cpg(path_shape)
        df = gpd.read_file(path_shape)


        # Create list of the matching column
        shp_set = set([str(e).upper() for e in \
                    list(df[csv_df.at[i, 'Col to Check']])])
        input_set = set([str(e).upper() for e in \
                         csv_df.at[i, 'List to Check']])

        # Get elements in shp that do not match
        shp_no_match = list(shp_set - input_set)
        input_no_match = list(input_set - shp_set)
        # Place Results in out_df
        row = len(out_df)
        
        if len(shp_no_match) == 0 and len(input_no_match) == 0:
            out_df.at[row, 'Match'] = 1
        else:
            out_df.at[row, 'Match'] = 0
        out_df.at[row, 'SHP No Match'] = ht.join_list(shp_no_match, ',')
        out_df.at[row, 'Num SHP'] = len(shp_no_match)
        out_df.at[row, 'Input No Match'] = ht.join_list(input_no_match, \
                                             ',')
        out_df.at[row, 'Num Input'] = len(input_no_match)
        out_df.at[row, 'Result'] = 'SUCCESS'
        out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
        
    # Shapefile creation failed
    except:
        print('ERROR:' + csv_df.at[i, 'Locality'])
        row = len(out_df)
        out_df.at[row, 'Result'] = 'FAILURE'
        out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']

# Create path to output our results CSV file and output
csv_out_path = csv_path[:-4] + ' RESULTS.csv'
out_df.to_csv(csv_out_path)
