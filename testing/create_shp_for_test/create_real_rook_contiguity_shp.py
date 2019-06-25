# -*- coding: utf-8 -*-
"""
Create shapefile to test the transform crs function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import Polygon

path_grid = os.getcwd() + "/test_data/real_rook_contiguity/grid.shp"
path_small_border = os.getcwd() + "/test_data/real_rook_contiguity/small_border.shp"
path_gap = os.getcwd() + "/test_data/real_rook_contiguity/gap.shp"

'''
grid: 2x2 square grid
small_border: 2x2  square grid shifted so there is an additional border that is
	really small
gap: two shapes with no border whatsoever
'''

# Initialize geodataframes
df_grid = gpd.GeoDataFrame(columns=['name', 'geometry'])
df_small_border = gpd.GeoDataFrame(columns=['name', 'geometry'])
df_gap = gpd.GeoDataFrame(columns=['name', 'geometry'])

# box documentation
# (minx, miny, maxx, maxy)

# Grid
df_grid.at[0, 'name'] = 'bottom_left'
df_grid.at[0, 'geometry'] = box(0, 0, 1, 1)

df_grid.at[1, 'name'] = 'bottom_right'
df_grid.at[1, 'geometry'] = box(1, 0, 2, 1)

df_grid.at[2, 'name'] = 'top_left'
df_grid.at[2, 'geometry'] = box(0, 1, 1, 2)

df_grid.at[3, 'name'] = 'top_right'
df_grid.at[3, 'geometry'] = box(1, 1, 2, 2)

# Small Border
epsilon = 10 ** (-10)


df_small_border.at[0, 'name'] = 'bottom_left'
df_small_border.at[0, 'geometry'] = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

df_small_border.at[1, 'name'] = 'bottom_right'
df_small_border.at[1, 'geometry'] = Polygon([(1.0, 0.0), (1 + epsilon, 0), (2, 0), (2, 1), (1, 1)])

df_small_border.at[2, 'name'] = 'top_left'
df_small_border.at[2, 'geometry'] = Polygon([(0, 1), (1, 1), (1 + epsilon, 1), (1 + epsilon, 2), (0, 2)])

df_small_border.at[3, 'name'] = 'top_right'
df_small_border.at[3, 'geometry'] = Polygon([(1 + epsilon, 1), (2, 1), (2, 2), 	(1 + epsilon, 2)])

# Gap
df_gap.at[0, 'name'] = 'left'
df_gap.at[0, 'geometry'] = box(0, 0, 1, 1)

df_gap.at[1, 'name'] = 'right'
df_gap.at[1, 'geometry'] = box(2, 0, 3, 1)

# Save to proper paths
df_grid.to_file(path_grid)
df_small_border.to_file(path_small_border)
df_gap.to_file(path_gap)
