# -*- coding: utf-8 -*-
"""
Create shapefile to test split noncontiguous
"""
import os
os.chdir('..')
import shapely as shp
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import Polygon

path_two = os.getcwd() + "/test_data/split_noncontiguous/two_pieces.shp"
path_four = os.getcwd() + "/test_data/split_noncontiguous/four_pieces.shp"

'''
two: two noncontiguous pieces 
four: four noncontiguous pieces
'''

# Initialize geodataframes
df_two = gpd.GeoDataFrame(columns=['name', 'value1', 'value2', 'geometry'])
df_four = gpd.GeoDataFrame(columns=['name', 'geometry'])

# Initilaize Four Polygons
poly1 = box(0, 0, 1, 1)
poly2 = box(2, 0, 3, 1)
poly3 = box(0, 2, 1, 3)
poly4 = box(2, 3, 2, 3)

# Two Pieces
df_two.at[0, 'name'] = 'two_pieces'
df_two.at[0, 'value1'] = 1
df_two.at[0, 'value2'] = 2

two_poly = poly1.union(poly2)
df_two.at[0, 'geometry'] = two_poly

# Four Pieces
df_four.at[0, 'name'] = 'four_pieces'

four_poly = shp.ops.cascaded_union([poly1, poly2, poly3, poly4])
df_four.at[0, 'geometry'] = four_poly

df_two.to_file(path_two)
df_four.to_file(path_four)