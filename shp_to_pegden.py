import pandas as pd
import pysal as ps
import numpy as np
import geopandas as gpd
import shapely as shp
from shapely.geometry import MultiLineString
from shapely.geometry import Point
from shapely.geometry import LinearRing
from shapely.geometry import LineString
from shapely.geometry import Polygon
import re
import operator
import pickle

# !!!Add from shapelygeometry shg

# Select state
state = 'VA'

# Info is text before state for filenames
info = ''

# Define paths
pgp = 'G:/Team Drives/princeton_gerrymandering_project/'
pgp_state = "mapping/VA/2010 Census/Dataverse_with_geom.shp"
output_text_file = state + '_Pegden_Input.txt'

# Which fields from the shapefile do we need?
D_string = 'PRES_DVOTE'
R_string = 'PRES_RVOTE'
pop_string = 'POPTOT_00'

# Add population from census
census_pop = True
census_file = 'mapping/VA/2010 Census/CensusBlocksPopTake2/tabblock2010_51'\
                '_pophu.shp'
c_pop_string = 'POP10'
# Determine which columns to keep 
# Could be adapted to keep more, but Pegden wiil run with D_string and R_string
capture_cols = [D_string, R_string, pop_string]

state_to_FIPS = {
  "AK": "02",
  "AL": "01",
  "AR": "05",
  "AS": "60",
  "AZ": "04",
  "CA": "06",
  "CO": "08",
  "CT": "09",
  "DC": "11",
  "DE": "10",
  "FL": "12",
  "GA": "13",
  "GU": "66",
  "HI": "15",
  "IA": "19",
  "ID": "16",
  "IL": "17",
  "IN": "18",
  "KS": "20",
  "KY": "21",
  "LA": "22",
  "MA": "25",
  "MD": "24",
  "ME": "23",
  "MI": "26",
  "MN": "27",
  "MO": "29",
  "MS": "28",
  "MT": "30",
  "NC": "37",
  "ND": "38",
  "NE": "31",
  "NH": "33",
  "NJ": "34",
  "NM": "35",
  "NV": "32",
  "NY": "36",
  "OH": "39",
  "OK": "40",
  "OR": "41",
  "PA": "42",
  "PR": "72",
  "RI": "44",
  "SC": "45",
  "SD": "46",
  "TN": "47",
  "TX": "48",
  "UT": "49",
  "VA": "51",
  "VI": "78",
  "VT": "50",
  "WA": "53",
  "WI": "55",
  "WV": "54",
  "WY": "56"}

FIPS = state_to_FIPS[state]


# %%
##############################################################################
###### LOAD SHAPES ###########################################################
##############################################################################

# load PA district shapes, append PA whole state, set GEOID10 as index
df = gpd.read_file(pgp + pgp_state)

state_bound = shp.ops.cascaded_union(df['geometry'])

df = df.append({'GEOID10': 'state_bound', 'geometry': state_bound}, 
                     ignore_index=True)
df = df.set_index('GEOID10')

df['area'] = pd.Series(dtype=object)

df.to_pickle('./' + info + state + '_load_shapes.pkl')

#%%
df = pd.read_pickle('./' + info + state + '_load_shapes.pkl')
#
# Calculate area for each precinct
for i, _ in df.iterrows():
    #print(i)
    poly = df.at[i, 'geometry']
    df.at[i, 'area'] = df.at[i, 'geometry'].area
    #df.set_value(i, 'area', poly.area)
 
###############################################################################
###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)###########################
###############################################################################

#  Create helper function to identify Multi-Polygons
def non_contiguous(geom):
    ''' Argument is a shape. Returns 1 if shape is a MultiPolygon. Returns 0
    if shape is not a MultiPolygon'''
    return geom.type == 'MultiPolygon'

# Find indexes of non-contiguous precincts
archipelagos = df[df['geometry'].apply(non_contiguous)==True].index

# Create a temporary data frame for the redefined split up precincts
temp_df = pd.DataFrame()

