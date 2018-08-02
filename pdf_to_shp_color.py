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

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Virginia_Digitizing/Auto/CSV/southampton_redo.csv"
def main():
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        # Import Google Drive path
        with open(csv_path) as f:
            reader = csv.reader(f)
            data = [r for r in reader]
        direc_path = data[0][1]
    
        # Import table from CSV into pandas dataframe
        name_list = ['Locality', 'Num Regions', 'Census Path', 'Out Folder',\
                     'Image Path', 'Colors']
        in_df = pd.read_csv(csv_path, header=1, names=name_list)
    
        # Initialize out_df, which contains the results of the transfers and
        # contains what will be copied into the conversion page of the Google
        # sheet
        new_cols = ['Result', 'Time Taken', 'Num Census Blocks']
        out_df = pd.DataFrame(columns=new_cols)
        
        # Iterate through each county we are creating a shapefile for
        for i, _ in in_df.iterrows():
            
            # Create shapefile out of precincts
            try:
                # Begin Start time
                start_time = time.time()
                
                # Set unique variables for the current county
                local = in_df.at[i, 'Locality']
                num_regions = in_df.at[i, 'Num Regions']
                shape_path = in_df.at[i, 'Census Path']
                out_folder = in_df.at[i, 'Out Folder']
                img_path = in_df.at[i, 'Image Path']
                num_colors = in_df.at[i, 'Colors']
        
                # Change census shapefile path and out folder if set to default
                if shape_path == 1:
                    census_filename = local + '_census_block.shp'
                    census_filename = census_filename.replace(' ', '_')
                    shape_path = direc_path + '/' + local + '/' + \
                                    census_filename
                    
                if out_folder == 1:
                    out_folder = direc_path + '/' + local
                    
                # set ouput shapefile name
                out_name = local + '_precinct'
                out_name = out_name.replace(' ', '_')
                
                # Convert image to tiff if not already a tiff
                ext = ['tif', 'tiff']
                img_ext = img_path.split('.')[-1]
                if img_ext not in ext:
                    im = Image.open(img_path)
                    img_path =  out_folder + '/' + local + 'Cropped Image.tif'
                    im.save(img_path)
                
                # Generate precinct shapefile and add corresponding precinct
                # index to the attribute field of the census block shapefile
                print(local)
                result = generate_precinct_shapefile(local, num_regions, \
                                                      shape_path, out_folder, \
                                                      img_path, num_colors)
                
                # Place Results in out_df
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Time Taken'] = time.time() - start_time
                out_df.at[row, 'Num Census Blocks'] = result
            
            # Shapefile creation failed
            except Exception as e:
                print(e)
                print('ERROR:' + in_df.at[i, 'Locality'])
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
    
        # Create path to output our results CSV file and output
        csv_out_path = csv_path[:-4] + ' RESULTS.csv'
        out_df.to_csv(csv_out_path)
    
    # CSV file could not be read in or exported
    except:
        print('ERROR: Path for csv file does not exist OR close RESULTS csv')
        
def pt_to_pixel(coord, init_len, init_min, fin_len, rnd=False):
    ''' This function will convert a coordinate into its corresponding pixel
    on the image. Transforming from coordinates in geometry to coordinates in
    pixels. If transformed coordinates are less than 0, 0 will be returned. If
    transformed coordinates are greater than fin_len then fin_len will
    be returned. This is to assist indexing.
    
    Return: A transformed coordinate that can be used as a pixel index
    
    Arguments:
    coord: the iniital coordinate
    init_len: range of initial x coordiante
    init_min: min of initial x coordinate (min coordinate of polygon)
    fin_len: range of final coordinates (amount of pixels)
    rnd: whether to round final values up or down. Takes input string "up"
    or input string "down" for the new value'''
    
    # Make transformation with two operations. Move initial coordinates such 
    # that min is now zero. Multiply by the proportion of new length over
    # old length
    new = (coord - init_min) * fin_len / init_len

    # Perform Rounding for coord
    if rnd == "up":
        new  = math.ceil(new)
    elif rnd == "down":
        new  = math.floor(new)
    else:
         new = round(new)
        
    # Perform boundary check for X
    if new < 0:
         new = 0
    elif new > fin_len:
         new = fin_len        
    return new
    

