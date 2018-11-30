#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 09:13:49 2018

@author: jessicanyquist
"""

import time
import pandas as pd
import geopandas as gpd
import shapely as shp
import warnings
warnings.filterwarnings("ignore")
import helper_tools as ht


counties = ['Vinton']

# take 2 precint assignments for blocks and flag difference
for cty in counties:
    # get census block shapefile with precinct assignments
    shp_path = "/Users/jessicanyquist/Desktop/PGP/Vinton_County_census_block.shp"

    ht.delete_cpg(shp_path)
    df_shp = gpd.read_file(shp_path)
    
    # add a column to get if the precinct labels are the same (0) or different (1)
    df_shp['match'] = 0;
    
    col_1 = 'PREC_SHP'
    col_2 = 'precinct_p'
    
    # check if precinct columns are the same 
    for i in range(0,len(df_shp.index)):
        prec_1 = df_shp.at[i,col_1]
        prec_2 = df_shp.at[i,col_2].upper()
        if(prec_1 != prec_2):
            df_shp.at[i, 'match'] = 1
            
    result_path = '.Vinton_County_census_block_match.shp'
    ht.save_shapefile(df_shp, result_path)
        
        
        
   
