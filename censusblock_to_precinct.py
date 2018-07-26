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
import os
import shutil

#%%

##############################################################################
###### PRELIMINARIES AND LOAD SHAPES #########################################
##############################################################################
census_shape_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/XML/York Test County/York County_census_block.shp"

out_folder = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/XML/York Test County"

out_name = 'York Without Projection precinct'

# Delete CPG file
cpg_path = ''.join(census_shape_path.split('.')[:-1]) + '.cpg'
if os.path.exists(cpg_path):
    os.remove(cpg_path)

# Define projection path and check if it exists
prj_exists = False
prj_path = ''.join(census_shape_path.split('.')[:-1]) + '.prj'
if os.path.exists(prj_path):
    prj_exists = True

df = gpd.read_file(census_shape_path)

#%%
##############################################################################
###### QUEEN CONTIGUITY FOR CENSUS ###########################################
##############################################################################

# Obtain queen continuity for each shape in the dataframe. We will remove all
# point contiguity. Shapely rook contiguity sometimes assumes lines with small
# lines are points
w = ps.weights.Queen.from_dataframe(df, geom_col='geometry')

# Initialize neighbors column
df['neighbors'] = pd.Series(dtype=object)

# Initialize neighbors for each precinct
for i,_ in df.iterrows():
    df.at[i, 'neighbors'] = w.neighbors[i]
    
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
#%%
##############################################################################
###### SETTING PRECINCT IDs ##################################################
##############################################################################

# Initialize List to all elements with an ID
prec_set_list = list(df[df['ID'] != None].index)

# Iterate until every census block has an ID
while len(prec_set_list) > 0:
    
    # Initialize new prec_set_list to be empty
    prec_set_list_new = []
    
    # Loop through the current prec_set_list of assigned census blocks
    for i in prec_set_list:
        # Iterate through the neighbors of the current census block
        nb_idnone = [j for j in  df.at[i, 'neighbors'] if df.at[j, 'ID'] \
                     == None]
        
        #  Get ID of census block i and set unassigned neighbors to this value
        i_id = df.at[i, 'ID']
        for k in nb_idnone:
            df.at[k, 'ID'] = i_id
    
        # Add these elements to the new queue
        prec_set_list_new += nb_idnone
        
    # set new prec_set_list
    prec_set_list = prec_set_list_new

#%%
##############################################################################
###### CREATE PRECINCTS USING ID #############################################
##############################################################################

# Get unique values in the df ID column
prec_id = list(df.ID.unique())

df_prec = pd.DataFrame(columns=['ID', 'geometry'])

# Iterate through all of the precinct IDs and set geometry of df_prec to union
for i in range(len(prec_id)):
    df_poly = df[df['ID'] == prec_id[i]]
    polys = list(df_poly['geometry'])
    df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
    df_prec.at[i, 'ID'] = prec_id[i]
    
#%%
##############################################################################
###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)##########################
##############################################################################

# Initialize indexes to drop
drop_ix = []

# Iterate through every precinct
for i, _ in df_prec.iterrows():
    # Check if it precinct is a MultiPolygon
    if df_prec.at[i, 'geometry'].type == 'MultiPolygon':
        # Add index as the index of a row to be dropped
        drop_ix.append(i)
        
        # get shape and area of current precinct
        precinct = df_prec.at[i, 'geometry']
        # Area is only needed for capture cols which are not currently used
        area = precinct.area

        # Iterate through every contiguous region in the precinct
        for region in precinct.geoms:
            # Set geometry and id of new_shape
            d = {}
            d['ID'] = df_prec.at[i, 'ID']
            d['geometry'] = region
            
            # Not currently necessary but might be later to have capture cols
# =============================================================================
#             # Adjust relevant fields by proportion of area
#             proportion = region.area/area
#             
#             # Set column values proportional to the regions area
#             for col in capture_cols:
#                 d[col] = proportion * df_prec.at[archipelago, col]
# =============================================================================
            df_prec = df_prec.append(d, ignore_index=True)
            
# Remove original noncontiguous precincts
df_prec = df_prec.drop(drop_ix)

#%%
##############################################################################
###### QUEEN CONTIGUITY FOR PRECINCTS ########################################
##############################################################################

# Obtain queen continuity for each shape in the dataframe. We will remove all
# point contiguity. Shapely rook contiguity sometimes assumes lines with small
# lines are points
w = ps.weights.Queen.from_dataframe(df_prec, geom_col='geometry')

# Initialize neighbors column
df_prec['neighbors'] = pd.Series(dtype=object)

# Initialize neighbors for each precinct
for i,_ in df_prec.iterrows():
    df_prec.at[i, 'neighbors'] = w.neighbors[i]
    
