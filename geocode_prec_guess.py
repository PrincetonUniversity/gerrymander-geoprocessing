import pandas as pd
import geopandas as gpd
import csv
import time
from geopy.geocoders import Nominatim
import os
import shapely as shp
from shapely.geometry import Point

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/precinct_guess_Bethune_Hill_small.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the transfer
try:
    # Import Google Drive path
    with open(csv_path) as f:
        reader = csv.reader(f)
        data = [r for r in reader]
    direc_path = data[0][1]
    
    # Set geolocator instance on Open Street Map server
    g = Nominatim(user_agent='my-application', timeout=10)
    
    # Import table from CSV into pandas dataframe
    csv_df_names = ['Locality', 'Precinct Name', 'Shape Path']
    csv_df = pd.read_csv(csv_path, header=1, names=csv_df_names)
    
    # Adjust strings delimited by commas into lists
    list_col = ['Precinct Name']
    for col in list_col:
        csv_df[col] = csv_df[col].str.split(',')
        
    # Iterate over every locality 
    for i, _ in csv_df.iterrows():
        
        try:
            # Obtain the locality
            local = csv_df.at[i, 'Locality']
            print('\n' + local)
            
            # Get the shapefile path
            shape_path = csv_df.at[i, 'Shape Path']
            
            # Change census shapefile path and out folder if set to default
            if shape_path == 1:
                census_filename = local + '_precincts.shp'
                shape_path = direc_path + '/' + local + '/' + \
                                census_filename
            
            # Load in shapefile
            # Delete CPG file if it exists
            cpg_path = ''.join(shape_path.split('.')[:-1]) + '.cpg'
            if os.path.exists(cpg_path):
                os.remove(cpg_path)
            
            # read in census block shapefile
            df = gpd.read_file(shape_path)
            
            # initialize prec_geo and prec_merge columns to 0
            df['prec_geo'] = pd.Series(dtype=object)
            df['prec_guess'] = pd.Series(dtype=object)
            df['prec_geo'] = '0'
            
            # get the complete county shape
            polys = list(df['geometry'])
            county_geom = shp.ops.cascaded_union(polys)
            
            # initialize empty used precinct list
            used_prec = []
            prec_copy = csv_df.at[i, 'Precinct Name']
    
            # Iterate through every precinct in the county
            for prec in csv_df.at[i, 'Precinct Name']:
                # Skip if error occurs
                try:
                    # get location
                    loc_str = prec + ' ' + local + ' Virginia'
                    location = g.geocode(loc_str)
                    
                    if location != None:
                        p = Point(location.longitude, location.latitude)
                        # Pause one second for usage limits
                        time.sleep(1)
                        
                        # match location 
                        if county_geom.contains(p):
                            # Iterate thorough all the shapes
                            for j, _ in df.iterrows():
                                # Check if point is within shape and shape has
                                # not been set
                                if df.at[j, 'geometry'].contains(p) and \
                                df.at[j, 'prec_geo'] == '0':
                                    df.at[j, 'prec_geo'] = prec
                                    used_prec.append(prec)
                except Exception as e:
                    print(e)
                    print(prec)
            
            # Set guess equal to geo
            df['prec_guess'] = df['prec_geo']
            
            # Randomly set the other precincts
            for prec in used_prec:
                prec_copy.remove(prec)
            
            guess_ix = 0
            for k, _ in df.iterrows():
                if df.at[k, 'prec_geo'] == '0':
                    df.at[k, 'prec_guess'] = prec_copy[guess_ix]
                    guess_ix += 1
            
            # Save shapefile
            df.to_file(shape_path)
            
        except Exception as e:
            print(e)

# CSV file could not be read in or exported
except Exception as e:
    print(e)
    print('ERROR: Reading in CSV file')
    