# Iterate through each of the non-contiguous precincts
for archipelago in archipelagos:
    # Get shape and area of current precinct
    precinct = df.at[archipelago, 'geometry']
    
    if archipelago == 'state_bound':
        print('HERE!!')
    
    area = df.at[archipelago, 'area']
    
    # count assists in "new" (split) precincts name creation
    count = 0
    
    # iterate through every polygon in the precinct
    for region in precinct.geoms:
        # New names will be original-name_count
        new_index  = str(archipelago) + '_' + str(count)
        
        # Set new index and shape in temporary dictionary
        d = dict()
        d['GEOID10'] = new_index
        d['geometry']= region
        
        # Adjust relevant fields by proportion of area
        proportion = region.area/area
        
        # Set column values proportional to the regions area
        for col in capture_cols:
            d[col] = proportion * df.at[archipelago, col]

        # Append split precinct from to temporary dataframe
        temp_df = temp_df.append(d, ignore_index = True)
        count += 1

# set index of temp dataframe to match original
temp_df = temp_df.set_index('GEOID10')

# merge datatframes
df = df.append(temp_df)

# delete original precinct rows
df = df.drop(archipelagos)

###############################################################################
###### QUEEN CONTIGUITY########################################################
###############################################################################

# Obtain queen continuity for each shape in the dataframe. We will remove all
# point contiguity. Shapely rook contiguity sometimes assumes lines with small
# lines are points
w = ps.weights.Queen.from_dataframe(df, geom_col='geometry')

# Initialize neighbors and shared_perims columns
new_cols = ['neighbors', 'shared_perims']
for column in new_cols:
    df[column] = pd.Series(dtype=object)

# Initialize neighbors for each precinct
for i,_ in df.iterrows():
    df.at[i, 'neighbors'] = w.neighbors[i]

# Save df after contiguity
df.to_pickle('./' + info + state + '_after_queen.pkl')

#%%
# Load df after contiguity
df = pd.read_pickle('./' + info + state + '_after_queen.pkl')

# Iterate through every precinct to remove all neighbors that only share a 
# single point. Rook contiguity would asssume some lines are points, so we
# have to use queen and then remove points
for i,_ in df.iterrows():
    
    # Obtain degree (# neighbors) of precinct
    nb_len = len(df.at[i, 'neighbors'])
    
    # Iterate through neighbor indexes in reverse order to prevent errors due
    # to the deletion of elements
    for j in range(nb_len - 1, -1, -1):
        # get the jth neighbor
        j_nb = df.at[i, 'neighbors'][j]
        
        # get the geometry for both precincts
        i_geom = df.at[i, 'geometry']
        j_nb_geom = df.at[j_nb, 'geometry']
        
        # If their intersection is a point, delete j_nb from i's neighbor list
        # do not delete in both directions. That will be taken care of
        # eventually when i = j_nb later in the loop or before this occurs
        if i_geom.intersection(j_nb_geom).type == 'Point':
            del df.at[i, 'neighbors'][j]

# Save df after removing point contiguity
df.to_pickle('./' + info + state + '_point_nb_deletion.pkl')

#%%
###############################################################################
###### MERGE PRECINCTS FULLY CONTAINED IN OTHER PRECINCTS #####################
###############################################################################

# Load df after removing point contiguity
df = pd.read_pickle('./' + info + state + '_point_nb_deletion.pkl')

# Notes: If running in sections, Capture Columns are defined above. Also, we
# are not adding the geometry when combining the precincts. We are just 
# combining area and other capture columns


# Donut Hole Precinct Check
# Get IDs of donut holes with only one neighbor
donut_holes = df[df['neighbors'].apply(len)==1].index
    
# Loop until no more donuts exist. Must loop due to concentric precincts
while len(donut_holes) != 0:
    # Iterate over each donut hole precinct
    for donut_hole in donut_holes:
        # find each donut's surrounding precinct
        donut = df.at[donut_hole, 'neighbors'][0]
    
        # Combine donut hole precinct and surrounding precinct capture columns
        for col in capture_cols:
            df.at[donut, col] = df.at[donut, col] + \
                                        df.at[donut_hole, col]
    
        # remove neighbor reference to donut hole precinct and delete
        donut_hole_index = df.at[donut, 'neighbors'].index(donut_hole)
        del(df.at[donut, 'neighbors'][donut_hole_index])
    
    # Drop the rows in the dataframe for the donut holes that existed
    df = df.drop(donut_holes)
    
    # get IDs of new donut holes created
    donut_holes = df[df['neighbors'].apply(len)==1].index

