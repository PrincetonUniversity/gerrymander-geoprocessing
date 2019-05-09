# -*- coding: utf-8 -*-
"""
Create shapefile to test the dissolve function
"""

import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path = os.getcwd() + "/debug/input_noncontiguous.shp"

# get grid length
grid_len = 3
grid_vals = ['A', 'B', 'A']

# attribute name and values
attribute_name = 'attribute'

# Initialize Geodataframe
df = gpd.GeoDataFrame(columns=[attribute_name, 'geometry'])

for i in range(grid_len):
    for j in range(grid_len):
        r = len(df)

        df.at[r, attribute_name] = grid_vals[i]
        df.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df.to_file(file_path)
