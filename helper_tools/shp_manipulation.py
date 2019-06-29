"""
Helper methods to make changes to shapefiles
"""

import geopandas as gpd
import pandas as pd
import shapely as shp
from shapely.geometry import Polygon

# import helper tools as if running from parent directory
import helper_tools.file_management as fm
import helper_tools.shp_calculations as sc

def old_merge_fully_contained(df, geo_id = 'geometry',
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
    
    # create neighbor list if it does not exist
    if (nbr_id not in df.columns):
        df = real_rook_contiguity(df)
    
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
                        
                # Add geometry of j to geometry of i
                polys = [df.at[i, 'geometry'], 
                         df.at[j, 'geometry']]
                df.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
    
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

def split_noncontiguous(df, cols_to_copy=[]):
    ''' Splits noncontiguous geometries in a dataframe and adds all polygons
    as their own attribute.
    
    Arguments:
        df: geodataframe
        cols_to_copy: columns from non-contiguous region to copy over to 
            all parts that were split off
    
    Output:
        df with no noncontiguous geometries
    '''
    
     # Initialize indexes to drop
    drop_ix = []
    
    # Iterate through every precinct
    for i, _ in df.iterrows():
        # Check if it precinct is a MultiPolygon
        if df.at[i, 'geometry'].type == 'MultiPolygon':
            # Add index as the index of a row to be dropped
            drop_ix.append(i)
            
            # get shape and area of current precinct
            precinct = df.at[i, 'geometry']
    
            # Iterate through every contiguous region in the precinct
            for region in precinct.geoms:
                # Set geometry of new shape, copy necessary fields
                d ={}
                d['geometry'] = region
                for col in cols_to_copy:
                    d[col] = df.at[i, col]
                df = df.append(d, ignore_index=True)
                
    # Remove original noncontiguous precincts
    df = df.drop(drop_ix)
    
    return df

def merge_geometries(df, indices_to_merge, cols_to_add=[]):
    '''
    Merges the geometries for given indices in a geodataframe into another
    geometry in the dataframe. Merges geometries by longest shared perimeter.
    Merges in order of most assigned perimeter (if geometry A has 50% of its
    perimeter assigned and geometry B has 40% of its area assigned, geometry
    A will be assigned before geometry B)
    
    Arguments:
        df: geodataframe
        indices_to_merge: indices of geometries that we want to merge into 
            some other geometry
        cols_to_add: columns in df to add as we merge (e.g. population)
        
    Output:
        geodataframe with merged geometries
    '''
    # Get neighbors dicts with shared_perims
    df = get_shared_perims(df)
    
    # Delete duplicates from indices_to_merge, which should never exist in
    # the first place but it would ruin the next part so let's be safe
    indices_to_merge = list(set(indices_to_merge))
    
    # temp list because we will be deleting
    original_indices_to_merge = indices_to_merge[:]
    
    # Merge while there are still geometries to merge
    while len(indices_to_merge) > 0:
        
        # find the index of the geometry to merge next, which is the geometry
        # with smallest fraction of its perimeter assigned to indices_to_merge
        fractions = [fraction_shared_perim(df.at[id, 'neighbors'],\
                                           indices_to_merge,\
                                           df.at[id, 'geometry'].length)\
                    for id in indices_to_merge]
        i = indices_to_merge[fractions.index(min(fractions))]

        # update neighbors and shared_perims
        cur_prec = df.at[i, 'neighbors']
        ix = max(cur_prec, key=cur_prec.get)
        merge_prec = df.at[ix, 'neighbors']

        # merge dictionaries
        merge_prec = Counter(merge_prec) + Counter(cur_prec)

        # remove key to itself
        merge_prec.pop(ix)

        # set neighbor dictionary in dataframe
        df.at[ix, 'neighbors'] = merge_prec
        
        # merge geometry
        df.at[ix, 'geometry'] = df.at[ix, 'geometry'].union\
            (df.at[i, 'geometry'])
        
        # delete neighbor reference to i and add reference for merge to key
        for key in list(cur_prec):
            df.at[key, 'neighbors'].pop(i)
            
            # get perimeter length for key in merge and set in 
            # neighbor list
            key_dist = df.at[ix, 'neighbors'][key]
            df.at[key, 'neighbors'][ix] = key_dist
            
        # remove i from indices to merge
        indices_to_merge.remove(i)
        
    # delete all merged precincts
    df = df.drop(original_indices_to_merge)
    
    return df

def merge_to_right_number(df, num_regions):
    ''' Decreases the number of attributes in a dataframe to a fixed number by
    merging the smallest geometries into the neighbor with which it shares the
    longest border.  Also creates 'region' field.
    
    Arguments:
        df: geodataframe to reduce geometries of
        num_regions: how many geometries to reduce to
        
    Output:
        reduced geodataframe
    '''
    # reset index for df
    df = df.reset_index(drop=True)
    
    # Get neighbors dicts with shared_perims
    df = get_shared_perims(df)

    # get list of precinct indices to merge (smallest areas)
    for i, _ in df.iterrows():
        df.at[i, 'area'] = df.at[i, 'geometry'].area
    arr = np.array(df['area'])
    
    precincts_to_merge = arr.argsort()[:-num_regions]
    
    # merge precincts_to_merge
    df = merge_geometries(df, precincts_to_merge)
    
    # reset index for df
    df = df.reset_index(drop=True)
        
    # set region values
    for i in range(len(df)):
        df.at[i, 'region'] = i
        
    return df

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
        cols_to_add: attributes that should be combined when precincts are
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