# Multiple Contained Precincts Check
# Create list of rows to drop at the end of the multiple contained check
ids_to_drop = []

# Iterate over all precincts except the state boundary precinct
for i,_ in df.iterrows():
    if i == 'state_bound':
        continue
    
    # Create polygon Poly for this precinct from its exterior coordinates. This
    # polygon will be filled without an interior. The purpose of filling
    # the interior is to allow for an intersection to see if a neighbor is
    # fully contained
    poly_coords = list(df.at[i, 'geometry'].exterior.coords)
    poly = Polygon(poly_coords)
    
    # Create list of contained neighbor id's to delete
    nb_ix_del = []

    # Define a list that contains possibly contained precincts. If a precint
    # is nested witin other contained precincts, we will need to add it to
    # this list
    possibly_contained = df.at[i, 'neighbors']
    for j in possibly_contained:        
        
        # Check if the intersection of Poly (precint i's full polygon) and the
        # current neighbor is equal to the current neighbor. This demonstrates
        # that the current neighbor is fully contained within precinct i
        j_geom = df.at[j, 'geometry']
        
        if j_geom == j_geom.intersection(poly):
            # j is fully contained within i. To account for nested precincts
            # we append any neighbor of j that is not already in possibly_
            # contained not including i
            for j_nb in df.at[j, 'neighbors']:
                if j_nb not in possibly_contained and j_nb != i:
                    possibly_contained.append(j_nb)

            # Add capture columns from neighbor to precinct i
            for col in capture_cols:
                df.at[i, col] = df.at[i, col] + df.at[j, col]
                        
            # add neighbor reference from precinct i to delete if a neighbor
            if j in df.at[i, 'neighbors']:
                nb_ix = df.at[i, 'neighbors'].index(j)
                nb_ix_del.append(nb_ix)
            
            # add neighbor precinct to the ID's to be dropped
            ids_to_drop.append(j)
            
    # Delete neighbor references from precinct i
    if len(nb_ix_del) > 0:
        # iterate through indexes in reverse to prevent errors through deletion
        for nb_ix in reversed(nb_ix_del):
            del(df.at[i, 'neighbors'][nb_ix])

# Drop contained precincts from the dataframe
df = df.drop(ids_to_drop)

# Save df after merge_contained
df.to_pickle('./' + info + state + '_merge_contained.pkl')


#%%
###############################################################################
###### PUT NEIGHBOR LISTS IN CLOCKWISE ORDER ##################################
###############################################################################

# Load df after merge_contained
df = pd.read_pickle('./' + info + state + '_merge_contained.pkl')

# Set the state border precinct to just be its boundary
df.at['state_bound', 'geometry'] = df.at['state_bound', 'geometry'].boundary


# Define helper function to get endpoints of strings
def getEndpoints(line_string):
    ''' Takes in a LineString as an argument. Returns A list that contains
    two points, which are the endpoints of the linestring'''
    return [Point(line_string.xy[0][0], line_string.xy[1][0]), 
                Point(line_string.xy[0][-1], line_string.xy[1][-1])]

# Initialize precincts as a dictionary
precincts = dict()

