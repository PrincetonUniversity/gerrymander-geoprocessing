# -*- coding: utf-8 -*-
"""
Created on Fri Jul 13 09:37:47 2018

@author: conno
"""

import geopandas as gpd
import pandas as pd
import re


elec_csv = './electionsVA_2016_General_VA.csv'

#%%

# Initialize election result dataframe
df = pd.read_csv(elec_csv)


#%%
def vtd(x):
    ''' Obtain the first 3 numbers representing the vtd for a given string'''
    match = re.match('^[0-9]{3}', x[:3])
    if match:
        return match[0]
    else:
        return ''
