"""
Helper methods to calculate properties within shapefiles
"""

import shapely as shp
from shapely.geometry import Polygon
from shapely.geometry import Point
import numpy as np
import pysal as ps
import pandas as pd
import math
import helper_tools.file_management as fm


def pt_to_pixel_color(pt, img_arr, xmin, xlen, ymin, ylen, img_xmin, img_xlen,
                      img_ymin, img_ylen):
    '''Returns the pixel color corresponding to a given Shapely point, given
    that the geometry and image have been aligned.  Uses the bounds of the
    geometry to map the point to the proper indices in the image array.  Thus,
    the image array must come from an image that has been cropped to fit on all
    four sides.

    Arguments:
        pt:
            Shapely point within reference geometry

        img_arr:
            numpy array generated by np.asarray(image)

        xmin:
            x coordinate (in geometry coordinate system) of leftmost point
            in georeferenced image

        xlen:
            maximum - minimum x coordinate in georeferenced image

        ymin:
            minimum y coordinate in georeferenced image

        ylen:
            maximum - minimum y coordinate in georeferenced image

        img_xmin:
            minimum x coordinate in img_arr (should probably be 0)

        img_xlen:
            maximum - minimum x coordinate in img_arr

        img_ymin:
            minimum y coordinate in img_arr

        img_ylen:
            maximum - minimum y coordinate in img_arr

    Output:
        pixel value (array)
    '''
    # coordinate transform calculation, where floor is used to prevent indices
    # from going out of bounds (also this is proper practice for the accuracy
    # of the transform)
    x = math.floor((pt.x - xmin) * img_xlen / xlen + img_xmin)
    y = math.floor((ymin-pt.y) * img_ylen / ylen + img_ylen - img_ymin)

    return img_arr[y][x]


def random_pt_in_triangle(triangle):
    ''' This function outputs a uniformly random point inside a triangle
    (given as a Shapely polygon), according to the algorithm
    described at http://mathworld.wolfram.com/TrianglePointPicking.html''

    Argument:
        triangle:
            Shapely polygon

    Output:
        Shapely Point drawn randomly from inside triangle'''

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


def fraction_shared_perim(nbrs, indices, perim):
    ''' Helper function for merge_geometries to calculate the fraction
    of a shape's perimeter that is shared with shapes at certain indices.
    Relies on having a dictionary of neighbors and shared perimeters.

    Arguments:
        nbrs:
            dictionary with keys as neighbor indices, values as shared perims

        indices:
            indices for which we care about the fraction shared

        perim:
            size of the perimeter of shape

    Output:
        fraction of perimter assigned
    '''
    # calcluate total perimeter shared with shapes at indices
    shared_perim = sum([nbrs[key] for key in nbrs if key in indices])

    return shared_perim / perim


def check_contiguity_and_contained(df, id_attribute):
    ''' Identify which geometries in a shapefile are noncontiguous and which
    geometries contain another geometries. Just prints when an error is found.

    Arguments:
        df:
            geodatafram of shapefile to check

        id_attribute:
            attribute used to identify geometries during check

    Output:
        Lists of two lists. First list, which geometries are noncontiguous.
        Second list: which geometries contain another.
        Will use print statements to display noncontiguous geometries
    '''

    # initialize dictionary that will refer to errors
    contains = []
    noncontig = []
    # Check that identification attribute is actually an attribute
    if id_attribute not in df.columns:
        print('Identification attribute is not an attribute of the shapefile.')
        print('Contiguity check aborted')
        return

    # Iterate through each of the geometries
    for i, row in df.iterrows():
        # Define the geometry
        geo = row['geometry']

        # Check if geometry contains another geometry
        if geo.type == 'Polygon':
            # Create a polygon from its exterior coordinates. If this is
            # contained by the geometry then we now that the geometry encircles
            # another

            # Create a polygon from the exterior coordinates. If there is no
            # "hole" in the geometry, then the generated polygon will be
            # contained by the geometry
            poly = Polygon(list(geo.exterior.coords))
            if not geo.contains(poly):
                contains.append(row[id_attribute])
                print('Contains Another: ' + row[id_attribute])

        # Check if geometry is noncontiguous
        else:
            print('\nNoncontiguous: ' + row[id_attribute])
            print('Num Non-Contiguous Pieces to Fix: ' +
                  str(len(geo.geoms) - 1))
            noncontig.append(row[id_attribute])

            # Check if any of the MultiPolygons contain another geometry

            for sub_polygon in geo.geoms:
                # Create a polygon from the exterior coordinates. If there is
                # no "hole" in the geometry, then the generated polygon will be
                # contained by the geometry
                poly = Polygon(list(sub_polygon.exterior.coords))
                if not sub_polygon.contains(poly):
                    contains.append(row[id_attribute])
                    print('Contains Another: ' + row[id_attribute])

    return [noncontig, contains]


