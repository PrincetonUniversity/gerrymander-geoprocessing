"""
Helper methods to make changes to shapefiles
"""

import geopandas as gpd
import pandas as pd
import shapely as shp
from shapely.geometry import Polygon
from collections import Counter
import numpy as np

# import helper tools as if running from parent directory
import helper_tools.file_management as fm
import helper_tools.shp_calculations as sc


def dissolve(df, dissolve_attribute):   
    ''' Dissolves boundaries according to the dissolve_attribute (diss_att)

    Arguments:
        in_path: geodataframe of shapefile to dissolve
        dissolve_attribute: attribute to dissolve boundaries according to

    Output:
        Shapefile with the boundaries dissolved

    Additional:
        Main use is to generate a precinct level shapefile from census block
        data
    '''
    # Get unique values of dissolved attribute
    dissolve_names = list(df[dissolve_attribute].unique())
    
    # Create dataframe for dissolved shapefile
    df_dissolve = pd.DataFrame(columns=[dissolve_attribute, 'geometry'])

    # Iterate through each unique element in the dissolve_attribute column
    for i, elem in enumerate(dissolve_names):
        # Use cascaded union to combine all smaller geometries with the same
        # dissolve attribute
        df_poly = df[df[dissolve_attribute] == elem]
        polys = list(df_poly['geometry'])
        geometry = shp.ops.cascaded_union(polys)

        # Add the union to the new dataframe
        df_dissolve.at[i, 'geometry'] = geometry
        df_dissolve.at[i, dissolve_attribute] = elem

    return gpd.GeoDataFrame(df_dissolve, geometry='geometry')

def generate_bounding_frame(df):
    ''' Generates a bounding frame arouund the extents of a shapefile
    
    Arguments:
        df: geodataframe of shapefile to create bounding frame around
        
    Output:
        Geometry of bounding frame (also saves shapefile)
        frame_df: geodataframe to the bounding frame (only one geometry)
    '''
    # Calculate boundaries of the geodataframe using union of geometries
    # takes form (min_x, min_y, max_x, max_y)
    bounds = shp.ops.cascaded_union(list(df['geometry'])).bounds
    xmin = bounds[0]
    xmax = bounds[2]
    xlen = xmax-xmin
    ymin = bounds[1]
    ymax = bounds[3]
    ylen = ymax-ymin
    
    # Generate frame geometry. The multiplier of 10 is arbitrary. We just need
    # it to be large enough that when exporting in GIS over an image it is the
    # only color on the border of the image it is overlaid on top of
    in_frame = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
    out_frame = Polygon([(xmin-10*xlen, ymin-10*ylen),\
                         (xmax+10*xlen, ymin-10*ylen),\
                         (xmax+10*xlen, ymax+10*ylen),\
                         (xmin-10*xlen, ymax+10*ylen)])
    frame = out_frame.symmetric_difference(in_frame)

    # Convert frame polygon into GeoDataFrame
    frame_df = gpd.GeoDataFrame()
    frame_df['geometry'] = [frame]
    return frame_df

