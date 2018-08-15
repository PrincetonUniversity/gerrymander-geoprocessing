# -*- coding: utf-8 -*-
"""
Created on Thu Aug  9 15:03:45 2018

@author: Jacob

Helper methods related to image processing and geoprocessing to be used in 
PDF conversion tools.

"""
import pandas as pd
import pysal as ps
import geopandas as gpd
from PIL import Image
import os
import numpy as np
import math
import shapely as shp
from shapely.geometry import Polygon
from shapely.geometry import Point
from collections import Counter
import csv
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

def get_shared_perims(df):
    ''' Return a dataframe that assigns the length of shared perimeters with
    neighbors in a dataframes neighbor list.
    
    Arguments:
        df:'''
        
    # iterate over all precincts to set shared_perims
    for i,_ in df.iterrows():
        
        # iterate over the neighbors of precinct i
        for key in df.at[i, 'neighbors']:
        
            # obtain the boundary between current precinct and its j neighbor
            shape = df.at[i, 'geometry'].intersection(df.at[key, 'geometry'])
            
            # get shared_perim length (casework)
            if shape.type == 'GeometryCollection' or \
                    shape.type == 'MultiLineString':
                length = 0
                for line in shape.geoms:
                    if line.type == 'LineString':
                        length += line.length
            elif shape.type == 'LineString':
                length = shape.length
            else:
                print(shape.type)
                print(i)
                print(key)
                print ('Unexpected boundary')
                length = -1
                
            df.at[i, 'neighbors'][key] = length
    return df

def reduce_colors(img, num_colors):
    ''' Generates an image reducing the number of colors to a number 
    specified by the user. Uses Image.convert from PIL.
    
    Arguments:
        img: original image in PIL Image format
        num_colors: number of distinct colors in output file
        
    Output:
        Modified image with reduced number of distinct RGB values'''
    
    conv_img = img.convert('P', palette=Image.ADAPTIVE, colors = num_colors)
    return conv_img.convert('RGB')

