import pandas as pd
import geopandas as gpd
import helper_tools as ht
import os.path
import sys

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/match_prec_num_to_name.csv"

# Check if the length is greater than 1
if len(sys.argv) > 1:
    # If file exists then make the csv_path the second argument
    if os.path.isfile(sys.argv[1]):
        csv_path = sys.argv[1]
        print('\nUsing command argument as csv path')
    else:
        print('\nTerminal argument does not exist. Exiting.')
        sys.exit()
        
save_shp_bool = False
convert_float_to_int_bool = True

try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'Path', 'Filename', 'Match Name', \
                 'Match Val', 'Append Name', 'Append Val', 'Merge Type']
    csv_list = ['Match Val', 'Append Val']
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

    # Initialize out_df, which contains the batching output
    new_cols = ['Result', 'Locality Name']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # 
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            
            # Get path
            path_shape = csv_df.at[i, 'Path']
            
            # If path is default 1 then use Filename
            if path_shape == 1:
                path_shape = direc_path + '/' + local + '/' + \
                                csv_df.at[i, 'Filename']
                                                
            # Read in shapefile
            ht.delete_cpg(path_shape)
            df = gpd.read_file(path_shape)

            # get match and append names. Get a copy so we can match our values
            # to a string type from the CSV. We will later delete the copy
            # after the merge. Define original name as it will be used to 
            # determine NaN values (see which values of Append Val did not
            # match)
            orig_match_name = csv_df.at[i, 'Match Name']
            match_name = orig_match_name + 'Copy'
            append_name = csv_df.at[i, 'Append Name']

            # create copy matching column and convert to a string type
            df[match_name] = df[csv_df.at[i, 'Match Name']]
            
            # Set up to merge on object
            if convert_float_to_int_bool:
                df[match_name] = df[match_name].astype(int, errors='ignore')
            df[match_name] = df[match_name].astype(str)
            
            # Create df to merge with
            df_dict = {}
            df_dict[match_name] = csv_df.at[i, 'Match Val']
            df_dict[append_name] = csv_df.at[i, 'Append Val']
            df_merge  = pd.DataFrame.from_dict(df_dict)
            
            # Get merge how and set to lowercase
            merge_how = csv_df.at[i, 'Merge Type'].lower()
            
            # save as old if append column is in df columns
            if append_name in list(df.columns):
                old_col_new_name = 'old_' + append_name
                df[old_col_new_name] = df[append_name]
                df = df.drop(columns=[append_name])

            # get wihch vales form the original dataframe did not find a match
            # (match_miss) and which values form the appended dataframe did
            # not find a match (append_miss)
            e_df = df.merge(df_merge, on=match_name, how='outer')
            match_miss = list(e_df[e_df[append_name].isnull()][match_name])
            
            if len(match_miss) == 0:
                match_miss_str = 'none'
            else:
                match_miss_str = ht.join_list(match_miss, ',')

            append_miss = list(e_df[e_df[orig_match_name].isnull()\
                                    ][match_name])

            if len(append_miss) == 0:
                append_miss_str = 'none'
            else:
                append_miss_str = ht.join_list(append_miss, ',')
            # Perform Merge. Delete copy column. Save
            if save_shp_bool:
                df = df.merge(df_merge, on=match_name, how=merge_how)
                ht.save_shapefile(df, path_shape, [match_name])

                
            # Place Results and Notes in out_df
            row = len(out_df)
            out_df.at[row, 'Result'] = 'SUCCESS'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            note = 'Values in original no match: ' + match_miss_str + \
                    '; Values in append no match: ' + append_miss_str
            out_df.at[row, 'Notes'] = note
        
        # Shapefile creation failed
        except:
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Notes'] = 'Failed on ' + local

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
