# -*- coding: utf-8 -*-
"""
Created on Thu Aug  9 15:03:45 2018

@author: Jacob
"""
import time
import pandas as pd
import pysal as ps
import geopandas as gpd
from PIL import Image
import os
import numpy as np
import math
import shapely as shp
from shapely.geometry import Polygon
from collections import Counter
import csv
import pickle
import operator

def real_rook_contiguity(df, geo_id = 'geometry',
                         nbr_id='neighbors',struct_type='list'):
    ''' Generates neighbor list using rook contiguity for a geodataframe.
    
    Arguments:
        df: geodataframe to apply rook contiguity to
        geo_id = column name for geometries in dataframe
        nbr_id = column name for neighbor list (to be generated) in dataframe
        struct_type: determines whether neighbors are returned as a list or
        as a dict
        
    Output:
        dataframe with neighbors list for each attribute in a new column
        called nbr_id (default name is 'neighbors')
    '''
    
    # Obtain queen continuity for each shape in the dataframe. We will remove 
    # all point contiguity. Shapely rook contiguity sometimes assumes lines
    # with small lines are points
    w = ps.weights.Queen.from_dataframe(df, geom_col=geo_id)
    
    # Initialize neighbors column
    df[nbr_id] = pd.Series(dtype=object)   
    
    # Initialize neighbors for each precinct
    for i,_ in df.iterrows():
        struct = w.neighbors[i]
        
        # Iterate through every precinct to remove all neighbors that only 
        # share a single point. Rook contiguity would asssume some lines are 
        # points, so we have to use queen and then remove points
        
        # Obtain degree (# neighbors) of precinct
        nb_len = len(struct)
        
        # Iterate through neighbor indexes in reverse order to prevent errors 
        # due to the deletion of elements
        for j in range(nb_len - 1, -1, -1):
            # get the jth neighbor
            j_nb = struct[j]
            
            # get the geometry for both precincts
            i_geom = df.at[i, geo_id]
            j_nb_geom = df.at[j_nb, geo_id]
            
            # If their intersection is a point, delete j_nb from i's neighbor 
            # list do not delete in both directions. That will be taken care of
            # eventually when i = j_nb later in the loop or before this occurs
            geom_type = i_geom.intersection(j_nb_geom).type
            if geom_type == 'Point' or geom_type == 'MultiPoint':
                del struct[j]
        
        # Assign to dataframe according to the structure passed in
        if struct_type == 'list':
            df.at[i, nbr_id] = struct
        elif struct_type == 'dict':
            df.at[i, nbr_id] = dict.fromkeys(struct)
    return df

def merge_fully_contained(df, geo_id = 'geometry',
                          nbr_id='neighbors', cols_to_add=['area']):
    
    # Create list of rows to drop at the end of the multiple contained check
    ids_to_drop = []
    
    # Iterate over all attributes
    for i,_ in df.iterrows():
        
        # Create polygon Poly from its exterior coordinates. This
        # polygon will be filled without an interior. The purpose of filling
        # the interior is to allow for an intersection to see if a neighbor is
        # fully contained
        geometry = df.at[i, geo_id]
        poly_coords = list(geometry.exterior.coords)
        poly = Polygon(poly_coords)
        
        # Assuming no overlaps in the geometries, if poly contains the 
        # geometry then no neighbors can be contained in the geometry.
        # So we can go quickly through the loop in most cases.
        if geometry.contains(poly):
            continue
        
        # Create list of contained neighbor id's to delete
        nb_ix_del = []
    
        # Define a list of "possibly contained" precincts. If a precinct
        # is nested witin other contained precincts, we will need to add it to
        # this list
        possibly_contained = df.at[i, nbr_id]
        for j in possibly_contained:        
            
            # Check if the intersection of Poly (precint i's full polygon) and the
            # current neighbor is equal to the current neighbor. This demonstrates
            # that the current neighbor is fully contained within precinct i
            j_geom = df.at[j, geo_id]
            
            if j_geom == j_geom.intersection(poly):
                # j is fully contained within i. To account for nested precincts
                # we append any neighbor of j that is not already in possibly_
                # contained not including i
                for j_nb in df.at[j, nbr_id]:
                    if j_nb not in possibly_contained and j_nb != i:
                        possibly_contained.append(j_nb)
    
                # Add capture columns from neighbor to precinct i
                for col in cols_to_add:
                    df.at[i, col] = df.at[i, col] + df.at[j, col]
                            
                # add neighbor reference from precinct i to delete if a neighbor
                if j in df.at[i, nbr_id]:
                    nb_ix = df.at[i, nbr_id].index(j)
                    nb_ix_del.append(nb_ix)
                
                # add neighbor precinct to the ID's to be dropped
                ids_to_drop.append(j)
                
        # Delete neighbor references from precinct i
        if len(nb_ix_del) > 0:
            # iterate through indexes in reverse to prevent errors through deletion
            for nb_ix in reversed(nb_ix_del):
                del(df.at[i, nbr_id][nb_ix])
    
    # Drop contained precincts from the dataframe and return
    df = df.drop(ids_to_drop)
    return df