def assign_blocks_to_regions(cb_df, reg_df):
    ''' Adds a 'region' column to dataframe of census blocks using areal
    interpolation with a dataframe with region names and geometries.
    
    Arguments:
        cb_df: dataframe with census blocks
        reg_df: dataframe with regions

    Output:
        Modified cb_df with 'region' column

    Note: this will overwrite the 'region' column in cb_df if it already
        exists.'''
        
    # construct spatial tree for precincts
    reg_df = gpd.GeoDataFrame(reg_df, geometry='geometry')
    pr_si = reg_df.sindex
    
    # instantiate empty 'region' column in cb_df
    cb_df['region'] = np.nan
    
    # iterate through every census block, i is the GEOID10 of the precinct
    for i, _ in cb_df.iterrows():

        # let census_block equal the geometry of the census_block. Note: later
        # census_block.bounds is the minimum bounding rectangle for the cb
        census_block = cb_df.at[i, 'geometry']
        
        # Find which MBRs for districts intersect with our cb MBR
        # MBR: Minimum Bounding Rectangle
        poss_pr = [reg_df.index[i] for i in \
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
                    area = reg_df.at[j, 'geometry'].intersection(\
                                     census_block).area / census_block.area
                    # Majority area means, we can assign district
                    if area > .5:
                        found_majority = True
                    frac_area[j] = area
            PR = max(frac_area.items(), key=operator.itemgetter(1))[0]
    
        # Assign census block region to PR
        cb_df.at[i, 'region'] = PR
        
    # return modified cb_df
    return cb_df

def split_non_contiguous():
    return 0

def merge_fully_contained(df, geo_id = 'geometry',
                          nbr_id='neighbors', cols_to_add=['area']):
    '''If any geometry is contained entirely within another geometry, this
    function merges it into the larger geometry.  Slightly distinct from the
    'donut and donut-hole' analogy because if multiple precincts are completely
    surrounded by a ring-shaped precinct, then they will all be consumed.
    
    Arguments:
        df: geodataframe to apply rook contiguity to
        geo_id = column name for geometries in dataframe
        nbr_id = column name for neighbor list (to be generated) in dataframe
        cols_to_add = which attributes (column names) should be added when 
            precincts are merged (i.e. area or population). For all other 
            columns, the data from the consuming precinct is preserved.
        
    Output:
        dataframe with neighbors list for each attribute in a new column
        called nbr_id (default name is 'neighbors')
    '''
    
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
                    if col in df.columns:
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

    
def pt_to_pixel_color(pt, img_arr, xmin, xlen, ymin, ylen, img_xmin, img_xlen, 
                img_ymin, img_ylen):
    '''Returns the pixel color corresponding to a given Shapely point, given 
    that the geometry and image have been aligned.  Uses the bounds of the
    geometry to map the point to the proper indices in the image array.  Thus,
    the image array must come from an image that has been cropped to fit on all
    four sides.
    
    Arguments:
        pt: Shapely point within reference geometry
        img_arr: numpy array generated by np.asarray(image)
        xmin: x coordinate (in geometry coordinate system) of leftmost point
            in georeferenced image
        xlen: maximum - minimum x coordinate in georeferenced image
        ymin: minimum y coordinate in georeferenced image
        ylen: maximum - minimum y coordinate in georeferenced image
        img_xmin: minimum x coordinate in img_arr (should probably be 0)
        img_xlen: maximum - minimum x coordinate in img_arr
        img_ymin: minimum y coordinate in img_arr
        img_ylen: maximum - minimum y coordinate in img_arr
        
    Output: pixel value (array)
        '''
    # coordinate transform calculation, where floor is used to prevent indices 
    # from going out of bounds (also this is proper practice for the accuracy 
    # of the transform)
    x = math.floor((pt.x - xmin) * img_xlen / xlen + img_xmin)
    y = math.floor((ymin-pt.y) * img_ylen / ylen + img_ylen - img_ymin)

    return img_arr[y][x]

def isBlack(color):
    ''' Returns True iff all 3 RGB values are less than 25.
    
    Arguments: 
        color: a list whose first 3 elements are RGB.'''
        
    return (color[0] < 25 and color[1] < 25 and color[2] < 25)

def random_pt_in_triangle(triangle):
    ''' This function outputs a uniformly random point inside a triangle
    (given as a Shapely polygon), according to the algorithm 
    described at http://mathworld.wolfram.com/TrianglePointPicking.html''
    
    Argument:
        triangle: Shapely polygon
        
    Output: Shapely Point drawn randomly from inside triangle'''
    
    # get list of vertices (cut off last element; first point is repeated)
    vertices = np.asarray(triangle.boundary.coords)[:3]
    
    # assuming that vertices[0] is at (0,0), get coordinates of other vertices
    v_1 = vertices[1] - vertices[0]
    v_2 = vertices[2] - vertices[0]
    
    # select random point in parallelogram created by vectors v_1 and v_2
    # r,s are random in [0, 1)
    r = np.random.random_sample()
    s = np.random.random_sample()
    pt = Point(vertices[0] + r * v_1 + s * v_2)
    
    # refelct pt to put it in the triangle if it is not inside
    if not triangle.contains(pt):
        pt = Point(vertices[0] + (1-r) * v_1 + (1-s) * v_2)
        
    # return the random point
    return pt


def most_common_color(poly, img_arr, xmin, xlen, ymin, ylen, sample_limit):
    ''' This function uses pixel sampling to calculate (with high probability)
    the most common RGB value in the section of an image corresponding to 
    a Shapely polygon within the reference geometry.
    
    Arguments:
        poly: Shapely polygon within reference geometry
        img_arr: numpy array generated by np.asarray(image)
        xmin: x coordinate (in geometry coordinate system) of leftmost point
            in georeferenced image
        xlen: maximum - minimum x coordinate in georeferenced image
        ymin: minimum y coordinate in georeferenced image
        ylen: maximum - minimum y coordinate in georeferenced image
        sample_limit: maximum number of pixels to sample before guessing
        
    Output:
        integer corresponding to 256^2 R + 256 G + B
    '''
    
    # triangulate polygon
    triangles = shp.ops.triangulate(poly)
    
    # in very rare cases, the polygon is so small that this shapely operation
    # fails to triangulate it, so we return 0 (black)
    if len(triangles) == 0:
        return 0
    
    # make list of partial sums of areas so we can pick a random triangle
    # weighted by area
    areas = np.asarray([0])
    for triangle in triangles:
        areas = np.append(areas, areas[-1] + triangle.area)
    
    # scale so last sum is 1
    areas = areas / areas[-1]

    # initialize data to monitor throughout the sampling process
    # colors is a dictionary to store the number of pixels of each color
    colors = {}
    count = 0
    color_to_return = None
    stop_sampling = False
    # sample as long as none of the stop criteria have been reached
    while not stop_sampling:
        
        # update count
        count += 1
        
        # select a random triangle (weighted by area) in the triangulation
        r = np.random.random_sample()
        triangle = triangles[np.searchsorted(areas,r)-1]
        
        # select a point uniformly at random from this triangle
        pt = random_pt_in_triangle(triangle)
        
        # gets size of img_arr to align it with poly
        img_xlen = len(img_arr[0])
        img_ylen = len(img_arr)
        
        # get color of pixel that corresponds to pt
        color = pt_to_pixel_color(pt, img_arr, xmin, xlen, ymin, ylen, \
                0, img_xlen, 0, img_ylen)
        

        # in case all are black, return black
        colors[0] = 1
        
        # if not black, add color to dictionary
        if not isBlack(color):    
            
            # for hashing
            color_int = 256*256*color[0] + 256*color[1]+color[2]
            
            # update dictionary
            if color_int not in colors:
                colors[color_int] = 0
            colors[color_int] += 1
        
        # decide if we are done sampling (every 10 samples)
        if (count % 10 == 0):
            
            # find the most common color and its frequency
            common = max(colors.items(), key=operator.itemgetter(1))[0]
            common_count = colors[common]
            
            # calculate z-score based on proportion test
            # trying to get evidence that this color is over 50% frequent
            # among all pixels
            z_score = (2 * common_count / count - 1) * np.sqrt(count)
            
            # stop sampling if we have convincing evidence or we hit our limit
            if (z_score > 4 or count >= sample_limit):
                color_to_return = common
                stop_sampling = True
    
    return color_to_return
    
def merge_to_right_number(df, num_regions):
    ''' Decreases the number of attributes in a dataframe to a fixed number by
    merging the smallest geometries into the neighbor with which it shares the
    longest border.
    '''
    # only do this if the current number of regions exceeds num_regions
    if (len(df) > num_regions):
        
        # reset index for df
        df = df.reset_index(drop=True)
    
        # Get rook contiguity through a dictionary and calculate the shared_perims
        df = real_rook_contiguity(df, struct_type='dict')
        print('did rook')
        df = get_shared_perims(df)
        print('did shared perims')
    
        # get list of precinct indices to keep
        df['area'] = 0
        for i, _ in df.iterrows():
            df.at[i, 'area'] = df.at[i, 'geometry'].area
        arr = np.array(df['area'])
        
        precincts_to_merge = arr.argsort()[ : -num_regions]
        
        # Iterate through indexes of precincts_to_merge
        for i in precincts_to_merge:
    
            # update neighbors and shared_perims
            cur_prec = df.at[i, 'neighbors']
            ix = max(cur_prec, key=cur_prec.get)
            merge_prec = df.at[ix, 'neighbors']
    
            # merge dictionaries (summing shared perims as needed)
            merge_prec = Counter(merge_prec) + Counter(cur_prec)
    
            # remove key to itself
            merge_prec.pop(ix)
    
            # set neighbor dictionary in dataframe
            df.at[ix, 'neighbors'] = merge_prec
            
            # merge geometry
            df.at[ix, 'geometry'] = df.at[ix, 'geometry'].union \
                (df.at[i, 'geometry'])
            
            # delete neighbor reference to i and add reference for merge to key
            for key in list(cur_prec):
                df.at[key, 'neighbors'].pop(i)
                
                ##-----------------------------------------------------------------
                # get perimeter length for key in merge and set in 
                # neighbor list
                key_dist = df.at[ix, 'neighbors'][key]
                df.at[key, 'neighbors'][ix] = key_dist
            
        # delete all merged precincts
        df = df.drop(precincts_to_merge)
            
        # reset index for df
        df = df.reset_index(drop=True)
            
        # set region values
        for i in range(len(df)):
            df.at[i, 'region'] = i
        
    return df
    