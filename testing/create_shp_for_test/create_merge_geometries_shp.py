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

path_stack = os.getcwd() + "/test_data/merge_geometries/stack.shp"
path_box = os.getcwd() + "/test_data/merge_geometries/box.shp"

# Initialize geodataframes
df_stack = gpd.GeoDataFrame(columns=['name', 'add1', 'add2', 'geometry'])
df_box = gpd.GeoDataFrame(columns=['name', 'geometry'])

# set up three of the four
poly1 = box(0, 0, 1, 1)
poly2 = box(0, 1, 2, 2)
poly3 = box(0, 2, 3, 3)

# Add small geometry
df_stack.at[0, 'name'] = 'small'
df_stack.at[0, 'add1'] = 10
df_stack.at[0, 'add2'] = 100
df_stack.at[0, 'geometry'] = poly1

# Add medium geometry
df_stack.at[1, 'name'] = 'medium'
df_stack.at[1, 'add1'] = 20
df_stack.at[1, 'add2'] = 200
df_stack.at[1, 'geometry'] = poly2

# Add large geometry
df_stack.at[2, 'name'] = 'large'
df_stack.at[2, 'add1'] = 30
df_stack.at[2, 'add2'] = 300
df_stack.at[2, 'geometry'] = poly3

# Add box geometries
poly1 = box(0, 0, 1, 1)
poly2 = box(1, 0.5, 2, 1)
poly3 = box(0, 1, 2, 2)

df_box.at[0, 'name'] = 'left'
df_box.at[0, 'geometry'] = poly1

df_box.at[1, 'name'] = 'right'
df_box.at[1, 'geometry'] = poly2

df_box.at[2, 'name'] = 'top'
df_box.at[2, 'geometry'] = poly3

df_stack.to_file(path_stack)
df_box.to_file(path_box)