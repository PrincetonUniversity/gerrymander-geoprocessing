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

path_gen = os.getcwd() + "/test_data/clean_manual_classification/general.shp"

# fully contained
path_fc = os.getcwd() + "/test_data/clean_manual_classification/fc.shp"

# split noncontiguous
path_sn = os.getcwd() + "/test_data/clean_manual_classification/sn.shp"

# Initialize geodataframes
df_gen = gpd.GeoDataFrame(columns=['class', 'geometry'])
df_fc = gpd.GeoDataFrame(columns=['class', 'geometry'])
df_sn = gpd.GeoDataFrame(columns=['class', 'geometry'])

# Create the general dataframe
poly1 = box(0, 0, 1, 1)
poly2 = box(1, 0, 3, 1)
poly3 = box(0, 1, 1, 2)
poly4 = box(1, 1, 3, 2)

df_gen.at[0, 'class'] = 'a'
df_gen.at[0, 'geometry'] = poly1

df_gen.at[1, 'class'] = 'b'
df_gen.at[1, 'geometry'] = poly2

df_gen.at[2, 'class'] = 'a'
df_gen.at[2, 'geometry'] = poly3

df_gen.at[3, 'geometry'] = poly4

# Create the fully contained  dataframe
poly1 = box(0, 0, 1, 1)
poly2 = box(1, 0, 2, 1)
poly3 = box(2, 0, 3, 1)
poly4 = box(0, 1, 1, 2)
poly5 = box(1, 1, 2, 2)
poly6 = box(2, 1, 3, 2)
poly7 = box(0, 2, 1, 3)
poly8 = box(1, 2, 2, 3)
poly9 = box(2, 2, 3, 3)

df_fc.at[0, 'geometry'] = poly1
df_fc.at[1, 'geometry'] = poly2
df_fc.at[2, 'geometry'] = poly3
df_fc.at[3, 'geometry'] = poly4
df_fc.at[4, 'geometry'] = poly5
df_fc.at[5, 'geometry'] = poly6
df_fc.at[6, 'geometry'] = poly7
df_fc.at[7, 'geometry'] = poly8
df_fc.at[8, 'geometry'] = poly9

df_fc.at[1, 'class'] = 'a'
df_fc.at[2, 'class'] = 'a'
df_fc.at[3, 'class'] = 'a'
df_fc.at[4, 'class'] = 'b'
df_fc.at[5, 'class'] = 'a'
df_fc.at[6, 'class'] = 'a'
df_fc.at[7, 'class'] = 'a'
df_fc.at[8, 'class'] = 'a'

# Create the split noncontiguous dataframe
df_sn.at[0, 'geometry'] = poly1
df_sn.at[1, 'geometry'] = poly2
df_sn.at[2, 'geometry'] = poly3
df_sn.at[3, 'geometry'] = poly4
df_sn.at[4, 'geometry'] = poly5
df_sn.at[5, 'geometry'] = poly6
df_sn.at[6, 'geometry'] = poly7
df_sn.at[7, 'geometry'] = poly8
df_sn.at[8, 'geometry'] = poly9

df_sn.at[0, 'class'] = 'a'
df_sn.at[1, 'class'] = 'b'
df_sn.at[2, 'class'] = 'a'
df_sn.at[4, 'class'] = 'b'
df_sn.at[6, 'class'] = 'a'
df_sn.at[7, 'class'] = 'b'
df_sn.at[8, 'class'] = 'a'

# Save dataframes
df_gen.to_file(path_gen)
df_fc.to_file(path_fc)
df_sn.to_file(path_sn)