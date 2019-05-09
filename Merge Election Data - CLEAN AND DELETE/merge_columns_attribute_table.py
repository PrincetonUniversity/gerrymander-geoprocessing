# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 13:53:32 2018

@author: Jacob
"""

import geopandas as gpd
import pandas as pd

# initialize shapefile paths
shp1_path = ''
shp2_path = ''
output_path = ''

# set field to match on
match = ''

# set field in second dataframe to add to first dataframe
field_to_add = ''

# read in files to geodataframes
df1 = gpd.read_file(shp1_path)
df2 = gpd.read_file(shp2_path)

# merge dataframes
merged = gpd.merge(df1, df2, on= match, how='left', suffixes=('', '_r_suffix'))

# rename key column
merged = merged.rename(columns={field_to_add + '_r_suffix': field_to_add})

# drop extra columns
cols_to_drop = [i for i in merged.columns if '_r_suffix' in i]
merged = merged.drop(cols_to_drop, axis=1)

# export
merged.to_file(output_path)