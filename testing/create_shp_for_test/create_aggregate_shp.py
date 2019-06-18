# -*- coding: utf-8 -*-
"""
Create shapefile to test the transform crs function
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box

path_large = os.getcwd() + "/test_data/aggregate/large.shp"
path_centroid = os.getcwd() + "/test_data/aggregate/small_centroid.shp"
path_within = os.getcwd() + "/test_data/aggregate/small_within.shp"
path_shared = os.getcwd() + "/test_data/aggregate/small_shared.shp"
path_leftover = os.getcwd() + "/test_data/aggregate/small_leftover.shp"
path_reset = os.getcwd() + "/test_data/aggregate/reset.shp"
path_keep = os.getcwd() + "/test_data/aggregate/keep.shp"

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
df_large = gpd.GeoDataFrame(columns=['col_agg_on', 'geometry'])
df_centroid = gpd.GeoDataFrame(columns=['geometry'])
df_within = gpd.GeoDataFrame(columns=['geometry'])
df_shared = gpd.GeoDataFrame(columns=['geometry'])
df_leftover = gpd.GeoDataFrame(columns=['geometry'])
df_reset = gpd.GeoDataFrame(columns=['geometry'])
df_keep = gpd.GeoDataFrame(columns=['keep_col', 'geometry'])

# box documentation
# (minx, miny, maxx, maxy)

# Large
df_large.at[0, 'col_agg_on'] = 2
df_large.at[1, 'col_agg_on'] = 1
df_large.at[0, 'geometry'] = box(0, 0, 2, 2)
df_large.at[1, 'geometry'] = box(2, 0, 4, 2)

# Centroid
df_centroid.at[0, 'agg_col'] = 1
df_centroid.at[0, 'geometry'] = box(-2, 0, -1, 1)

# Within
df_within.at[0, 'agg_col'] = 2
df_within.at[0, 'other_col'] = 4
df_within.at[0, 'geometry'] = box(0.5, 0.5, 1.5, 1.5)
df_within.at[1, 'agg_col'] = 1
df_within.at[1, 'other_col'] = 3
df_within.at[1, 'geometry'] = box(2.5, 0.5, 3.5, 1.5)

# Reset
df_reset.at[0, 'agg_col'] = 200
df_reset.at[1, 'agg_col'] = 100
df_reset.at[0, 'geometry'] = box(0, 0, 2, 2)
df_reset.at[1, 'geometry'] = box(2, 0, 4, 2)

# Keep
df_keep.at[0, 'keep'] = 'keep'
df_keep.at[1, 'keep'] = 'keep'
df_keep.at[0, 'geometry'] = box(0, 0, 2, 2)
df_keep.at[1, 'geometry'] = box(2, 0, 4, 2)

# Shared
df_shared.at[0, 'agg_col'] = 1
df_shared.at[1, 'agg_col'] = 1
df_shared.at[2, 'agg_col'] = 1
df_shared.at[3, 'agg_col'] = 1
df_shared.at[4, 'agg_col'] = 1

# 90% left box
shift = 0.2
df_shared.at[0, 'geometry'] = box(0 + shift, 0, 2 + shift, 0.4)

# 70% left box
shift = 0.6
df_shared.at[1, 'geometry'] = box(0 + shift, 0.4, 2 + shift, 0.8)

# 55% left box
shift = 0.9
df_shared.at[2, 'geometry'] = box(0 + shift, 0.8, 2 + shift, 1.2)

# 40% left box
shift = 1.2
df_shared.at[3, 'geometry'] = box(0 + shift, 1.2, 2 + shift, 1.6)

# 20% left box
shift = 1.6
df_shared.at[4, 'geometry'] = box(0 + shift, 1.6, 2 + shift, 2)

# Leftover
df_leftover.at[0, 'agg_col'] = 1
df_leftover.at[0, 'geometry'] = box(0, -1, 3, 1)

# Save to proper paths
df_large.to_file(path_large)
df_centroid.to_file(path_centroid)
df_within.to_file(path_within)
df_reset.to_file(path_reset)
df_keep.to_file(path_keep)
df_shared.to_file(path_shared)
df_leftover.to_file(path_leftover)