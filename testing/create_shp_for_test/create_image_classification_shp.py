# -*- coding: utf-8 -*-
"""
Create shapefile to test the image classification
"""

import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path = os.getcwd() + "/test_data/image_classification/img_class.shp"

# get grid length
grid_len = 4

# attribute name and values
attribute_name = 'attribute'

# Initialize Geodataframe
df = gpd.GeoDataFrame(columns=[attribute_name, 'geometry'])

for i in range(grid_len):
    for j in range(grid_len):
        r = len(df)
        df.at[r, attribute_name] = grid_len * i + j
        df.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df.to_file(file_path)