def isBlack(color):
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


def most_common_color(img_arr, poly, img_xlen, img_ylen, shp_xlen, shp_ylen,
                    shp_xmin, shp_ymin, sample_limit):
    
    # triangulate polygon
    triangles = shp.ops.triangulate(poly)
    
    # make list of partial sums of areas so we can pick a random triangle
    # weighted by area
    areas = np.asarray([0])
    for triangle in enumerate(triangles):
        np.append(areas, areas[-1] + triangle.area)
    
    # scale so last sum is 1
    areas /= areas[-1]
    
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
        triangle = triangles[np.searchsorted(areas , r)]
        
        # select a point uniformly at random from this triangle
        pt = random_pt_in_triangle(triangle)
        
        # get color of pixel that corresponds to this point 
        ######### TODO TODO ##########
        ######### UPDATE pt_to_pixel #######
        color = [0, 0, 0]
        
        # add color to dictionary
        if color not in colors:
            colors[color] = 0
        colors[color] += 1
        
        # decide if we are done sampling (every 10 samples)
        if (count % 0 == 10):
            
            # find the most common color and its frequency
            common = max(colors.iteritems(), key=operator.itemgetter(1))[0]
            common_count = colors[common]
            
            # calculate z-score based on proportion test
            # trying to get evidence that this color is over 50% frequent
            # among all pixels
            z_score = (2 * common_count / count - 1) * np.sqrt(count)
            
            # stop sampling if we have convincing evidence or we hit our limit
            if (z_score > 4 or count > sample_limit):
                color_to_return = common
                stop_sampling = True
    
    return color_to_return
        
def most_common_color(img_getcolors):
    ''' This function will take in an image and return the most common color
    within the image
    
    Arguments:
    img_getcolors: array created from the method Image.getcolors. It will
    create a list of tuples. Each tuple has how many pixels have a given color
    and the value of the color
    '''
    
    # remove black pixels (probably just boundary, don't want to consider)
    img_getcolors = [color for color in img_getcolors if not isBlack(color[1])]
    
    if len(img_getcolors) == 0:
        img_getcolors = [(1, (0, 0, 0))]
    
    # Convert color counts into numpy array
    arr = np.array([item[0] for item in img_getcolors])
    
    # Get index of max color count
    max_ix = np.argmax(arr)

    # return the color that is found the most
    return img_getcolors[max_ix][1]

    
def image_bound_box(img_arr, poly, img_xlen, img_ylen, shp_xlen, shp_ylen,
                    shp_xmin, shp_ymin):
    ''' This function will return a subimage that is the bounding box around
    a given geometry
    
    Arguments:
    img_arr: this is the matrix of colors given by the full image
    poly: this is the geometry given by the current polygon beinge evaluated
    img_xlen: the number of pixels on the x axis of the full image
    img_ylen: "" y ""
    shp_xlen: range of x coordinates for entire shape
    shp_ylen: "" y ""
    shp_xmin: min of x coordinates for entire shape
    shp_ymin: "" y ""
    '''

    # Get the bounding box values for the inputted polygon
    bnd = poly.bounds
    
    # Convert boundaries into pixel coordinate system
    xmin = pt_to_pixel(bnd[0], shp_xlen, shp_xmin, img_xlen, "up")
    xmax = pt_to_pixel(bnd[2], shp_xlen, shp_xmin, img_xlen, "down")
    
    # rounding reversed becase they will be inverted due to top down
    ymin = pt_to_pixel(bnd[1], shp_ylen, shp_ymin, img_ylen, "down")
    ymax = pt_to_pixel(bnd[3], shp_ylen, shp_ymin, img_ylen, "up")
    
    # Invert y coordinates because image is indexed top down
    ymax_flip = img_ylen - ymin
    ymin_flip = img_ylen - ymax
    
    # Slice array to get array for subimage
    subarray = img_arr[ymin_flip:ymax_flip, xmin:xmax]
    
    # return the subimage
    return Image.fromarray(subarray)
    