# iterate over each precinct
for i,_ in df.iterrows():
    
    # Initialize each precinct's geoID to be a key in the precincts dictionary
    precincts[i] = dict() # lines, neighbors, used indexed the same
    
    # Initialize four lists, which will have indexes that are aligned. Lines
    # will be the actual geometry, neighbors will be the index of the neighbor
    # precint, used will be whether or not boundary with a neighbor has been
    # sorted, and shared_perims is the length of the boundary with said
    # neighbor
    precincts[i]['lines'] = []
    precincts[i]['neighbors'] = []
    precincts[i]['used'] = []  # has been used in the reordering process so far
    precincts[i]['shared_perims'] = []
    
    # Iterate over the neighbors of precinct i
    for j in df.at[i, 'neighbors']:
        
        # Obtain the boundary between the current precinct and its j neighbor
        shape = df.at[i, 'geometry'].intersection(df.at[j, 'geometry'])
        
        # Account for all the different possible types shape could have. In
        # each case append the geometry to lines, neighbor index to neighbors,
        # a false used index, and the border length to shared perimeters
        if shape.type == 'MultiLineString':
            # attempt to merge combine the multiline string
            new_shape = shp.ops.linemerge(shape)  # merge connected LineStrings
            
            # If merge is successful, we have a single linestring
            # Note: merge will only be successful if vertices are shared
            if new_shape.type == 'LineString':
                precincts[i]['lines'].append(new_shape)
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
                precincts[i]['shared_perims'].append(new_shape.length)
            # Merge unsuccessful. loop through each of the shapes
            else:
                for line in new_shape.geoms:
                    precincts[i]['lines'].append(line)
                    precincts[i]['neighbors'].append(j)
                    precincts[i]['used'].append(False)
                    precincts[i]['shared_perims'].append(line.length)
                    
        # Single line case
        elif shape.type == 'LineString':
            precincts[i]['lines'].append(shape)
            precincts[i]['neighbors'].append(j)
            precincts[i]['used'].append(False)
            precincts[i]['shared_perims'].append(shape.length)
            
        # LineStrings and Points Case
        elif shape.type == 'GeometryCollection':
            
            # Extract all of the LineStrings from the Geometry
            lines = []
            for k in shape.geoms:
                if k.type == 'LineString':
                    lines.append(k)
                    
            # One LineString Case
            if len(lines) == 1:
                precincts[i]['lines'].append(lines[0])
                precincts[i]['neighbors'].append(j)
                precincts[i]['used'].append(False)
                precincts[i]['shared_perims'].append(lines[0].length)
                
            # Multiple Lines case
            elif len(lines)> 1:
                # Convert lines into a MultLine and attempt to merge
                new_shape = shp.ops.linemerge(MultiLineString(lines))
                
                # Successful merge
                if new_shape.type == 'LineString':
                    precincts[i]['lines'].append(new_shape)
                    precincts[i]['neighbors'].append(j)
                    precincts[i]['used'].append(False)
                    precincts[i]['shared_perims'].append(new_shape.length)
                    
                # Unsuccessful merge
                else:
                    for line in new_shape.geoms:
                        precincts[i]['lines'].append(line)
                        precincts[i]['neighbors'].append(j)
                        precincts[i]['used'].append(False)
                        precincts[i]['shared_perims'].append(line.length)

