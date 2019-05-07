'''
Dissolve boundaries for shapefile(s) according to a given attribute. we will
also check for contiguity after boundaries have been dissolved.

Can perform for a batch
'''

import pandas as pd
import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm

''' 
INPUT:

in_path: full path to input shapefile to be dissolved
out_path: full path to save created shapefile
disolve_attribute: attribute to dissolve boundaries by
'''
in_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/debug/input_contained.shp"
out_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/debug/test_contained.shp"
dissolve_attribute = "attribute"

''' Code '''
#  Generate dissolved shapefile
geo_df = sm.dissolve(in_path, dissolve_attribute)

# Check for noncontiguous and contained geometries
sc.check_contiguity_and_contained(geo_df, dissolve_attribute)

# Save shapefile
fm.save_shapefile(geo_df, out_path)