def image_square_area(img_arr, poly, img_xlen, img_ylen, shp_xlen, shp_ylen,
                    shp_xmin, shp_ymin):
    ''' This function will return a subimage that is a square of the same area
    as the geometry centered at the centroid of the geometry
    
    Arguments:
    img_arr: this is the matrix of colors given by the full image
    poly: this is the geometry given by the current polygon beinge evaluated
    img_xlen: the number of pixels on the x axis of the full image
    img_ylen: "" y ""
    shp_xlen: range of x coordinates for entire shape
    shp_ylen: "" y ""
    shp_xmin: min of x coordinates for entire shape
    shp_ymin: "" y ""
    '''
    
    # get the area and centroid of the polygon
    area = poly.area
    c = list(poly.centroid.coords)
    
    # Calculate distance from centroid that will make a square of the same
    # area as the polygon. sqrt(area) / 2
    
    # CHANGED TO 1/4 OF AREA
    d = math.sqrt(area) / 2
    
    # Convert boundaries into pixel coordinate system
    xmin = pt_to_pixel(c[0][0] - d, shp_xlen, shp_xmin, img_xlen, "down")
    xmax = pt_to_pixel(c[0][0] + d, shp_xlen, shp_xmin, img_xlen, "up")
    ymin = pt_to_pixel(c[0][1] - d, shp_ylen, shp_ymin, img_ylen, "down")
    ymax = pt_to_pixel(c[0][1] + d, shp_ylen, shp_ymin, img_ylen, "up")
    
    # Invert y coordinates because image is indexed top down
    ymax_flip = img_ylen - ymin
    ymin_flip = img_ylen - ymax

    # Slice array to get array for subimage
    subarray = img_arr[ymin_flip:ymax_flip, xmin:xmax]
    
    # return the subimage
    return Image.fromarray(subarray)

def real_rook_contiguity(df, struct_type='list'):
    ''' Generates neighbor list using rook contiguity for a geodataframe.
    
    Arguments:
        df: geodataframe to apply rook contiguity to
        struct_type: determines whether neighbors are returned as a list or
        as a dict'''
    
    # Obtain queen continuity for each shape in the dataframe. We will remove 
    # all point contiguity. Shapely rook contiguity sometimes assumes lines
    # with small lines are points
    w = ps.weights.Queen.from_dataframe(df, geom_col='geometry')
    
    # Initialize neighbors column
    df['neighbors'] = pd.Series(dtype=object)   
    
    # Initialize neighbors for each precinct
    for i,_ in df.iterrows():
        struct = w.neighbors[i]
        
        # Iterate through every precinct to remove all neighbors that only 
        # share a single point. Rook contiguity would asssume some lines are 
        # points, so we have to use queen and then remove points
        
        # Obtain degree (# neighbors) of precinct
        nb_len = len(struct)
        
        # Iterate through neighbor indexes in reverse order to prevent errors 
        # due
        # to the deletion of elements
        for j in range(nb_len - 1, -1, -1):
            # get the jth neighbor
            j_nb = struct[j]
            
            # get the geometry for both precincts
            i_geom = df.at[i, 'geometry']
            j_nb_geom = df.at[j_nb, 'geometry']
            
            # If their intersection is a point, delete j_nb from i's neighbor 
            # list do not delete in both directions. That will be taken care of
            # eventually when i = j_nb later in the loop or before this occurs
            geom_type = i_geom.intersection(j_nb_geom).type
            if geom_type == 'Point' or geom_type == 'MultiPoint':
                del struct[j]
        
        # Assign to dataframe according to the structure passed in
        if struct_type == 'list':
            df.at[i, 'neighbors'] = struct
        elif struct_type == 'dict':
            df.at[i, 'neighbors'] = dict.fromkeys(struct)
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
    
