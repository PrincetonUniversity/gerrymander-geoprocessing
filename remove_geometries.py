import pandas as pd
import geopandas as gpd
import shapely as shp
import helper_tools as ht
import os.path
import sys

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/shapefile_difference_VA_09_13_18.csv"

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
# results of the difference
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
            
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'Remove', 'Out Path', 'Keep Ratio']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 2, csv_col, csv_list)
    
    # get the base path
    base_path = ht.read_one_csv_elem(csv_path, 2, 2)
    ht.delete_cpg(base_path)
    base_df = gpd.read_file(base_path)

    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Create geometry for entire locality
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)

            # Get path for remove and base shape
            remove_path = ht.default_path(csv_df.at[i, 'Remove'], local, \
                                          direc_path)
            ht.delete_cpg(remove_path)
            remove_df = gpd.read_file(remove_path)
            
            # Get path for out path
            out_path = ht.default_path(csv_df.at[i, 'Out Path'], local, \
                                       direc_path)
            
            # Find union of first shape
            base_polys = list(base_df['geometry'])
            base_poly = shp.ops.cascaded_union(base_polys)
            
            drop_ix = []
            drop_ratio = csv_df.at[i, 'Keep Ratio']
            
            # Iterate through all of the remove geometries
            for j, _ in remove_path.iterrows():
                # Get overlap ratio
                poly = base_df.at[j, 'geometry']
                ratio = poly.intersection(base_poly).area / poly.area
                
                # Drop when intersection ratio is less than drop ratio
                if ratio < drop_ratio:
                    drop_ix.append(j)
                    
            # Drop indexes and save
            out_df = remove_df.drop(drop_ix)
            ht.save_shapefile(out_df, out_path, cols_to_exclude=[])
        
        # Shapefile creation failed
        except:
            print('ERROR:' + csv_df.at[i, 'Locality'])

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
