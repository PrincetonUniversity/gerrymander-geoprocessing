import pandas as pd
import geopandas as gpd
import time
from geopy.geocoders import Nominatim
import shapely as shp
from shapely.geometry import Point
import helper_tools as ht
import os.path
import sys

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/precinct_guess_Bethune_Hill_small.csv"

# Check if the length is greater than 1
if len(sys.argv) > 1:
    # If file exists then make the csv_path the second argument
    if os.path.isfile(sys.argv[1]):
        csv_path = sys.argv[1]
        print('\nUsing command argument as csv path')
    else:
        print('\nTerminal argument does not exist. Exiting.')
        sys.exit()


state = 'Virginia'
# Initial try and except to catch improper csv_path or error exporting the
# results of the transfer
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['Locality', 'Precinct Name', 'Shape Path']
    csv_list = ['Precinct Name']
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

    # Initialize out_df, which contains the batching output
    new_cols = ['Result', 'Locality Name']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Set geolocator instance on Open Street Map server
    g = Nominatim(user_agent='my-application', timeout=10)

    # Iterate over every locality 
    for i, _ in csv_df.iterrows():
        
        try:
            # Obtain the locality
            local = csv_df.at[i, 'Locality']
            print('\n' + local)
            
            # Get the shapefile path
            shape_path = ht.default_path(csv_df.at[i, 'Shape Path'], local,\
                                         direc_path)
            
            # read in census block shapefile
            ht.delete_cpg(shape_path)
            df = gpd.read_file(shape_path)
            
            # initialize prec_geo and prec_merge columns to 0
            df['prec_geo'] = pd.Series(0, dtype=object)
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
                    loc_str = prec + ' ' + local + ' ' + state
                    location = g.geocode(loc_str)
                    
                    if location != None:
                        p = Point(location.longitude, location.latitude)
                        # Pause one second for Nominatim usage limits
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
                except:
                    print('ERROR ' + prec)
            
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
            
        except:
            print('ERROR: ' + local)

# CSV file could not be read in or exported
except:
    print('ERROR: Reading in CSV file')
    
