# -*- coding: utf-8 -*-
"""
Created on Fri Jul 13 09:37:47 2018

@author: conno
"""

import geopandas as gpd
import pandas as pd
import re

# Initialize csv string
elec_csv = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Election Results/2016 November General.csv"

# Initialize shp file string
shp_path = 'G:/Team Drives/princeton_gerrymandering_project/mapping/VA/2010 Census/tl_2012_51_vtd10.shp'

# Election Year
year = '2016'

# Initialize candidate identification strings
cand1_fname = 'Donald'
cand1_lname = 'Trump'

cand2_fname = 'Hillary'
cand2_lname = 'Clinton'

# Initialize column string names from csv
fname_str = 'FirstName'
lname_str = 'LastName'
office_str = 'OfficeTitle'
votes_str = 'TOTAL_VOTES'
county_fips_str_raw = 'LocalityCode'
vtd_str_raw = 'PrecinctName'

#Initialize column string names for attribute table
county_fips_str_geo = 'COUNTYFP10'
vtd_str_geo = 'VTDST10'

# initialize strings that are in absentee and provisional
absentee_str = 'Absentee'
provisional_str = 'Provisional'

#%%

# Initialize election result dataframe
raw_df = pd.read_csv(elec_csv)




#%%
def vtd(x):
    ''' Obtain the first 3 numbers representing the vtd for a given string'''
    match = re.match('^[0-9]{3}', x[:3])
    if match:
        return match[0]
    elif absentee_str in x:
        return 'absentee'
    elif provisional_str in x:
        return 'provisional'
    else:
        return ''

#  Get VTD for every row
raw_df['VTD'] = raw_df[vtd_str_raw].apply(vtd)
raw_df['VTD'].astype(str)
raw_df[county_fips_str_raw].astype(str)

# Get name for every raw precinct
for i, _ in raw_df.iterrows():
    raw_df.at[i, 'precinct_name2'] = raw_df.at[i, vtd_str_raw].split(' - ')[-1]
    raw_df.at[i, 'precinct_name'] = raw_df.at[i, vtd_str_raw].split(' - ')[-1][:8]
    
def zero_if_multiple(x):
    if len(x)==1:
        return x
    else:
        return 0
    
raw_pivot = raw_df.pivot_table(index=[county_fips_str_raw, 'precinct_name'], \
                               columns=[lname_str, fname_str, office_str],\
                          values=votes_str, aggfunc=zero_if_multiple)
raw_pivot = raw_pivot[[cand1_lname, cand2_lname]]
raw_pivot[cand1_lname] = raw_pivot[cand1_lname].fillna(0)
raw_pivot[cand2_lname] = raw_pivot[cand2_lname].fillna(0)

raw_pivot.to_csv('./Result_2016_test.csv')
#%% Check both name and FIP
# =============================================================================

# geo_df = gpd.read_file(shp_path)
# geo_df[year + '_' + cand1_lname] = pd.Series(dtype=object)
# geo_df[year + '_' + cand2_lname] = pd.Series(dtype=object)
# 
# # Make all VTDs be a string of length 3
# geo_df[vtd_str_geo] = geo_df[vtd_str_geo].apply(lambda x: str(int(x)).zfill(3)) 
# 
# # iterate through every precinct
# for i, row in geo_df.iterrows():
#     # Set index from geo_df
#     index = (int(row[county_fips_str_geo]), row[vtd_str_geo], row['NAME10'].upper())
#     # Iterate through both candidates
#     for cand in [cand1_lname, cand2_lname]:
#         if index in raw_pivot.index:
#             geo_df.at[i, year + '_' + cand] = raw_pivot.loc[index][cand][0]
#         else:
#             if len(row[vtd_str_geo]) == 4 and (index[0], index[1][:3], index[2]) in raw_pivot.index:
#                 # some VTDs come in multiple parts in the shapefile but are merged in the OE file.
#                 # for a VTD coded in OE as '402', the VTDST10 codes will be '4021' and '4022'
#                 # this is a hack because i know that repeat VTDS only come in pairs.
#                 # TODO: have this check for the number of multipart VTDs
#                 geo_df.at[i, year + '_' + cand] = raw_pivot.loc[(index[0], index[1][:3], index[2])][cand][0] / 2 
#             else:
#                 geo_df.at[i, year + '_' + cand] = None
# =============================================================================
                
# =============================================================================
# geo_df = gpd.read_file(shp_path)
# geo_df[year + '_' + cand1_lname] = pd.Series(dtype=object)
# geo_df[year + '_' + cand2_lname] = pd.Series(dtype=object)
# 
# # Make all VTDs be a string of length 3
# geo_df[vtd_str_geo] = geo_df[vtd_str_geo].apply(lambda x: str(int(x)).zfill(3)) 
# 
# # iterate through every precinct
# for i, row in geo_df.iterrows():
#     # Set index from geo_df
#     index = (int(row[county_fips_str_geo]), row['NAME10'].upper()[:8])
#     # Iterate through both candidates
#     for cand in [cand1_lname, cand2_lname]:
#         if index in raw_pivot.index:
#             geo_df.at[i, year + '_' + cand] = raw_pivot.loc[index][cand][0]
#         else:
#             geo_df.at[i, year + '_' + cand] = None
# =============================================================================

#%%


#print(sum(geo_df[year + '_' + cand1_lname].isnull()) / len(geo_df))






