def generate_precinct_shapefile(local, num_regions, shape_path, out_folder,\
                                img_path, colors=0):
    ''' Generates a precinct level shapefile from census block data and an 
    image cropped to a counties extents. Also updates the attribute table in
    the census block shapefile to have a precinct value.
    
    Arguments:
        local: name of the locality
        num_regions: number of precincts in the locality
        shape_path: full path to the census block shapefile
        out_folder: directory that precinct level shapefile will be saved in
        img_path: full path to image used to assign census blocks to precincts
        
    Output:
        Number of census blocks in the county
        '''        
    # Convert image to array, color reducing if specified
    img = Image.open(img_path)
    if colors > 0:
        img = reduce_colors(img, colors)
    img_arr = np.asarray(img)

    # Delete CPG file if it exists
    cpg_path = ''.join(shape_path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)
    
    # read in census block shapefile
    df = gpd.read_file(shape_path)

    # Create a new color and district index series in the dataframe
    add_cols = ['color', 'region', 'area']
    for i in add_cols:
        df[i] = pd.Series(dtype=object)
    
    # Calculate boundaries of the geodataframe using union of geometries
    bounds = list(shp.ops.cascaded_union(list(df['geometry'])).bounds)
    
    # Calculate global bounds for image and shape
    img_xlen = img.size[0]
    img_ylen = img.size[1]
    shp_xlen = bounds[2] - bounds[0]
    shp_ylen = bounds[3] - bounds[1]
    shp_xmin = bounds[0]
    shp_ymin = bounds[1]
    
    # set max color to a value > 256^3 so most_common_color doesn't return none
    maxc = 20000000
    count = 0
    # Itereate through each polygon and assign its most common color
    for i, _ in df.iterrows():
        
        # See timing
        if count % 100 == 0:
            print(count)
        count += 1
    
        # Get current polygon
        poly = df.at[i, 'geometry']
        
        # Calculate subimage
        sub_im = image_square_area(img_arr, poly, img_xlen, img_ylen, shp_xlen, 
                                   shp_ylen, shp_xmin, shp_ymin)
        
        # Set color for census block
        df.at[i, 'color'] = most_common_color(sub_im.getcolors(maxcolors=maxc))
    
    # Assign each polygon with a certain color a district index
    for i, color in enumerate(df['color'].unique()):
        df.loc[df['color'] == color, 'region'] = i
        
    ###########################################################################
    ###### CREATE PRECINCTS USING ID ##########################################
    ###########################################################################
    
    # Get unique values in the df ID column
    prec_id = list(df.region.unique())
    
    df_prec = pd.DataFrame(columns=['region', 'geometry'])
    
    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # union
    for i in range(len(prec_id)):
        df_poly = df[df['region'] == prec_id[i]]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'region'] = prec_id[i]
        
    ###########################################################################
    ###### SPLIT NON-CONTIGUOUS PRECINCTS (archipelagos)#######################
    ###########################################################################
    
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
    
            # Iterate through every contiguous region in the precinct
            for region in precinct.geoms:
                # Set geometry and id of new_shape
                d = {}
                d['region'] = df_prec.at[i, 'region']
                d['geometry'] = region
                df_prec = df_prec.append(d, ignore_index=True)
                
    # Remove original noncontiguous precincts
    df_prec = df_prec.drop(drop_ix)

    ###########################################################################
    ###### MERGE PRECINCTS FULLY CONTAINED IN OTHER PRECINCTS #################
    ###########################################################################
    
    df_prec = real_rook_contiguity(df_prec)
    
    # Multiple Contained Precincts Check
    # Create list of rows to drop at the end of the multiple contained check
    ids_to_drop = []
    
    # Iterate over all precincts except the state boundary precinct
    for i,_ in df_prec.iterrows():
        
        # Create polygon Poly for this precinct from its exterior coordinates. 
        # This polygon is currently without an interior. The purpose of filling
        # the interior is to allow for an intersection to see if a neighbor is
        # fully contained
        poly_coords = list(df_prec.at[i, 'geometry'].exterior.coords)
        poly = Polygon(poly_coords)
        
        # Create list of contained neighbor id's to delete
        nb_ix_del = []
    
        # Define a list that contains possibly contained precincts. If a 
        # precinct is nested witin other contained precincts, we will need to 
        # add it to this list
        possibly_contained = df_prec.at[i, 'neighbors']
        for j in possibly_contained:        
            
            # Check if the intersection of Poly (precint i's full polygon) and 
            # the current neighbor is equal to the current neighbor. This 
            # demonstrates that the current neighbor is fully contained within 
            # precinct i
            j_geom = df_prec.at[j, 'geometry']
            
            if j_geom == j_geom.intersection(poly):
                # j is fully contained within i. To account for nested 
                # precincts we append any neighbor of j that is not already in 
                # possibly_contained not including i
                for j_nb in df_prec.at[j, 'neighbors']:
                    if j_nb not in possibly_contained and j_nb != i:
                        possibly_contained.append(j_nb)
    
                # Add geometry of j to geometry of i
                polys = [df_prec.at[i, 'geometry'], 
                         df_prec.at[j, 'geometry']]
                df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
                            
                # add neighbor reference from precinct i to delete if a nb
                if j in df_prec.at[i, 'neighbors']:
                    nb_ix = df_prec.at[i, 'neighbors'].index(j)
                    nb_ix_del.append(nb_ix)
                
                # add neighbor precinct to the ID's to be dropped
                ids_to_drop.append(j)
                
        # Delete neighbor references from precinct i
        if len(nb_ix_del) > 0:
            # iterate through ixs in reverse to prevent errors through deletion
            for nb_ix in reversed(nb_ix_del):
                del(df_prec.at[i, 'neighbors'][nb_ix])
    
    # Drop contained precincts from the dataframe
    df_prec = df_prec.drop(ids_to_drop)

    ###########################################################################
    ###### MERGE PRECINCTS UNTIL WE HAVE THE RIGHT NUMBER #####################
    ###########################################################################
    
    # reset index for df_prec
    df_prec = df_prec.reset_index(drop=True)
    
    # Get rook contiguity through a dictionary and calculate the shared_perims
    df_prec = real_rook_contiguity(df_prec, 'dict')
    df_prec = get_shared_perims(df_prec)

    # get list of precinct indices to keep
    for i, _ in df_prec.iterrows():
        df_prec.at[i, 'area'] = df_prec.at[i, 'geometry'].area
    arr = np.array(df_prec['area'])
    
    precincts_to_merge = arr.argsort()[ : -num_regions]
    
    # Iterate through indexes of small "fake" precincts
    for i in precincts_to_merge:

        # update neighbors and shared_perims
        cur_prec = df_prec.at[i, 'neighbors']
        ix = max(cur_prec, key=cur_prec.get)
        merge_prec = df_prec.at[ix, 'neighbors']

        # merge dictionaries
        merge_prec = Counter(merge_prec) + Counter(cur_prec)

        # remove key to itself
        merge_prec.pop(ix)

        # set neighbor dictionary in dataframe
        df_prec.at[ix, 'neighbors'] = merge_prec
        
        # merge geometry
        df_prec.at[ix, 'geometry'] = df_prec.at[ix, 'geometry'].union\
            (df_prec.at[i, 'geometry'])
        
        # delete neighbor reference to i and add reference for merge to key
        for key in list(cur_prec):
            df_prec.at[key, 'neighbors'].pop(i)
            
            ##-----------------------------------------------------------------
            # get perimeter length for key in merge and set in 
            # neighbor list
            key_dist = df_prec.at[ix, 'neighbors'][key]
            df_prec.at[key, 'neighbors'][ix] = key_dist
        
    # delete all merged precincts
    df_prec = df_prec.drop(precincts_to_merge)
        
    # reset index for df_prec
    df_prec = df_prec.reset_index(drop=True)
        
    # set region values
    for i in range(len(df_prec)):
        df_prec.at[i, 'region'] = i
        
    ###########################################################################
    ###### Assign Census Blocks to Regions ####################################
    ###########################################################################

    df = assign_blocks_to_regions(df, df_prec)
    
    ###########################################################################
    ###### Save Shapefiles ####################################################
    ###########################################################################
    
    # Save census block shapefile with updated attribute table
    df = df.drop(columns=['color'])
    df.to_file(shape_path)
    
    # Save Precinct Shapefile
    out_name = local + '_precincts'
    out_name.replace(' ', '_')
    
    df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')
    df_prec = df_prec.drop(columns=['neighbors'])
    df_prec.to_file(out_folder + '/' + out_name + '.shp')
        
    return len(df)
        
if __name__ == '__main__':
    main()