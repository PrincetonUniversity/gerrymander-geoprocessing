import pandas as pd
import geopandas as gpd
import os
import shapely as shp
import csv

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/county_diff_received_shapefiles2.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    # Import Google Drive path
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    direc_path = data[0][1]

    # Import table from CSV into pandas dataframe
    name_list = ['Locality Name', 'Shape1', 'Shape2']
    csv_df = pd.read_csv(csv_path, header=1, names=name_list)

    # Initialize out_df, which contains the results of the difference
    new_cols = ['Result', 'Locality Name', 'Percent Diff']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Create shapefile out of precincts
        try:
            # Define the locality
            local = csv_df.at[i, 'Locality Name']
            print(local)
            # Get path for the first shape
            path_shape1 = direc_path + '/' + local + '/' + \
                            csv_df.at[i, 'Shape1']
                            
            # Get path for the second shape
            # Set second shape to census blocks if set to default
            if csv_df.at[i, 'Shape2'] == 1:
                census_filename = local + '_census_block.shp'
                census_filename = census_filename.replace(' ', '_')
                path_shape2 = direc_path + '/' + local + '/' + \
                                census_filename
            else:
                path_shape2 = direc_path + '/' + local + '/' + \
                            csv_df.at[i, 'Shape2']
        
            # Read in first shape                
            # Delete CPG file if it exists
            cpg_path1 = ''.join(path_shape1.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path1):
                os.remove(cpg_path1)
            df1 = gpd.read_file(path_shape1)
            
            # Find union of first shape
            polys1 = list(df1['geometry'])
            poly1 = shp.ops.cascaded_union(polys1)
            
            # Read in second shape
            # Delete CPG file if it exists
            cpg_path2 = ''.join(path_shape2.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path2):
                os.remove(cpg_path2)
            df2 = gpd.read_file(path_shape2)
            
            # Find union of second shape
            polys2 = list(df2['geometry'])
            poly2 = shp.ops.cascaded_union(polys2)
            
            # Find percent difference
            diff = poly2.difference(poly1).area
            perc_diff = diff / poly2.area
        
            # Place Results in out_df
            row = len(out_df)
            out_df.at[row, 'Result'] = 'SUCCESS'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Percent Diff'] = perc_diff
        
        # Shapefile creation failed
        except Exception as e:
            print(e)
            print('ERROR:' + csv_df.at[i, 'Locality'])
            row = len(out_df)
            out_df.at[row, 'Result'] = 'FAILURE'
            out_df.at[row, 'Locality Name'] = csv_df.at[i, 'Locality Name']
            out_df.at[row, 'Percinct Diff'] = 'NA'

    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)

# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist OR close RESULTS csv')
