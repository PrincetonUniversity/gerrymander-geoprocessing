import pandas as pd
import pysal as ps
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import shapely as shp
from shapely.geometry import MultiLineString
from shapely.geometry import LinearRing
from shapely.geometry import Point
sns.set()
import re
import operator
# import multiprocessing
# from functools import partial

# test

# %load_ext autoreload
# %autoreload 2 # autoreload all modules every time you run code
# %autoreload 0 # turn off autoreload

pgp = 'G:/Team Drives/princeton_gerrymandering_project/'

############################################
###### LOAD SHAPES #########################
############################################

# load PA whole state shape
states = gpd.read_file(pgp + 'mapping/all_state_boundaries/tl_2017_us_state.shp')
pa_bound = states.loc[states['NAME']=='Pennsylvania', 'geometry'].values[0]

# load PA district shapes, append PA whole state
pa_df = gpd.read_file(pgp + 'mapping/PA/dataverse/pa_final.shp')
pa_df = pa_df.append({'GEOID10': 'PA_bound', 'geometry': pa_bound}, ignore_index=True)
pa_df = pa_df.set_index('GEOID10')

pa_df['centroid'] = pd.Series(dtype=object)

for i, _ in pa_df.iterrows():
    poly = pa_df.loc[i, 'geometry']
    pa_df.loc[i, 'area'] = poly.area
    pa_df.loc[i, 'perimeter'] = poly.length
    pa_df.at[i, 'centroid'] = poly.centroid
    
    #%%
#############################################################################
###### SPLIT NON-CONTIGUOUS PRECINCTS ###
#############################################################################

# From Pegden's SI Text
#79 precincts that were not contiguous were split into
#continuous areas, with voting and population data distributed
#proportional to the area

capture_cols = ['VAP', 'POP100', '(?:USP|USS|USC|GOV|STS|STH)[DR]V[0-9]{4}']
capture_cols = [i for i in pa_df.columns if any([re.match(j, i) for j in capture_cols])]

def non_contiguous(geom):
    return geom.type == 'MultiPolygon'

# find non-contiguous precincts
non_contiguous = pa_df[pa_df['geometry'].apply(non_contiguous)==True].index


#%%
############################################
###### ROOK CONTIGUITY######################
############################################

w = ps.weights.Rook.from_dataframe(pa_df, geom_col='geometry')

pa_df['neighbors'] = pd.Series(dtype=object)
pa_df['shared_perims'] = pd.Series(dtype=object)

for i,_ in pa_df.iterrows():
    pa_df.at[i, 'neighbors'] = w.neighbors[i]

#%%


#############################################################################
###### PROCESS PRECINCTS FULLY CONTAINED IN OTHER PRECINCTS (donut holes) ###
#############################################################################

capture_cols = ['VAP', 'POP100', 'area', '(?:USP|USS|USC|GOV|STS|STH)[DR]V[0-9]{4}']
capture_cols = [i for i in pa_df.columns if any([re.match(j, i) for j in capture_cols])]

# get IDs of donut holes
donut_holes = pa_df[pa_df['neighbors'].apply(len)==1].index

for donut_hole in donut_holes:
    # find each hole's donut
    donut = pa_df.loc[donut_hole]['neighbors'][0]

    # hi ho the dairy-o, the donut eats the hole
    for col in capture_cols:
        pa_df.loc[donut, col] = pa_df.loc[donut, col] + pa_df.loc[donut_hole, col]

    # remove neighbor reference to donut hole
    donut_hole_index = pa_df.loc[donut, 'neighbors'].index(donut_hole)
    del(pa_df.loc[donut, 'neighbors'][donut_hole_index])

# the holes are gone
pa_df = pa_df.drop(donut_holes)





#%%

################################################
###### PUT NEIGHBOR LISTS IN CLOCKWISE ORDER ###
################################################

pa_df.loc['PA_bound', 'geometry'] = pa_df.loc['PA_bound', 'geometry'].boundary
#%%
precincts = dict()
for i,_ in pa_df.iterrows():
    precincts[i] = dict()
    precincts[i]['boundary'] = pa_df.loc[i, 'geometry'].boundary
    precincts[i]['lines'] = []
    precincts[i]['neighbors'] = []
    precincts[i]['used'] = []
    for j in pa_df.loc[i, 'neighbors']:
        shape = pa_df.loc[i, 'geometry'].intersection(pa_df.loc[j, 'geometry'])
        if shape.type == 'MultiLineString':
            new_shape = shp.ops.linemerge(shape)
            if new_shape.type == 'LineString':
                precincts[i]['lines'].append(new_shape)
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
            else:
                for line in new_shape.geoms:
                    precincts[i]['lines'].append(line)
                    precincts[i]['neighbors'].append(j)
                    precincts[i]['used'].append(False)
        elif shape.type == 'LineString':
            precincts[i]['lines'].append(shape)
            precincts[i]['neighbors'].append(j)
            precincts[i]['used'].append(False)
        elif shape.type == 'GeometryCollection':
            lines = []
            for k in shape.geoms:
                if k.type == 'LineString':
                    lines.append(k)
            if len(lines) == 1:
                precincts[i]['lines'].append(lines[0])
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
            elif len(lines)> 1:
                new_shape = shp.ops.linemerge(MultiLineString(lines))
                if new_shape.type == 'LineString':
                    precincts[i]['lines'].append(new_shape)
                    precincts[i]['neighbors'].append(j)
                    precincts[i]['used'].append(False)
                else:
                    for line in new_shape.geoms:
                        precincts[i]['lines'].append(line)
                        precincts[i]['neighbors'].append(j)
                        precincts[i]['used'].append(False)
            else:
                print('Uh oh, no lines!')
                print(i)
                print(j)
        else:
            print('Unexpected type')
            print(i)
            print(j)

