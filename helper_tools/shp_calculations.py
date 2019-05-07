"""
Helper methods to calculate properties within shapefiles
"""

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
    ''' Return a dataframe with a new field, neighbors, containing a dictionary
    where the keys are indices of rook-contiguous neighbors and the values are
    shared perimeters.
    
    Arguments:
        df: geodataframe
    
    Output:
        geodataframe, with shared perimeter length in its dictionary
    '''
    df = real_rook_contiguity(df, struct_type='dict')
    
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
        triangle: Shapely polygon
        
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
        nbrs: dictionary with keys as neighbor indices, values as shared perims
        indices: indices for which we care about the fraction shared
        perim: perimeter of shape
    
    Output:
        fraction of perimter assigned
    '''
    # calcluate total perimeter shared with shapes at indices
    shared_perim = sum([nbrs[key] for key in nbrs if key in indices])
    
    return shared_perim/perim
