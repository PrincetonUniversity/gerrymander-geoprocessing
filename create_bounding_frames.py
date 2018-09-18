import geopandas as gpd
import helper_tools as ht

# Get path to our CSV file
csv_path = "/home/hannah/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/generate_bounding_frame_Essex_Richmond_Staunton.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'Census Path', 'Out Path']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Create geometry for entire locality
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            
            # Get paths and delete cpg file
            census_path = ht.default_path(csv_df.at[i, 'Census Path'], \
                                           local, direc_path)
            ht.delete_cpg(census_path)
            out_path = ht.default_path(csv_df.at[i, 'Out Path'], local, \
                                       direc_path)

            df_census = gpd.read_file(census_path)
            ht.generate_bounding_frame(df_census, out_path)

        # Shapefile creation failed
        except:
            print('ERROR:' + csv_df.at[i, 'Locality'])

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
