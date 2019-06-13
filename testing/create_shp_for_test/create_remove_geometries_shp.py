# -*- coding: utf-8 -*-
"""
Create shapefile to test the transform crs function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path_ref = os.getcwd() + "/test_data/remove_geometries/reference.shp"
file_path_del = os.getcwd() + "/test_data/remove_geometries/delete.shp"

# Create reference shapefile
df_ref = gpd.GeoDataFrame(columns=['type', 'geometry'])
df_del = gpd.GeoDataFrame(columns=['type', 'geometry'])

# box documentation
# (minx, miny, maxx, maxy)

# Reference Shapefile

df_ref.at[0, 'type'] = 'first'
df_ref.at[0, 'geometry'] = box(0, 0, 1, 1)

df_ref.at[1, 'type'] = 'second'
df_ref.at[1, 'geometry'] = box(1, 0, 2, 1)

df_ref.at[2, 'type'] = 'third'
df_ref.at[2, 'geometry'] = box(0, 1, 1, 2)

df_ref.at[3, 'type'] = 'fourth'
df_ref.at[3, 'geometry'] = box(1, 1, 2, 2)

df_ref.to_file(file_path_ref)

# Delete shapefile
# Left squares are shifted by 0.2. Right squares are shifted by 0.5
df_del.at[0, 'type'] = 'first'
df_del.at[0, 'geometry'] = box(0 - 0.2, 0, 1 - 0.2, 1)

df_del.at[1, 'type'] = 'second'
df_del.at[1, 'geometry'] = box(1 + 0.5, 0, 2 + 0.5, 1)

df_del.at[2, 'type'] = 'third'
df_del.at[2, 'geometry'] = box(0 - 0.2, 1, 1 - 0.2, 2)

df_del.at[3, 'type'] = 'fourth'
df_del.at[3, 'geometry'] = box(1 + 0.5, 1, 2 + 0.5, 2)

df_del.to_file(file_path_del)