# Iterate over each precinct. i is the GEOID10 of each precinct. Update
# neighbor lists such that they are in counterclockwise order
for i,_ in df.iterrows():

    # Initialize lists that will sort the neighbors, lines, and perimeters
    # in clockwise order by appending the first element to the list
    new_neighbors = [precincts[i]['neighbors'][0]]
    new_lines = [precincts[i]['lines'][0]]
    new_shared_perims = [precincts[i]['shared_perims'][0]]
    
    # Set first neighbor/line/perim to true since it was initialized above
    precincts[i]['used'][0] = True
    
    # We will first sort the neighbors into a directional order (clockwise or
    # counter-clockwise) We will then check which direction our order is in
    # and then switch it if necessary

    # Helper variable to determine which neighbor comes next in the direction
    # we are outlining
    index = 0

    # Set the current endpoint to be the first endpoint of the 1st line
    curr_endpt = getEndpoints(precincts[i]['lines'][0])[0]

    # Find an order for the neighbors. We loop until every line on precint i's
    # boundary has been used
    while(not all(precincts[i]['used'])):
        
        # Find indexes for neighbors/lines/perims that have not been used
        unused_ix = [i for i, used in enumerate(precincts[i]['used']) if \
                     not used]
        
        # Initialize minimum distance to -1. This case demonstrates that a
        # distance has yet to be calculated
        min_dist = -1
    
        # Iterate through indexes of unused neighbors/lines/perims
        for j in unused_ix:
            # Obtain endpoints and distances for the line being checked
            check_endpts = getEndpoints(precincts[i]['lines'][j])
            dist_endpt = [curr_endpt.distance(check_endpts[0]), 
                            curr_endpt.distance(check_endpts[1])]

            # If either (1) this is the first line to be checked for precinct
            # i or (2) the line being checked has an endpoint closer to our
            # current endpoint, update the min distance, set index to this
            # neighbor/line/perim, and update the proposed next endpoint to
            # be the endpoint of the line being checked that is furthest from
            # the current endpoint
            if(min(dist_endpt) < min_dist or min_dist == -1):
                min_dist = min(dist_endpt)
                index = j
                next_endpt = check_endpts[dist_endpt.index(max(dist_endpt))]

        # Update the new list of neighbors/lines/perims and update used value
        # to be equal to TRUE
        new_neighbors.append(precincts[i]['neighbors'][index])
        new_lines.append(precincts[i]['lines'][index])
        new_shared_perims.append(precincts[i]['shared_perims'][index])
        precincts[i]['used'][index] = True
        
        # Update the current endpoint to the far endpoint of the closest line
        curr_endpt = next_endpt

    # The neighboring precincts are now organized in either clockwise or 
    # counterclockwise order. We will use a LinearRing to check which direction
    # they are organized in, and reverse the order if necessary
        
    # Initialize the list of endpoints that will form the ring. The real_ring
    # will contain all the coordinates of every line on precinct i's boundary
    endpts_ring = []
    real_ring = []
    
    # Initialize the first line into the endpts ring. Make sure that we start
    # endpoints in the correct direction
    
    # Get the endpoints for the 0th and 1st line in the new lines array
    line0 = getEndpoints(new_lines[0])
    line1 = getEndpoints(new_lines[1])
    
    # Get the endpoints for each line
    line0_e0 = line0[0]
    line0_e1 = line0[1]
    line1_e0 = line1[0]
    line1_e1 = line1[1]
    
    # Check which endpoint is closest to line1. The closer endpoint will be
    # the second point appended in the endpts_ring array to ensure that
    # we start the ring in the correct direction
    line0_e0_dist = min(line0_e0.distance(line1_e0), 
                        line0_e0.distance(line1_e1))
    line0_e1_dist = min(line0_e1.distance(line1_e0), 
                        line0_e1.distance(line1_e1))
    
    # if one endpoint is closer, add the lines coordinates in the opposite
    # order. If line0_e0 is closer to line 1 than line0_e1, we reverse the
    # coordinate order. If it is theo other way around, we do not reverse
    # the coordinate order
    if line0_e0_dist < line0_e1_dist:
        endpts_ring.append(line0_e1)
        endpts_ring.append(line0_e0)
        real_ring += list(reversed(list(new_lines[0].coords)))
    else:
        endpts_ring.append(line0_e0)
        endpts_ring.append(line0_e1)
        real_ring += list(new_lines[0].coords)
    
    # Set the current endpoint for the ring. We will measure the distance of
    # the endpoints of the next line to this endpoint to see which endpoint
    # comes first in terms of the ring
    curr_endpt_ring = endpts_ring[1]
    
    # iterate through all of the lines other than the 0th line
    for j in range(1, len(precincts[i]['lines'])):
        # Obtain next endpoints and calculate distance from current endpoint
        next_endpts_ring = getEndpoints(new_lines[j])
        dist_endpt_ring = [curr_endpt_ring.distance(next_endpts_ring[0]), 
                        curr_endpt_ring.distance(next_endpts_ring[1])]
        
        # Determine which point to append first. Append min distance point
        # first. The max distance point becomes the current endpoint
        p1 = next_endpts_ring[dist_endpt_ring.index(min(dist_endpt_ring))]
        p2 = next_endpts_ring[dist_endpt_ring.index(max(dist_endpt_ring))]
        endpts_ring.append(p1)
        endpts_ring.append(p2)
        curr_endpt_ring = p2
        
        # Add coordinates to the real_ring. Need to reverse if p1 equals the
        # second endpoint
        if p1 == next_endpts_ring[0]:
            real_ring += list(new_lines[j].coords)
        else:
            real_ring += list(reversed(list(new_lines[j].coords)))
                
    # Create the linear rings in both direction
    lring1 = real_ring
    lring2 = list(reversed(lring1))
    
    # If LinearRing orientation is counter-clockwise, reverse neighbors/lines/
    # perims
    if LinearRing(lring1).is_ccw:
        # since normal order is ccw, we must reverse orders
        new_neighbors = list(reversed(new_neighbors))
        new_lines = list(reversed(new_lines))
        new_shared_perims = list(reversed(new_shared_perims))
    # If LinearRing is not clockwise or counterclockwise print error
    elif not LinearRing(lring2).is_ccw:
        print('ERROR: Did not obtain a correct order')
        print(i)

    # Since we appended for MultiLineStrings, we may have duplicate neighbors
    # in our lists. i.e. precincts that appear to border themselves. If a 
    # precinct appears to border itself, delete that instance and add the 
    # perimeters.
    
    # Use this loop index to correctly iterate since deletions are being made
    loop_ix = 0
    
    # Loop through the new neighbors array that contains duplicates
    for ix in range(len(new_neighbors)):
        # Get the index for the next element. Modulo so last element can
        # check the first element
        next_ix = (loop_ix + 1) % len(new_neighbors)
        
        # If a repeat occurs, sum perimeters, and delete duplicate. Do not
        # increment the loop index to account for deletion
        if new_neighbors[loop_ix] == new_neighbors[next_ix]:
            new_shared_perims[loop_ix] += new_shared_perims[next_ix]
            del new_neighbors[next_ix]
            del new_shared_perims[next_ix]
            
        # Increment loop index because no deletion was necessary
        else:
            loop_ix +=1
    
    # Set new_neighbors array into the dataframe
    df.at[i, 'neighbors'] = new_neighbors
    df.at[i, 'shared_perims'] = new_shared_perims