def real_rook_contiguity(df, geo_id='geometry', nbr_id='neighbors',
                         struct_type='list'):
    ''' Generates neighbor list using rook contiguity for a geodataframe. Pysal
    rook contiguity sometimes fails for small borders

    Arguments:
        df:
            geodataframe to apply rook contiguity to

        geo_id:
            column name for geometries in dataframe

        nbr_id:
            column name for neighbor list (to be generated) in dataframe

        struct_type:
            determines whether neighbors are returned as a list or
            as a dict

    Output:
        dataframe with neighbors list for each attribute in a new column
        called nbr_id (default name is 'neighbors')
    '''
    # Reset index
    df = df.reset_index(drop=True)
    
    # Obtain queen continuity for each shape in the dataframe. We will remove
    # all point contiguity. Pysal rook contiguity sometimes assumes lines
    # with small lines are points
    w = ps.lib.weights.contiguity.Queen.from_dataframe(df, geom_col=geo_id)

    # Initialize neighbors column
    df[nbr_id] = pd.Series(dtype=object)

    # Initialize neighbors for each precinct
    for i, _ in df.iterrows():
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


def calculate_shared_perimeters(df):
    ''' Add a neighbor dictionary for each geometry as well as the length of
    the shared perimeter with each neighbor. In the dictionary, the keys are
    indices of rook-contiguous neighbors

    Argument:
        df:
            geodataframe

    Output:
        df with neighbors and shared perimeters added
    '''

    # get neighbors with dictionary
    df = real_rook_contiguity(df, struct_type='dict')

    # iterate over each geometry and its neighborsto set shared perimeters
    for ix, row in df.iterrows():
        for key in row['neighbors']:

            # obtain boundary between geometry and its neighbor
            s = row['geometry'].intersection(df.at[key, 'geometry'])

            # intersection is noncontiguous
            if s.type == 'GeometryCollection' or s.type == 'MultiLineString':
                row['neighbors'][key] = 0

                # add length of LineString
                for line in s.geoms:
                    if line.type == 'LineString':
                        row['neighbors'][key] += line.length

            # intersection is a single line
            elif s.type == 'LineString':
                row['neighbors'][key] = s.length

            # if shape or point print issues and set length to -1
            else:
                print(s.type)
                print(ix)
                print(key)
                print('Unexpected Boundary')
                row['neighbors'][key]
    return df


def compare_shapefile_difference(shp_paths1, shp_paths2, verbose=False):
    '''
    Compare shapefiles to check how much difference is between them in terms
    of ratio of the first shapefile.

    A result of 0.90 ratio between the two shapefiles means that 90 percent
    of the first shapefile is NOT contained in the second shapefile. First path
    in list1 is compared to first list in path 2. Second path in list1 is
    compared to second path in list 2 and so on

    This is useful for comparing shapefiles received from local jurisdictions.

    Arguments:
        shp_paths1:
            LIST of paths to shapefiles to be compared

        shp_paths2:
            LIST of paths to shapefiles to compare

        verbose:
            whether to print the difference ratio as they
        are calculated

    Output:
        LIST of ratio of difference as described above for each shp pair.
        Returns false if the length of the lists are not the same
    '''

    # List of difference ratio to the first shapefile
    out = []

    # if list of shapefile lengths are not the same return false
    if len(shp_paths1) != len(shp_paths2):
        return False

    for ix in range(len(shp_paths1)):
        path1 = shp_paths1[ix]
        path2 = shp_paths2[ix]

        # Load in shapefiles
        shp1 = fm.load_shapefile(path1)
        shp2 = fm.load_shapefile(path2)

        # Get full geometries
        poly1 = shp.ops.cascaded_union(list(shp1['geometry']))
        poly2 = shp.ops.cascaded_union(list(shp2['geometry']))

        # calculate, store, and potentially print difference
        diff = poly2.difference(poly1).area
        out.append(diff)
        if verbose:
            name1 = path1.split('/')[-1]
            name2 = path2.split('/')[-1]
            print('Difference Between ' + name1 + ' and' + name2 + ': ' +
                  str(out[ix]))

    return out
