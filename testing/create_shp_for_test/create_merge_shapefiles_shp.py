# -*- coding: utf-8 -*-
"""
Create shapefile to test the dissolve function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

file_path_full = os.getcwd() + "/test_data/merge_shapefiles/input_full.shp"
file_path_part1 = os.getcwd() + "/test_data/merge_shapefiles/input_part1.shp"
file_path_part2 = os.getcwd() + "/test_data/merge_shapefiles/input_part2.shp"
file_path_part3 = os.getcwd() + "/test_data/merge_shapefiles/input_part3.shp"

# Get grid length and columns
grid_len = 3
cols = ['col1', 'col2', 'col3']

# Create full shapefile
df_full = gpd.GeoDataFrame(columns=['col1', 'col2', 'col3', 'geometry'])

for i in range(grid_len):
	for j in range(grid_len):
		r = len(df_full)

		for c in cols:
			df_full.at[r, c] = 1
		df_full.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df_full.to_file(file_path_full)

# Create Part 1 shapefile
df_part1 = gpd.GeoDataFrame(columns=['col1', 'col2', 'col3', 'geometry'])

i = 0
for j in range(grid_len):
	r = len(df_part1)

	for c in cols:
		df_part1.at[r, c] = 1
	df_part1.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df_part1.to_file(file_path_part1)

# Create Part 2 shapefile
df_part2 = gpd.GeoDataFrame(columns=['col1', 'col2', 'col3', 'geometry'])
i = 1
for j in range(grid_len):
	r = len(df_part2)

	for c in cols:
		df_part2.at[r, c] = 1
	df_part2.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df_part2.to_file(file_path_part2)

# Create Part 3 shapefile
df_part3 = gpd.GeoDataFrame(columns=['col1', 'col2', 'col3', 'geometry'])
i = 2
for j in range(grid_len):
	r = len(df_part3)

	for c in cols:
		df_part3.at[r, c] = 1
	df_part3.at[r, 'geometry'] = box(i, j, i + 1, j + 1)

df_part3.to_file(file_path_part3)
