# -*- coding: utf-8 -*-
"""
Create shapefile to test merge fully contained 
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import Polygon

path_reg = os.getcwd() + "/test_data/merge_fully_contained/regular.shp"
path_nest = os.getcwd() + "/test_data/merge_fully_contained/nested.shp"

# Initialize geodataframes
df_reg = gpd.GeoDataFrame(columns=['name', 'value', 'geometry'])
df_nest = gpd.GeoDataFrame(columns=['name', 'geometry'])

# box documentation
# (minx, miny, maxx, maxy)

# Regular
df_reg.at[0, 'name'] = 'inside'
df_reg.at[0, 'value'] = 1
df_reg.at[0, 'geometry'] = box(1, 1, 2, 2)

df_reg.at[1, 'name'] = 'outside'
df_reg.at[1, 'value'] = 1
df_reg.at[1, 'geometry'] = Polygon([(0,0), (0,3), (3,3), (3,0)], \
	[[(1,1), (1,2), (2,2), (2,1)]])

# Nested
df_nest.at[0, 'name'] = 'inside'
df_nest.at[0, 'geometry'] = box(2, 2, 3, 3)

df_nest.at[1, 'name'] = 'middle_top'
df_nest.at[1, 'geometry'] = box(2, 3, 3, 4)
df_nest.at[2, 'name'] = 'middle_bot'
df_nest.at[2, 'geometry'] = box(2, 1, 3, 2)

df_nest.at[3, 'name'] = 'middle_left'
df_nest.at[3, 'geometry'] = Polygon([(1,1), (2,1), (2,2), (2,3), (2,4), (1,4)])

df_nest.at[4, 'name'] = 'middle_right'
df_nest.at[4, 'geometry'] = Polygon([(4,1), (3,1), (3,2), (3,3), (3,4), (4,4)])

df_nest.at[5, 'name'] = 'outside'
df_nest.at[5, 'geometry'] = Polygon([(0,0), (0,5), (5,5), (5,0)], \
	[[(1,1), (2,1), (3,1), (4,1), (4,4), (3,4), (2,4), (1,4)]])

# Save to proper paths
df_reg.to_file(path_reg)
df_nest.to_file(path_nest)