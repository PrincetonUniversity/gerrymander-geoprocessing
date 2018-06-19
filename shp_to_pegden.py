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

# test2

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
###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)###
#############################################################################

# From Pegden's SI Text
# 79 precincts that were not contiguous were split into
# continuous areas, with voting and population data distributed
# proportional to the area

capture_cols = ['area', 'VAP', 'POP100', '(?:USP|USS|USC|GOV|STS|STH)[DR]V[0-9]{4}']
capture_cols = [i for i in pa_df.columns if any([re.match(j, i) for j in capture_cols])]

def non_contiguous(geom):
    return geom.type == 'MultiPolygon'

# find non-contiguous precincts
archipelagos = pa_df[pa_df['geometry'].apply(non_contiguous)==True].index

temp_pa_df = pd.DataFrame()

for archipelago in archipelagos:
    precinct = pa_df.loc[archipelago]['geometry']
    area = pa_df.loc[archipelago]['area']
    count = 0 # used for naming new precincts
    for region in precinct.geoms:
        new_index  = str(archipelago) + '_' + str(count)
        d = dict()
        d['GEOID10'] = new_index
        d['geometry']=region
        
        # adjust relevant fields by area proportion
        proportion = region.area/area
        for col in capture_cols:
            d[col] = proportion * pa_df.loc[archipelago][col]
        
        # an island declares its independence from the archipelago
        temp_pa_df = temp_pa_df.append(d, ignore_index = True)
        count = count + 1

# set index of temp dataframe to match original
temp_pa_df = temp_pa_df.set_index('GEOID10')

# merge datatframes
pa_df = pa_df.append(temp_pa_df)

# delete original precinct
pa_df = pa_df.drop(archipelagos)

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
# iterate over precincts
for i,_ in pa_df.iterrows():
    precincts[i] = dict() # lines, neighbors, used indexed the same
    precincts[i]['boundary'] = pa_df.loc[i, 'geometry'].boundary
    precincts[i]['lines'] = []
    precincts[i]['neighbors'] = []
    precincts[i]['used'] = []  # has been used in the reordering process so far
    
    # iterate over neighbors
    for j in pa_df.loc[i, 'neighbors']:
        shape = pa_df.loc[i, 'geometry'].intersection(pa_df.loc[j, 'geometry'])  # get bounday between precinct and neighbor
        if shape.type == 'MultiLineString':
            new_shape = shp.ops.linemerge(shape)  # merge connected LineStrings
            
            # if we get just one LineString, add it to the list
            if new_shape.type == 'LineString':
                precincts[i]['lines'].append(new_shape)
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
            # otherwise, add all LineStrings to the list
            else:
                for line in new_shape.geoms:
                    precincts[i]['lines'].append(line)
                    precincts[i]['neighbors'].append(j)
                    precincts[i]['used'].append(False)
                    
        elif shape.type == 'LineString':
            precincts[i]['lines'].append(shape)
            precincts[i]['neighbors'].append(j)
            precincts[i]['used'].append(False)

        elif shape.type == 'GeometryCollection':  # LineStrings and Points
            
            # get all LineStrings
            lines = []
            for k in shape.geoms:
                if k.type == 'LineString':
                    lines.append(k)
                    
            # if there is only one, add it to the list
            if len(lines) == 1:
                precincts[i]['lines'].append(lines[0])
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
                
            # otherwise, create a MultilineString and proceed as above
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

# May need to change to x,y ; x,y&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
def getEndpoints(line_string):
    return [Point(line_string.xy[0][0], line_string.xy[1][0]), Point(line_string.xy[0][1], line_string.xy[1][1])]
 #%%

# Connor+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
for i,_ in pa_df.iterrows():
    num_lines = len(precincts[i]['lines'])
    # Check for donut
    if num_lines <= 1:
        print('Should have been identified as a donut')
        continue

    # Initialize list of neighbors and lines in clockwise order
    # Let first neighbor/line be starting value
    new_neighbors = [precincts[i]['neighbors'][0]]
    new_lines = [precincts[i]['lines'][0]]
    index = 0

    # Set first neighbor/line to true
    precincts[i]['used'][0] = True

    # Set the current endpoint
    curr_endpt = getEndpoints(precincts[i]['lines'][0])[0]

    # Find a (counter-)clockwise order for the neighbors of the precinct
    # Loop until every neighbor has been used
    while(not all(precincts[i]['used'])):

        # Set minimum distance to -1 to initialize
        min_dist = -1

        # Find unused indexes for neighbors/lines
        unused_ix = [i for i, x in enumerate(precincts[i]['used']) if x==False]
        # Iterate through unused neighbors/lines
        for j in unused_ix:
            # Obtain endpoints and distances for line we are checking
            check_endpts = getEndpoints(precincts[i]['lines'][j])
            dist_endpt = [curr_endpt.distance(check_endpts[0]), 
                            curr_endpt.distance(check_endpts[1])]

            # If first line being checked or line has an endpoint closer to our
            # current endpoint, update the minimum distance, set index 
            # (neighbor) to this line, update proposed next endpoint to become 
            # current endpoint
            if(min(dist_endpt) < min_dist or min_dist == -1):
                min_dist = min(dist_endpt)
                index = j
                # Endpoint furthest from the current endpoint
                next_endpt = check_endpts[dist_endpt.index(max(dist_endpt))]

        # Update the new list of lines and neighbors. Set used = True
        new_neighbors.append(precincts[i]['neighbors'][index])
        new_lines.append(precincts[i]['lines'][index])
        precincts[i]['used'][index] = True

        # Update the current endpoint to the far endpoint of the closest line
        curr_endpt = next_endpt

    # We now have the neighbors in either counterclockwise or clockwise
    # Create a set of points to create a linear ring and form ccw
    endpts_ring = []

    # Inintialize first lines into the ring
    endpts_ring.append(getEndpoints(new_lines[0])[0])
    endpts_ring.append(getEndpoints(new_lines[0])[1])
    curr_endpt_ring = endpts_ring[1]

    for j in range(1, num_lines):
        # Obtain next endpoints in order and calculate distance
        next_endpts_ring = getEndpoints(new_lines[j])
        dist_endpt_ring = [curr_endpt_ring.distance(next_endpts_ring[0]), 
                        curr_endpt_ring.distance(next_endpts_ring[1])]
        # Determine which point to append first
        p1 = next_endpts_ring[dist_endpt_ring.index(min(dist_endpt_ring))]
        p2 = next_endpts_ring[dist_endpt_ring.index(max(dist_endpt_ring))]

        # Append min distance point first. max distance point becomes current
        endpts_ring.append(p1)
        endpts_ring.append(p2)
        curr_endpt_ring = p2

    # Create the linear rings in both direction
    lring1 = LinearRing(endpts_ring)
    lring1 = [pt.coords[0] for pt in lring1]
    lring2 = LinearRing(list(reversed(endpts_ring)))

    # Check Linear Ring Orientation
    if lring1.is_ccw:
        # since normal order is ccw, we must reverse orders
        new_neighbors = list(reversed(new_neighbors))
        new_lines = list(reversed(new_lines))
    elif not lring2.is_ccw:
        print('ERROR: Did not obtain a correct order')
        print(i)

    # Set new neighbors
    pa_df.loc[i]['neighbors'] = new_neighbors

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
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

# for i in [2851, 2852, 2853]:
#    pa_df.loc[pa_df['sequential']==i, 'CD'] = '7'
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


            
