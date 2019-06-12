# -*- coding: utf-8 -*-
"""
Create shapefile to test the transform crs function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path_proj = os.getcwd() + "/test_data/transform_crs/projection.shp"
file_path_no_proj = os.getcwd() + "/test_data/transform_crs/no_projection.shp"

# Create reference shapefile
df_proj = gpd.GeoDataFrame(columns=['type', 'geometry'])
df_proj.at[0, 'type'] = 'projection'
df_proj.at[0, 'geometry'] = box(0, 0, 1, 1)
df_proj.crs = {'init': 'epsg:4326'}
df_proj.to_file(file_path_proj)


# Create some shifted shapefile
df_no_proj = gpd.GeoDataFrame(columns=['type', 'geometry'])
df_no_proj.at[0, 'type'] = 'no_projection'
df_no_proj.at[0, 'geometry'] = box(0, 0, 1, 1)
df_no_proj.to_file(file_path_no_proj)

