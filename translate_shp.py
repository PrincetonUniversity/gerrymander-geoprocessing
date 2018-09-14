import pandas as pd
import geopandas as gpd
import shapely as shp
import helper_tools as ht
from shapely.geometry import Polygon
from shapely.geometry import LinearRing

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Misc CSV/translate_shp_Roanoke_City_Sep_14.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the difference
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    # Import table from CSV into pandas df
    csv_col = ['Locality Name', 'Shape1', 'Shape2']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

    # Initialize out_df, which contains the batching output
    new_cols = ['Result', 'Locality Name']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Iterate through each county we are finding the difference for
    for i, _ in csv_df.iterrows():
        
        # Create geometry for entire locality
        try:
            ######################
            import time
            start = time.time()
            current = start
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
            ht.delete_cpg(path_shape1)
            df1 = gpd.read_file(path_shape1)
            
            # Find union of first shape
            polys1 = list(df1['geometry'])
            poly1 = shp.ops.cascaded_union(polys1)
            
            # Read in second shape
            ht.delete_cpg(path_shape2)
            df2 = gpd.read_file(path_shape2)
            
            # Find union of second shape
            polys2 = list(df2['geometry'])
            poly2 = shp.ops.cascaded_union(polys2)
            
            # Get the bounds for each 
            bounds1 = poly1.bounds
            bounds2 = poly2.bounds
            
            # Calculate shift x and shift y for second shapefile
            shift_x = bounds2[0] - bounds1[0]
            shift_y = bounds2[1] - bounds1[1]

            # Iterate through every geometry in the second geodataframe
            for j, _ in df1.iterrows():
                
                current = time.time()
                # translate the polygon
                poly = df1.at[j, 'geometry']
                
                # need to get the exterior
                exterior = list(poly.exterior.coords)
                new_ext = []
                for c in exterior:
                    c_new_x = c[0] + shift_x
                    c_new_y = c[1] + shift_y
                    new_ext.append((c_new_x, c_new_y))
                    
                # need to get the interiors
                new_interiors = []
                interiors = list(poly.interiors)
                for inter in interiors:
                    inter_coords = list(inter.coords)
                    new_inter_coords = []
                    for c in inter_coords:
                        c_new_x = c[0] + shift_x
                        c_new_y = c[1] + shift_y
                        new_inter_coords.append((c_new_x, c_new_y))
                        
                    new_interiors.append(LinearRing(new_inter_coords))
                        
                df1.at[j, 'geometry'] = Polygon(new_ext, new_interiors)

            ht.save_shapefile(df1, path_shape1)
        
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
