import geopandas as gpd
import helper_tools as ht

# Transfer an attribute column to another shapefile using areal interpolation.

# Get path to our CSV batch file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Areal Interpolate CSV/interpolate_label_testing_galax.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the transfer
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['locality', 'type', 'to_df path', 'to_df cols', 'format', \
                    'from_df path', 'from_df cols']
    csv_list = ['to_df cols', 'from_df cols', 'format']
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)
    
    # Iterate through all of the interpolations
    for i, _ in csv_df.iterrows():
        
        # Show which locality is currently being interpolated
        local = csv_df.at[i, 'locality']
        print('\n' + local)
        try: 
            
            # Initalize columns (to, from) for the interpolation as well
            # as the format
            adjust_cols = []
            from_cols = csv_df.at[i, 'from_df cols']
            to_cols = csv_df.at[i, 'to_df cols']
            format_cols =  csv_df.at[i, 'format']
            
            # Throw error if we there are an incorrect number of columns
            # to interpolate
            if len(from_cols) != len(to_cols):
                raise Exception('# of from and to cols are unequal')
        
            # Create the adjust list. This list contains a tuple of
            # column to interpolate, column interpolated from, format of
            # the new string
            for ix, elem in enumerate(to_cols):
                adjust_cols.append((elem, from_cols[ix], format_cols[ix]))
                
            # Get to path and from path
            to_path = ht.default_path(csv_df.at[i, 'to_df path'], local, \
                                      direc_path)
            from_path = ht.default_path(csv_df.at[i, 'from_df path'], \
                                        local, direc_path)
            
            # Delete CPG files for to and from
            ht.delete_cpg(to_path)
            ht.delete_cpg(from_path)
            
            # Load dataframes
            df_to = gpd.read_file(to_path)
            df_from = gpd.read_file(from_path)

            # run label interpolation
            new_df_to = ht.interpolate_label(df_to, df_from, adjust_cols,\
                                             csv_df.at[i, 'type'])
            
            # Save the new "to" df
            ht.save_shapefile(new_df_to, to_path)
            
        except:
            print('Error during interpolation')

# CSV file could not be read in or exported
except:
    print('ERROR: Reading in CSV file')
    