# Save df after sorting neighbors in clockwise order
df.to_pickle('./' + info + state + '_after_clockwise.pkl')

#%%
###############################################################################
###### PUT BOUNDARY LISTS IN NEGATVIE COUNTER-CLOCKWISE ORDER #################
###############################################################################

# Load df after sorting neighbors in clockwise order
df = pd.read_pickle('./' + info + state + '_after_clockwise.pkl')

# Initialzie negative counter. This will be the value assigned to state
# boundaries
counter = -1

# Find an initial precinct on the state boundary
for i, _ in df.iterrows():
    # find a starting border that only touches the border once
    if df.at[i, 'neighbors'].count('state_bound') == 1:
        break

# set the initial GEOID10 so we know once we have looped around the entire 
# state
initial = i

pr = initial
first_pr = True

# we need to initialize a value of last precinct for the initial comparison
last_pr = 0
while True:
    total = 0
    # Get the degree of the new precinct for mod division
    nb_len = len(df.at[pr, 'neighbors'])
    
    # iterate through all of the neighbors. Find the neighbor that is
    # 'state_bound' and its clockwise neighbor is the last precinct
    for j in range(nb_len):
        # Get value of the neighbor precinct (bound) and the neighbor that
        # is one precinct clockwise of the neighbor of the neighbor precinct
        bound = df.at[pr,'neighbors'][j]
        cw_pr = df.at[pr,'neighbors'][(j + 1) % nb_len]
        
        # Find the correct neighbor as explained above or enter if it is the
        # initial case when a last precinct does not exist
        if (cw_pr == last_pr and bound == 'state_bound') or \
        (first_pr and bound == 'state_bound'):
            first_pr = False
            
            # Set value of border and decrement counter
            df.at[pr, 'neighbors'][j] = counter
            counter -= 1

            # Update the precinct values. New precinct is the counter-clockwise
            # neighbor of the last precinct
            last_pr = pr
            pr = df.at[pr, 'neighbors'][(j - 1) % nb_len]
            
            # This is the case when the counterclockwise nb (now pr) ends up 
            # only touching the boundary on a point
            nb_point_case = True
            
            # Define which edge touches the border. Even at a point to deal
            # with queen contiguity on border
            touches_border = j
            
            # Loop until we find a precinct that meets the boundary in a line            
            while nb_point_case:
                # We will obtain shared perimeters to ensure that the boundary
                # we are checking between last_pr and pr has the correct index
                # due to precincts being able to be each others neighbors 
                # multiple times
                
                # get the shared perimeter of precinct
                pr_shared_perim = df.at[last_pr, 'shared_perims'][\
                                       (touches_border - 1) % nb_len]
                
                # Iterate through all of the indexes of pr neighbors looking
                # for the last precinct
                k_nb_len = len(df.at[pr, 'neighbors'])
                for k in range(k_nb_len):
                    
                    # Check that neighbor is the last precinct and that the
                    # shared perimeter is equal
                    
                    # Check if the current neighbor is the last precinct and
                    # that the shared perimeter is equal
                    if df.at[pr, 'neighbors'][k] == last_pr:
                        nb_shared_perim = df.at[pr, 'shared_perims'][k]
                        if abs(nb_shared_perim - pr_shared_perim) < 1e-8:
                            # Reset index that touches edge in case this
                            # is not a state_bound
                            touches_border = k
                            
                            # Check that the precinct that is one neighbor
                            # counter-clockwise is the boundary. 
                            if df.at[pr, 'neighbors'][(k - 1) % k_nb_len] \
                            == 'state_bound':
                                nb_point_case = False
                                
                            # The counter-clockwise neighbor is not the
                            # boundary, so we have the point case in which we
                            # need to shift last_pr and pr by one precinct
                            # counter-clockwise and check again until we no
                            # longer have a boundary point case
                            else:
                                last_pr = pr
                                pr = df.at[pr, 'neighbors'][(k - 1) % \
                                             k_nb_len]
                                
                                # Exit while loop if we have went over every
                                # boundary
                                if pr == -1:
                                    nb_point_case = False
                                    
                            # Leave the for loop that iterates with k
                            break
            # Break because we do not need to check the remaining neighbors
            break
        
    # Prevent being stuck in an infinite while loop. Keeps assumption that a
    # precinct will not have 1000 neighbors
    total += 1
    if total > 1000:
        print('STUCK')
        break
    
    # Leave the entire loop once every boundary has been accounted for
    if pr == -1:
        break
    
    # Print
    if pr == '51685002_1':
        break