# Iterate through every precinct to remove all neighbors that only share a 
# single point. Rook contiguity would asssume some lines are points, so we
# have to use queen and then remove points
for i,_ in df_prec.iterrows():
    
    # Obtain degree (# neighbors) of precinct
    nb_len = len(df_prec.at[i, 'neighbors'])
    
    # Iterate through neighbor indexes in reverse order to prevent errors due
    # to the deletion of elements
    for j in range(nb_len - 1, -1, -1):
        # get the jth neighbor
        j_nb = df_prec.at[i, 'neighbors'][j]
        
        # get the geometry for both precincts
        i_geom = df_prec.at[i, 'geometry']
        j_nb_geom = df_prec.at[j_nb, 'geometry']
        
        # If their intersection is a point, delete j_nb from i's neighbor list
        # do not delete in both directions. That will be taken care of
        # eventually when i = j_nb later in the loop or before this occurs
        if i_geom.intersection(j_nb_geom).type == 'Point':
            del df_prec.at[i, 'neighbors'][j]
            
#%%
##############################################################################
###### MERGE PRECINCTS FULLY CONTAINED IN OTHER PRECINCTS ####################
##############################################################################

# Donut Hole Precinct Check
# Get IDs of donut holes with only one neighbor
donut_holes = df_prec[df_prec['neighbors'].apply(len)==1].index
    
# Loop until no more donuts exist. Must loop due to concentric precincts
while len(donut_holes) != 0:
    # Iterate over each donut hole precinct
    for donut_hole in donut_holes:
        # find each donut's surrounding precinct
        donut = df_prec.at[donut_hole, 'neighbors'][0]
        
        # Combine geometries for donut holde
        polys = [df_prec.at[donut, 'geometry'], 
                 df_prec.at[donut_hole, 'geometry']]
        df_prec.at[donut, 'geometry'] = shp.ops.cascaded_union(polys)
        # Capture columns not currently in use
# =============================================================================
#         # Combine donut hole precinct and surrounding precinct capture columns
#         for col in capture_cols:
#             df_prec.at[donut, col] = df_prec.at[donut, col] + \
#                                         df_prec.at[donut_hole, col]
# =============================================================================
        # remove neighbor reference to donut hole precinct and delete
        donut_hole_index = df_prec.at[donut, 'neighbors'].index(donut_hole)
        del(df_prec.at[donut, 'neighbors'][donut_hole_index])
    
    # Drop the rows in the dataframe for the donut holes that existed
    df_prec = df_prec.drop(donut_holes)
    
    # get IDs of new donut holes created
    donut_holes = df_prec[df_prec['neighbors'].apply(len)==1].index

# Multiple Contained Precincts Check
# Create list of rows to drop at the end of the multiple contained check
ids_to_drop = []

# Iterate over all precincts except the state boundary precinct
for i,_ in df_prec.iterrows():
    
    # Create polygon Poly for this precinct from its exterior coordinates. This
    # polygon will be filled without an interior. The purpose of filling
    # the interior is to allow for an intersection to see if a neighbor is
    # fully contained
    poly_coords = list(df_prec.at[i, 'geometry'].exterior.coords)
    poly = Polygon(poly_coords)
    
    # Create list of contained neighbor id's to delete
    nb_ix_del = []

    # Define a list that contains possibly contained precincts. If a precint
    # is nested witin other contained precincts, we will need to add it to
    # this list
    possibly_contained = df_prec.at[i, 'neighbors']
    for j in possibly_contained:        
        
        # Check if the intersection of Poly (precint i's full polygon) and the
        # current neighbor is equal to the current neighbor. This demonstrates
        # that the current neighbor is fully contained within precinct i
        j_geom = df_prec.at[j, 'geometry']
        
        if j_geom == j_geom.intersection(poly):
            # j is fully contained within i. To account for nested precincts
            # we append any neighbor of j that is not already in possibly_
            # contained not including i
            for j_nb in df_prec.at[j, 'neighbors']:
                if j_nb not in possibly_contained and j_nb != i:
                    possibly_contained.append(j_nb)

            # Add geometry of j to geometry of i
            polys = [df_prec.at[i, 'geometry'], 
                     df_prec.at[j, 'geometry']]
            df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        
# =============================================================================
#             # Add capture columns from neighbor to precinct i
#             for col in capture_cols:
#                 df_prec.at[i, col] = df_prec.at[i, col] + df_prec.at[j, col]
# =============================================================================
                        
            # add neighbor reference from precinct i to delete if a neighbor
            if j in df_prec.at[i, 'neighbors']:
                nb_ix = df_prec.at[i, 'neighbors'].index(j)
                nb_ix_del.append(nb_ix)
            
            # add neighbor precinct to the ID's to be dropped
            ids_to_drop.append(j)
            
    # Delete neighbor references from precinct i
    if len(nb_ix_del) > 0:
        # iterate through indexes in reverse to prevent errors through deletion
        for nb_ix in reversed(nb_ix_del):
            del(df_prec.at[i, 'neighbors'][nb_ix])

# Drop contained precincts from the dataframe
df_prec = df_prec.drop(ids_to_drop)

#%%
##############################################################################
###### Save as Shapefile #####################################################
##############################################################################

df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')
df_prec = df_prec.drop(columns=['neighbors'])
df_prec.to_file(out_folder + '/' + out_name + '.shp')

# Copy PRJ file if it exists
if prj_exists:
    shutil.copy(prj_path, out_folder + '/' + out_name + '.shp')











