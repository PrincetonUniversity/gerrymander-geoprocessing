import pandas as pd
import pysal as ps
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()
import re
import operator
# import multiprocessing
# from functools import partial

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

############################################
###### ROOK CONTIGUITY######################
############################################

w = ps.weights.Rook.from_dataframe(pa_df, geom_col='geometry')

pa_df['neighbors'] = pd.Series(dtype=object)
pa_df['shared_perims'] = pd.Series(dtype=object)
pa_df['angles'] = pd.Series(dtype=object)

# sort neighbors by angle
# TODO: angle probably is not a robust solution

def angle_between(centroid1, centroid2):
    lldiff = np.array(centroid1.coords[0]) - np.array(centroid2.coords[0])
    return np.arctan2(lldiff[1], lldiff[0])

for i,_ in pa_df.iterrows():
    pa_df.at[i, 'neighbors'] = w.neighbors[i]

    # find angles between neighbors
    pa_df.at[i, 'angles'] = [angle_between(pa_df.loc[i, 'centroid'], pa_df.loc[j, 'centroid']) for j in pa_df.loc[i, 'neighbors']]

    direction = -1 # -1 is CW, 1 is CCW
    idx = np.argsort(direction*np.array(pa_df.at[i, 'angles'])) # find sort index based on angle
    pa_df.at[i, 'angles'] = [pa_df.at[i, 'angles'][j] for j in idx] # sort angles
    pa_df.at[i, 'neighbors'] = [pa_df.at[i, 'neighbors'][j] for j in idx] # sort neighbors

    # unparallelized:
    pa_df.at[i, 'shared_perims'] = [pa_df.loc[i, 'geometry'].intersection(pa_df.loc[j, 'geometry']).length for j in pa_df.loc[i, 'neighbors']]


# attempt at parallelizing
# cores = 8
# chunks = np.array_split(pa_df[['neighbors', 'shapely']], cores)
# polygons = pa_df['shapely'].to_dict()
# neighbors = [i['neighbors'].to_dict() for i in chunks]
#
# def f(polygons, neighbors):
#     y = {}
#     for vtd, nb in neighbors.items():
#         y[vtd] = [polygons[vtd].intersection(polygons[j]).length for j in nb]# df.loc[i, 'shared_perims'] = [polygons[i].intersection(polygons.loc[j]).length for j in df.loc[i, 'neighbors']]
#     return df
#     # figure out why (i) i can't get this to use all cores, and (ii) why i have extra trouble doing it with pandas
#
# pool = multiprocessing.Pool(processes=cores) # declare pool after function
# result = pool.map(partial(f, polygons=polygons), chunks)
# pool.close()
# result


# drop full state bound
pa_df = pa_df.drop('PA_bound')


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
    del(pa_df.loc[donut, 'shared_perims'][donut_hole_index])

# the holes are gone
pa_df = pa_df.drop(donut_holes)

counter = -1
for i, _ in pa_df.iterrows():
    on_bound = ['PA_bound'==s for s in pa_df.loc[i, 'neighbors']]
    if any(on_bound):
        pa_df.loc[i, 'neighbors'][on_bound.index(True)] = counter
        counter -= 1

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



#%%
# for comparison, load in Pegden data
peg_df = pd.read_csv(pgp + 'pegden_algo/InputPA.txt',
                 sep='\t', header=2, names=['src', 'nbr', 'shared_perim', 'unshared', 'area', 'pop', 'voteA', 'voteB', 'congD'])


peg_df = peg_df.astype(dtype={'src': str, 'nbr': str})
peg_df['nbr'] = peg_df['nbr'].apply(lambda x: x.split(','))
peg_df['shared_perim'] = peg_df['shared_perim'].apply(lambda x: [float(i) for i in x.split(',')])
#%%

# cross reference populations and areas to get number of each precinct in Pegden's inputPA.txt
# for use in arcgis to see if there is a method to how he ordered the neighbors 
def getPegdenNumbers():
    numPrecincts = 9048
    pegdenNumbers = dict()
    pa_pop = np.array(pa_df['POP100'])
    peg_pop = np.array(peg_df['pop'])
    pop = np.where(peg_pop == pa_pop[: , np.newaxis])

    for i in range(len(pop[0])):
        j = pop[0][i]
        k = pop[1][i]
        if abs(peg_df['area'][k]/pa_df['area'][j] - 1) < 0.00001:
            pegdenNumbers[j] = k
            
    result = []
    for i in range(numPrecincts):
        if i in pegdenNumbers.keys():
            result.append(pegdenNumbers[i])
        else:
            result.append('*')
    return result
            