# Remove the state boundary "precinct"
df = df.drop('state_bound')

# Save df after boundary counter-clockwise sort
df.to_pickle('./' + info + state + '_after_boundary.pkl')
#%%
############################################
###### ASSIGN CONG. DISTRICTS TO PRECINCTS #
############################################

# Load df after boundary counter-clockwise sort
df = pd.read_pickle('./' + info + state + '_after_boundary.pkl')

# Assign congressional districts
CDs = gpd.read_file(pgp + \
 'mapping/115th congress shapefiles/tl_2016_us_cd115.shp').set_index('CD115FP')
CDs = CDs.loc[CDs['STATEFP'] == FIPS]
CDs.index = CDs.index.astype(int)

# construct r-tree spatial index. Creates minimum bounding rectangle about
# each district
si = CDs.sindex

# iterate through every precinct, i is the GEOID10 of the precinct
for i, _ in df.iterrows():
    # let precinct equal the geometry of the precinct. Note: later
    # precinct.bounds is the minimum bounding rectangle for the precinct
    precinct = df.at[i, 'geometry']
    
    # Find which MBRs for districts intersect with our precincts MBR
    # MBR: Minimum Bounding Rectangle
    poss_CD = [CDs.index[i] for i in list(si.intersection(precinct.bounds))]
    
    # If precinct's MBR only intersects one district's MBR, set the district
    if len(poss_CD) == 1:
        CD = poss_CD[0]
    else:
        # for cases with multiple matches, compare fractional area
        frac_area = {}
        found_majority = False
        for j in poss_CD:
            if not found_majority:
                area = CDs.at[j, 'geometry'].intersection(precinct).area / \
                        precinct.area
                # Majority area means, we can assign district
                if area > .5:
                    found_majority = True
                frac_area[j] = area
        CD = max(frac_area.items(), key=operator.itemgetter(1))[0]

    # Assign the district to the precinct
    df.at[i, 'CD'] = str(CD)

