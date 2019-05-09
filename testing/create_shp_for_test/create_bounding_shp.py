# -*- coding: utf-8 -*-
"""
Create shapefile to test the dissolve function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path1 = os.getcwd() + "/debug/input_contiguous.shp"
file_path2 = os.getcwd() + "/debug/input_noncontiguous.shp"

# get grid length
grid_len = 3
grid_vals = ['A', 'A', 'A']

# attribute name and values
attribute_name = 'attribute'

# Create contiguous dataframe
df1 = gpd.GeoDataFrame(columns=[attribute_name, 'geometry'])

for i in range(grid_len):
    for j in range(grid_len):
        r = len(df1)

        df1.at[r, attribute_name] = grid_vals[i]
        df1.at[r, 'geometry'] = box(i, j, i + 1, j + 1)
df1.to_file(file_path1)

# Create noncontiguous dataframe
df2 = gpd.GeoDataFrame(columns=[attribute_name, 'geometry'])

for i in range(grid_len):
    for j in range(grid_len):
        r = len(df2)

        df2.at[r, attribute_name] = grid_vals[i]
        df2.at[r, 'geometry'] = box(i, j, i + 0.5, j + 0.5)

df2.to_file(file_path2)