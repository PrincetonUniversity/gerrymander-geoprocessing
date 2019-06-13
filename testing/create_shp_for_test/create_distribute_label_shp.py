# -*- coding: utf-8 -*-
"""
Create shapefile to test the transform crs function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

path_ref = os.getcwd() + "/test_data/distribute_label/reference.shp"
path_within = os.getcwd() + "/test_data/distribute_label/within.shp"
path_shared = os.getcwd() + "/test_data/distribute_label/shared.shp"
path_centroid = os.getcwd() + "/test_data/distribute_label/centroid.shp"
path_reset = os.getcwd() + "/test_data/distribute_label/reset.shp"
path_keep = os.getcwd() + "/test_data/distribute_label/keep.shp"

'''
Ref -> df_large
within -> checks when only one intersection occurs
shared -> checks when multiple intersections occur
centroid -> checks when no intersection occurs
reset -> existing columns get deleted
keep -> checks that df_small retains existing columns
default -> default columns works

NOTE: that within, default all use the same shapefile within
'''

# Create reference shapefile
df_ref = gpd.GeoDataFrame(columns=['large_str', 'large_int', 'large_flt', 
	'geometry'])
df_within = gpd.GeoDataFrame(columns=['geometry'])
df_shared = gpd.GeoDataFrame(columns=['geometry'])
df_centroid = gpd.GeoDataFrame(columns=['geometry'])
df_reset = gpd.GeoDataFrame(columns=['geometry'])
df_keep = gpd.GeoDataFrame(columns=['keep_col', 'geometry'])

# box documentation
# (minx, miny, maxx, maxy)

# Reference
df_ref.at[0, 'large_str'] = 'a'
df_ref.at[1, 'large_str'] = 'b'
df_ref['large_str'] = df_ref['large_str'].astype('str')

df_ref.at[0, 'large_int'] = 0
df_ref.at[1, 'large_int'] = 1
df_ref['large_int'] = df_ref['large_int'].astype('int')

df_ref.at[0, 'large_flt'] = 0.5
df_ref.at[1, 'large_flt'] = 1.5
df_ref['large_flt'] = df_ref['large_flt'].astype('float')

df_ref.at[0, 'geometry'] = box(0, 0, 2, 2)
df_ref.at[1, 'geometry'] = box(2, 0, 4, 2)

# Within
df_within.at[0, 'geometry'] = box(0 + 0.5, 0 + 0.5, 2 - 0.5, 2 - 0.5)
df_within.at[1, 'geometry'] = box(2 + 0.5, 0 + 0.5, 4 - 0.5, 2 - 0.5)

# Shared
df_shared.at[0, 'geometry'] = box(1 - 0.1, 0, 3, 1)
df_shared.at[1, 'geometry'] = box(1 + 0.1, 1, 3, 2)

# Centroid
df_centroid.at[0, 'geometry'] = box(0 - 5, 0, 1 - 5, 1)
df_centroid.at[1, 'geometry'] = box(3 + 5, 0, 4 + 5, 1)

# Reset
df_reset.at[0, 'large_str'] = 'y'
df_reset.at[1, 'large_str'] = 'z'
df_reset['large_str'] = df_reset['large_str'].astype('str')

df_reset.at[0, 'large_int'] = 8
df_reset.at[1, 'large_int'] = 9
df_reset['large_int'] = df_reset['large_int'].astype('int')

df_reset.at[0, 'large_flt'] = 8.5
df_reset.at[1, 'large_flt'] = 9.5
df_reset['large_flt'] = df_reset['large_flt'].astype('float')

df_reset.at[0, 'geometry'] = box(0 + 0.5, 0 + 0.5, 2 - 0.5, 2 - 0.5)
df_reset.at[1, 'geometry'] = box(2 + 0.5, 0 + 0.5, 4 - 0.5, 2 - 0.5)

# Keep
df_keep.at[0, 'keep_col'] = 'keep'
df_keep.at[1, 'keep_col'] = 'keep'

df_keep.at[0, 'geometry'] = box(0 + 0.5, 0 + 0.5, 2 - 0.5, 2 - 0.5)
df_keep.at[1, 'geometry'] = box(2 + 0.5, 0 + 0.5, 4 - 0.5, 2 - 0.5)

# Save to proper paths
df_ref.to_file(path_ref)
df_within.to_file(path_within)
df_shared.to_file(path_shared)
df_centroid.to_file(path_centroid)
df_reset.to_file(path_reset)
df_keep.to_file(path_keep)
