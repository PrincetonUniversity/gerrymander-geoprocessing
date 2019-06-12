# -*- coding: utf-8 -*-
"""
Create shapefile to test the shapefile difference function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path_ref = os.getcwd() + "/test_data/compare_shapefile_difference/reference.shp"
file_path_some = os.getcwd() + "/test_data/compare_shapefile_difference/some_difference.shp"
file_path_all = os.getcwd() + "/test_data/compare_shapefile_difference/all_difference.shp"

# Create reference shapefile
df_ref = gpd.GeoDataFrame(columns=['type', 'geometry'])
x_shift = 0
df_ref.at[0, 'type'] = 'reference'
df_ref.at[0, 'geometry'] = box(0 + x_shift, 0, 1 + x_shift, 1)
df_ref.to_file(file_path_ref)

# Create some shifted shapefile
df_some = gpd.GeoDataFrame(columns=['type', 'geometry'])
x_shift = 0.25
df_some.at[0, 'type'] = 'reference'
df_some.at[0, 'geometry'] = box(0 + x_shift, 0, 1 + x_shift, 1)
df_some.to_file(file_path_some)

# Create all shifted shapefile
df_all = gpd.GeoDataFrame(columns=['type', 'geometry'])
x_shift = 1
df_all.at[0, 'type'] = 'reference'
df_all.at[0, 'geometry'] = box(0 + x_shift, 0, 1 + x_shift, 1)
df_all.to_file(file_path_all)

