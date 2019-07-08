# -*- coding: utf-8 -*-
"""
Create shapefile to test merge_geometries
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import Polygon

path = os.getcwd() + "/test_data/merge_to_right_number/right_number.shp"

# Initialize geodataframes
df = gpd.GeoDataFrame(columns=['name', 'geometry'])

# set up three of the four
poly1 = box(0, 0, 1, 1)
poly2 = box(0, 1, 2, 2)
poly3 = box(0, 2, 4, 3)
poly4 = box(0, 3, 8, 4)

# Add small geometry
df.at[0, 'name'] = 'small'
df.at[0, 'geometry'] = poly1

# Add medium geometry
df.at[1, 'name'] = 'medium'
df.at[1, 'geometry'] = poly2

# Add large geometry
df.at[2, 'name'] = 'large'
df.at[2, 'geometry'] = poly3

# Add extra large geometry
df.at[3, 'name'] = 'XL'
df.at[3, 'geometry'] = poly4

df.to_file(path)