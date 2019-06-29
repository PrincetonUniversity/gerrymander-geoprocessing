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

path_grid = os.getcwd() + "/test_data/calculate_shared_perimeters/grid.shp"
path_small_border = os.getcwd() + "/test_data/calculate_shared_perimeters/multiple_intersections.shp"

'''
grid: 2x2 square grid
mult_bound: top geometry intersects with bottom geometry in two locations.
	the middle geometry is nested between the two
'''

# Initialize geodataframes
df_grid = gpd.GeoDataFrame(columns=['name', 'geometry'])
df_mult_bound = gpd.GeoDataFrame(columns=['name', 'geometry'])

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

# Multiple Boundaries
df_mult_bound.at[0, 'name'] = 'top'
df_mult_bound.at[0, 'geometry'] = Polygon([(0,0), (0,2), (3,2), (3,0), (2,0), 
									 (2,1), (1,1), (1,0)])

df_mult_bound.at[1, 'name'] = 'middle'
df_mult_bound.at[1, 'geometry'] = Polygon([(1,0), (2,0), (2,1), (1,1)])

df_mult_bound.at[2, 'name'] = 'bottom'
df_mult_bound.at[2, 'geometry'] = Polygon([(0,0), (1,0), (2,0), (3,0), (3,-1), 
										   (0,-1)])

# Save to proper paths
df_grid.to_file(path_grid)
df_mult_bound.to_file(path_small_border)