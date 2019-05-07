import time
import pandas as pd
import helper_tools as ht
import geopandas as gpd
from collections import Counter
import numpy as np

county = 'Adams'

start_path = '/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/PA'
#get census blocks with voter roll and VTD labels
fp = start_path + '/Precinct Data/' +county +' County/'+county+'_County_census_block.shp'
df = gpd.read_file(fp)

#get list of precincts from VTD column
vtds = df.NAMELSAD.unique()
vtds = np.asarray(vtds)
#initilize dict that will keep track of VR precincts for every VTD
vr_dict = {}
#for each precinct, look at every census block and which VR precinct they have
for vtd in vtds:
    count_dict = {}
    df_vtd = df[df['NAMELSAD'] == vtd]
    vr_precs = df_vtd.precinct.unique()
    df_vr = pd.DataFrame(df_vtd['precinct'].value_counts())
    for prec in vr_precs:
        count_dict[prec] = df_vr.precinct[prec]
    tot = sum(count_dict.values())
    count_dict_copy = count_dict
    for key in count_dict.keys():
        prop = count_dict[key] / tot
        if prop < .3:
            del count_dict_copy[key]
"""
having trouble ending up with a dict that only has precincts with >30% of census blocks
"""

    vr_dict[vtd] = [count_dict]
    vr_dict_reduced[vtd] = [count_dict_copy]
count_df = pd.DataFrame.from_dict(vr_dict,orient='index')    
#include proportions to this dict?

#print a list of precincts in this county that have 40-50% ranges? 30-50?