#%%
# get the neighbors in order, possibly with duplicates

def getEndpoints(line_string):
    return [Point(line_string.xy[0][0], line_string.xy[1][0]), Point(line_string.xy[0][1], line_string.xy[1][1])]
 #%%
for i,_ in pa_df.iterrows():
    num_lines = len(precincts[i]['lines'])
    if len(num_lines <= 1):
        print ('Shoulda been a donut')
        continue
    
    new_neighbors = []
    new_lines = []
    index = 0
    
    for j in range(num_lines):
        new_neighbors.append(precincts['neighbors'][index])
        new_lines.append(precincts['lines'][index])
        endpoints = getEndpoints(precincts['lines'][index])
        

    
#%%
# drop full state bound
counter = -1
for i, _ in pa_df.iterrows():
    on_bound = ['PA_bound'==s for s in pa_df.loc[i, 'neighbors']]
    if any(on_bound):
        pa_df.loc[i, 'neighbors'][on_bound.index(True)] = counter
        counter -= 1
        

pa_df = pa_df.drop('PA_bound')
#%%
############################################
###### ASSIGN CONG. DISTRICTS TO PRECINCTS #
############################################

CDs = gpd.read_file(pgp + 'mapping/115th congress shapefiles/tl_2016_us_cd115.shp').set_index('CD115FP')
CDs = CDs.loc[CDs['STATEFP']=='42']
CDs.index = CDs.index.astype(int)

#%%

# construct r-tree spatial index
si = CDs.sindex

for i, _ in pa_df.iterrows():
    precinct = pa_df.loc[i, 'geometry']

    # check to see which possible CD intersections exist
    poss_CD = [CDs.index[i] for i in list(si.intersection(precinct.bounds))]
    if len(poss_CD) == 1:
        CD = poss_CD[0]
    else:
        # for cases with multiple matches, compare fractional area
        frac_area = {}
        found_majority = False
        for j in poss_CD:
            if not found_majority:
                area = CDs.loc[j, 'geometry'].intersection(precinct).area / precinct.area
                if area > .5:
                    found_majority = True
                frac_area[j] = area
        CD = max(frac_area.items(), key=operator.itemgetter(1))[0]

    pa_df.loc[i, 'CD'] = str(CD)


############################################
###### TOUCH-UPS ###########################
############################################

pa_df['sequential'] = range(len(pa_df))
seq_map = pa_df['sequential'].to_dict()

for i in [2851, 2852, 2853]:
    pa_df.loc[pa_df['sequential']==i, 'CD'] = '7'
    # NOTE: the problem here is that these three are contained in a non-contiguous precinct; oy

pa_df.to_pickle('padf_cw.pickle')
# pa_df = pd.read_pickle('padf.pickle')


for i, _ in pa_df.iterrows():
    for col in ['neighbors', 'shared_perims']:
        pa_df.loc[i, col].reverse()
        
#%%    
# cross reference populations and areas to get number of each precinct in Pegden's inputPA.txt
# for use in arcgis to see if there is a method to how he ordered the neighbors 
def getPegdenNumbers():
    numPrecincts = len(pa_df)
    pegdenNumbers = dict()
    pa_pop = np.array(pa_df['POP100'])
    peg_pop = np.array(peg_df['pop'])
    pop = np.where(peg_pop == pa_pop[: , np.newaxis])

    for i in range(len(pop[0])):
        j = pop[0][i]
        k = pop[1][i]
        if abs(peg_df['area'][k] - pa_df['area'][j]) < 1e-12:
            pegdenNumbers[j] = k
             
    return [pegdenNumbers[i] if i in pegdenNumbers.keys() else '*' for i in range(numPrecincts)]
    
#%%

#%%

############################################
###### EXPORT ##############################
############################################

f = open('chain_cw.txt', 'w')
f.write('precinctlistv01\n' + str(len(pa_df)) + '\n' + '\tnb\tsp\tunshared\tarea\tpop\tvoteA\tvoteB\tcongD\n')

def convert_geoid(x):
    if str(x)[0]=='-':
        # identifies VTDs at edge of state
        return str(x)
    else:
        return str(seq_map[x])

for _, row in pa_df.iterrows():
    f.write(str(row['sequential']) + '\t')

    f.write(convert_geoid(row['neighbors'][0]))
    if len(row['neighbors']) > 1:
        for i in row['neighbors'][1:]:
            f.write(',' + convert_geoid(i))
    f.write('\t')

    f.write(str(row['shared_perims'][0]))
    if len(row['shared_perims']) > 1:
        for i in row['shared_perims'][1:]:
            f.write(',' + str(i))

    f.write('\t0\t' + str(row['area']) + '\t' + str(round(row['POP100'])) + '\t' + str(round(row['USSDV2010'])) + '\t' + str(round(row['USSRV2010'])) + '\t' + row['CD'])
    f.write('\n')

f.close()

#%%
# for comparison, load in Pegden data
peg_df = pd.read_csv(pgp + 'pegden_algo/InputPA.txt',
                 sep='\t', header=2, names=['src', 'nbr', 'shared_perim', 'unshared', 'area', 'pop', 'voteA', 'voteB', 'congD'])


peg_df = peg_df.astype(dtype={'src': str, 'nbr': str})
peg_df['nbr'] = peg_df['nbr'].apply(lambda x: x.split(','))
peg_df['shared_perim'] = peg_df['shared_perim'].apply(lambda x: [float(i) for i in x.split(',')])
#%%


            