def merge_fully_contained(df, geo_name='geometry', nbr_name='neighbors',
                          cols_to_add=[]):
    '''Merge geometries contained entirely by another geometry

    Arguments:
        df: DataFrame
        geo_name: column name for geometries in DataFrame
        nbr_name: column name for neighbors in DataFrame
        cols_to_add: attributes that should be combined when geometries are
            merged

    Output:
        DataFrame after merges
    '''

    # create neighbor list if it does not exist
    if nbr_name not in df.columns:
        df = sc.real_rook_contiguity(df)

    # Initialize list of rows to drop at the end
    ix_to_drop = []

    # iterate over all geometries
    for ix, row in df.iterrows():

        # Create polygon from its exterior coordinates
        poly = Polygon(list(row[geo_name].exterior.coords))

        # if the exterior created polygon is a subset of the actual poly
        # then no other geometry can be contained within the current geometry
        if row[geo_name].contains(poly):
            continue

        # initialize list of contained neighbor ids
        nb_ix_del = []

        # iterate through the lsit of neighors
        possibly_contained = row[nbr_name]
        for nbr in possibly_contained:

            nbr_poly = df.at[nbr, geo_name]

            # check if the intersection of current geometry and its neighbor
            # is equal to the neighbor. This demonstrates neighbor is contained
            if nbr_poly == nbr_poly.intersection(poly):

                # To account for nested, we say neighbors of contained 
                # neighbors are possibly contained
                for nbr_nbr in df.at[nbr, nbr_name]:
                    if nbr_nbr not in possibly_contained and nbr_nbr != ix:
                        possibly_contained.append(nbr_nbr)

                # Add geometry of nbr to geometry of ix
                polys = [row[geo_name], df.at[nbr, geo_name]]
                df.at[ix, geo_name] = shp.ops.cascaded_union(polys)

                # Add inputted columns
                for col in cols_to_add:
                    if col in df.columns:
                        df.at[ix, col] = row[col] + df.at[nbr, col]

                # add neighbor to list to drop
                ix_to_drop.append(nbr)

        # delete neighbor references from the current precinct. Iterate in
        for nb_ix in reversed(nb_ix_del):
            del(df.at[ix, nbr_name][nb_ix])

    # Drop contained geometries from the dataframe and return
    return df.drop(ix_to_drop).reset_index(drop=True)

def split_noncontiguous(df, retain_cols=[]):
    '''Split noncontiguous geometries such that each contiguous section becomes
    its own geometry. We create a new geometry for each "piece" and drop the
    original geometry.

    Arguments:
        df: df
        retain_cols: attributes to retain the values of after the split

    Output:
        dataframe without the noncontiguous geometries
    '''

    # Initialize list that will contain indexes to drop
    drop_ix = []

    # Search for MultiPolygon
    for ix, row in df.iterrows():
        if row['geometry'].type == 'MultiPolygon':

            # Add as an index to be dropped and initilaize geometry
            drop_ix.append(ix)
            multi_poly = row['geometry']

            # Iterate through each section and generate a new geoemtry
            for region in multi_poly.geoms:
                d = {}
                d['geometry'] = region

                # Keep desired attributes
                for col in retain_cols:
                    d[col] = df.at[ix, col]

                # Append new geometry to dataframe
                df = df.append(d, ignore_index=True)

    # Remove original geometries
    df = df.drop(drop_ix)
    df = df.reset_index(drop=True)

    return df