# Save df after boundary counter-clockwise sort
df.to_pickle('./' + info + state + '_after_CD_assign.pkl')

#%%
###############################################################################
###### Assign Census Blocks To Precincts and Get Population####################
###############################################################################

# Load df after boundary counter-clockwise sort
df = pd.read_pickle('./' + info + state + '_after_CD_assign.pkl')

if census_pop:
    # read in census file
    c_df = gpd.read_file(pgp + census_file)
    c_df.to_pickle('./' + info + state + '_load_census.pkl')

    # initialize population to zero
    df[pop_string] = 0
    
    # construct spatial tree for precincts
    pr_si = df.sindex
    
    # iterate through every census block, i is the GEOID10 of the precinct
    for i, _ in c_df.iterrows():

        # let census_block equal the geometry of the censu_block. Note: later
        # census_block.bounds is the minimum bounding rectangle for the cb
        census_block = c_df.at[i, 'geometry']
        
        # Find which MBRs for districts intersect with our cb MBR
        # MBR: Minimum Bounding Rectangle
        poss_pr = [df.index[i] for i in \
                   list(pr_si.intersection(census_block.bounds))]
        
        # If precinct MBR only intersects one district's MBR, set the district
        if len(poss_pr) == 1:
            PR = poss_pr[0]
        else:
            # for cases with multiple matches, compare fractional area
            frac_area = {}
            found_majority = False
            for j in poss_pr:
                if not found_majority:
                    area = df.at[j, 'geometry'].intersection(census_block).area / \
                            census_block.area
                    # Majority area means, we can assign district
                    if area > .5:
                        found_majority = True
                    frac_area[j] = area
            PR = max(frac_area.items(), key=operator.itemgetter(1))[0]
    
        # Add population to precinct
        df.at[PR, pop_string] += c_df.at[i, c_pop_string]



############################################
###### TOUCH-UPS ###########################
############################################

df['sequential'] = range(len(df))
seq_map = df['sequential'].to_dict()

# Save df after assigning districts
df.to_pickle('./' + info + state + '_df_final.pkl')
#%%
############################################
###### EXPORT ##############################
############################################

# Load df after assigning districts
df = pd.read_pickle('./' + info + state + '_df_final.pkl')

# Name output text file and write headers. output_text_file is located at the
# top of the code
f = open(output_text_file, 'w')
f.write('precinctlistv01\n' + str(len(df)) + '\n' + \
        '\tnb\tsp\tunshared\tarea\tpop\tvoteA\tvoteB\tcongD\n')

# Helper function to convert geoID values into precinct index values
def convert_geoid(x):
    if str(x)[0]=='-':
        # identifies VTDs at edge of state
        return str(x)
    else:
        return str(seq_map[x])

# Iterate through each row in the dataframe to write outpt
for ix, row in df.iterrows():
 
    # Label precinct index (GEOID10)
    f.write(str(row['sequential']) + '\t')
    
    # Write list of neighbors
    f.write(convert_geoid(row['neighbors'][0]))
    if len(row['neighbors']) > 1:
        for i in row['neighbors'][1:]:
            f.write(',' + convert_geoid(i))
    f.write('\t')

    # Write list of shared perimeter
    row['shared_perims'] = ['%.8f' % elem for elem in row['shared_perims']]
    f.write(row['shared_perims'][0])
    if len(row['shared_perims']) > 1:
        for i in row['shared_perims'][1:]:
            f.write(',' + i)
    
    # Write remaining input
    f.write('\t0\t' + str(row['area']) + '\t' + str(round(row[pop_string])) + \
            '\t' + str(round(row[D_string])) + '\t' + \
            str(round(row[R_string])) + '\t' + row['CD'])
    f.write('\n')

f.close()