def merge_geometries(df, ixs_to_merge, cols_to_add=[]):
    '''Combine geoemtries using greedy method of greatest shared perimenter.
    Adds in the order of greatest fraction of perimeter assigned. 

    Example: if geometry A has 50 percent of its perimeter assigned and 
    geometry B has 40 percent of its perimeter assigned, then geometry A will
    be assigned before geometry B

    Example: If geometry A needs to be merged, and geometry Ashareds 70 percent 
    of its perimeter with geometry B and 30 percent of its perimeter with
    geometry C, geometry A will be merged with geometry B

    We are taking the original geometry and combining it with the merge
    neighbor geometry.

    Arguments:
        df: DataFrame
        ixs_to_merge: indices of geometries in the dataframe to merge with
            other geomerties
        cols_to_add: attributes that should be combined when precincts are
            merged

    Output:
        geodataframe with merged geometries
    '''
    # Only keep attributes in cols_to_add that are in the dataframe
    cols_to_add = list(set(cols_to_add).intersection(set(df.columns)))

    # set appropriate columns to floats
    for col in cols_to_add:
        df[col] = df[col].astype(float)

    # obtain the neighbors dictionary with shared perimeters
    df = sc.calculate_shared_perimeters(df)

    # Ensure that there are no duplicated indices to merge
    ixs_to_merge = list(set(ixs_to_merge))

    # Set copy of indices to merge list in order to delete at end
    del_ixs =  ixs_to_merge.copy()

    # Keep merging geometries until the indices_to_merge list is empty
    while len(ixs_to_merge) > 0:

        # find how much of each perimeter of each geometry isa ssigned for 
        # each of the indices that we need to merge
        fractions = [sc.fraction_shared_perim(df.at[i, 'neighbors'],
            ixs_to_merge, df.at[i, 'geometry'].length) for i in ixs_to_merge]

        # Find the index to the geometry that has the smallest fraction of its
        # perimeter assigned
        orig_ix = ixs_to_merge[fractions.index(min(fractions))]

        # Determine the neighbor to merge with
        orig_nbrs = df.at[orig_ix, 'neighbors']
        merge_nbr_ix = max(orig_nbrs, key=orig_nbrs.get)

        # Find the neighbors of the merge neighbor
        nbrs_of_merge_nbr = df.at[merge_nbr_ix, 'neighbors']

        # Add the geometry of the original to the merge_nbr
        orig_poly = df.at[orig_ix, 'geometry']
        merge_nbr_poly = df.at[merge_nbr_ix, 'geometry']
        df.at[merge_nbr_ix, 'geometry'] = merge_nbr_poly.union(orig_poly)

        # Add the appropriate columns
        for col in cols_to_add:
            df.at[merge_nbr_ix, col] += df.at[orig_ix, col]

        # Fix the shared perimeters dictionary

        # Combine the shared perimeters dictionary of the original and merge
        # neighbor geometries. Transform back to regular dictionary
        nbrs_of_merge_nbr = Counter(nbrs_of_merge_nbr) + Counter(orig_nbrs)
        nbrs_of_merge_nbr = dict(nbrs_of_merge_nbr)

        # Remove references to the boundary that previously existed between
        # the original geometry and the merge_nbr geometry
        nbrs_of_merge_nbr.pop(merge_nbr_ix)
        nbrs_of_merge_nbr.pop(orig_ix)

        # Fix shared perimeter values for each of the neighbors



        # iterate through each of the orig neighbors that isn't the merge_nbr
        orig_nbrs.pop(merge_nbr_ix)
        for non_merge_nbr_ix in orig_nbrs:

            # get current neighbors dictioanry of the non_merge_nbr
            nbrs_of_non_merge_nbr = df.at[non_merge_nbr_ix, 'neighbors']

            # Get distance of periemter between the original geometry and its
            # non-mergining neighbor
            orig_dist = orig_nbrs[non_merge_nbr_ix]

            # Case 1: non_merge_nbr and merge_nbr were already neighbors
            if merge_nbr_ix in nbrs_of_non_merge_nbr:

                # Fix shared perimeter value of merge_nbr
                nbrs_of_non_merge_nbr[merge_nbr_ix] += orig_dist
                nbrs_of_non_merge_nbr.pop(orig_ix)

            # Case 2: non_merge_nbr and merge_nbr were NOT already neighbors
            else:

                # Fix shared perimeter value of merge_nbr
                nbrs_of_non_merge_nbr[merge_nbr_ix] = orig_dist
                nbrs_of_non_merge_nbr.pop(orig_ix)

            # Set value for non merging neighbor
            df.at[non_merge_nbr_ix, 'neighbors'] = nbrs_of_non_merge_nbr

        # Update perimeters values for merge neighbor
        df.at[merge_nbr_ix, 'neighbors'] = nbrs_of_merge_nbr

        # remove ix of original geometry from list of indices to remove
        ixs_to_merge.remove(orig_ix)

    # delete all geometries that were merged
    df = df.drop(del_ixs)

    return df

def merge_to_right_number(df, num_geometries, cols_to_add=[]):
    '''Reduce a shapefile to only have num_geometries geometries. Merges the
    smallest geometries into the neighbor with which it shares the largest
    perimeter. Uses the merge_geometries function.

    Arguments:
        df: dataframe
        num_geometries: number of geometries remaining after function completes
        cols_to_add: cols to add together
    '''

    # reset indexes for the dataframe
    df = df.reset_index(drop=True)

    # Find the smallest area geometries
    for i, row in df.iterrows():
        df.at[i, 'area'] = df.at[i, 'geometry'].area
    arr = np.array(df['area'])
    ixs_to_merge = arr.argsort()[:-num_geometries]

    # Drop area column
    df = df.drop(columns=['area'])

    # Merge geometries
    df = merge_geometries(df, ixs_to_merge)

    return df