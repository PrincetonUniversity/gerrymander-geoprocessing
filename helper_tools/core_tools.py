"""
Helper methods to execute main algorithms.
    shp_from_sampling
        Create shapefile from image identifying precinct boundaries
    shp_from_manual_GIS
        Create shapefile from human entered boundaries
    interpolate_label
        label smaller geometries based on names of larger geometries
    interpolate_aggregate  
        aggregate values of smaller geometries into larger geometries
"""

import pandas as pd
import operator
from titlecase import titlecase

def shp_from_sampling(local, num_regions, shape_path, out_path, img_path, \
                      colors=0, sample_limit=500):
    ''' Generates a precinct level shapefile from census block data and an 
    image cropped to a locality's extents. Also updates the attribute table in
    the census block shapefile to have a region value that represents to 
    precinct id.
    
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
    delete_cpg(shape_path)
    
    # read in census block shapefile
    df = gpd.read_file(shape_path)

    # Create new series in dataframe
    add_cols = ['color', 'region']
    for i in add_cols:
        df[i] = pd.Series(dtype=object)
    
    # Calculate boundaries of the geodataframe using union of geometries
    bounds = shp.ops.cascaded_union(list(df['geometry'])).bounds
    
    # Calculate global bounds for shape
    shp_xlen = bounds[2] - bounds[0]
    shp_ylen = bounds[3] - bounds[1]
    shp_xmin = bounds[0]
    shp_ymin = bounds[1]

    # Iterate through each polygon and assign its most common color
    for i, _ in df.iterrows():
        
        # Get current polygon
        poly = df.at[i, 'geometry']
        
        # Set color for census block
        df.at[i, 'color'] = most_common_color(poly, img_arr, shp_xmin, \
             shp_xlen, shp_ymin, shp_ylen, sample_limit)
            
    # Assign each polygon with a certain color a district index
    for i, color in enumerate(df['color'].unique()):
        df.loc[df['color'] == color, 'region'] = i
    
    # Get unique values in the df precinct column
    prec_id = list(df.region.unique())

    # Initialize the precinct dataframe, which will eventually be exported
    # as the precinct shapefile
    df_prec = pd.DataFrame(columns=['region', 'geometry'])

    # cascaded union        
    for i, elem in enumerate(prec_id):
        df_poly = df[df['region'] == elem]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'region'] = elem
    
    # Split noncontiguous precincts
    df_prec = split_noncontiguous(df_prec)

    # Merge precincts fully contained in other precincts
    df_prec = merge_fully_contained(df_prec)
    
    # Convert precinct dataframe into a geodataframe
    df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')

    # Merge precincts until we have the correct number of precincts
    df_prec = merge_to_right_number(df_prec, num_regions)

    # Assign census blocks to regions
    df = interpolate_label(df, df_prec, [('region', 'region', 0)])
    
    # Save census block shapefile with updated attribute table
    save_shapefile(df, shape_path, cols_to_exclude=['color'])
   
    # Save precinct shapefile    
    generate_precinct_shp(local, shape_path, out_path, 'region')
        
    return len(df)

def shp_from_manual_GIS(local, shape_path, out_path, prec_col):
    ''' Generates a precinct level shapefile from census block data and a
    designated attribute column generated from assigning blocks in GIS. Also 
    updates the attribute table in the census block shapefile to have a 
    precinct value.
    
    Arguments:
        local: name of the locality
        shape_path: full path to the census block shapefile
        out_folder: directory that precinct level shapefile will be saved in
        prec_col: the column in the census block shapefile that denotes which
        precinct the block belongs to
        
    Output:
        Number of census blocks in the county
    ''' 
    # read in census block shapefile
    delete_cpg(shape_path)
    df = gpd.read_file(shape_path)

    
     # Get unique values in the df region column
    prec_id = list(df[prec_col].unique())

    
    # Check if there are census blocks not assigned to a prec_col
    if np.isnan(prec_id).any():
        # set num_regions to one less to acount for nan
        num_regions = len(prec_id) - 1

        # Assign blocks with nan prec_col to a dummy id
        for i, _ in df[df[prec_col].isnull()]:
            df.at[i, prec_col] = 'dummy_id' + str(i)
        
    # Every block is assigned and we do not need to account for nan in prec_id
    else:
        num_regions = len(prec_id)

    
    # reset the prec_id list
    prec_id = list(df[prec_col].unique())
    
    # Initialize the precinct dataframe, which will eventually be exported
    # as the precinct shapefile
    df_prec = pd.DataFrame(columns=[prec_col, 'geometry'])
    
    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # cascaded union        
    for i, elem in enumerate(prec_id):
        df_poly = df[df[prec_col] == elem]
        polys = list(df_poly['geometry'])
        df_prec.at[i, 'geometry'] = shp.ops.cascaded_union(polys)
        df_prec.at[i, prec_col] = elem
        
    # Split noncontiguous precincts
    df_prec = split_noncontiguous(df_prec)

    # Merge precincts fully contained in other precincts
    df_prec = merge_fully_contained(df_prec)

    # Merge precincts until we have the correct number of precincts
    df_prec = merge_to_right_number(df_prec, num_regions)
    
    # Convert precinct dataframe into a geodataframe
    df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')

    # Assign census blocks to regions
    df = interpolate_label(df, df_prec, [(prec_col, prec_col, 0)])
    
    # Save census block shapefile with updated attribute table
    save_shapefile(df, shape_path, cols_to_exclude=['color'])
    
    # Save precinct shapefile    
    generate_precinct_shp(local, shape_path, out_path, 'region')

    return len(df)

# def interpolate_label(df_to, df_from, adjust_cols, label_type='greatest area'):
#     ''' Label geometries (assign a text value0) in df_to from df_from based on
#     the label_type method. Also assigns elements that do not have overlapping 
#     bounding boxes by closeset centroid distance
    
#     Arguments:
#         to_df_path: path to the shapefile containing the dataframe to be 
#         modified
#         from_df_path: path to the shapefile used to modify to_df
#         adjust_cols: list of tuples that determine which df_to columns are
#         set equal to which df_from cols. Format column is string manipulation
#         to apply such as upper/lower/title case [(df_to_col1, df_from_col1, 
#         format_col1), (df_to_col2, df_from_col2, format_col2),...]
#         label_type: How to perform the labeling. Three valid types 
#         ('greatest area', 'first centroid', 'min centroid dist')
            
#     Output: To dataframe with the new series containing the labels
#     '''
    
#     # lowercase to help string matching
#     label_type = label_type.lower()
    
#     # Default set to greatest area
#     if label_type != 'min centroid dist' and label_type != 'first centroid':
#         label_type = 'greatest area'

#     # Read in input dataframe
#     df_from.index = df_from.index.astype(int)
    
#     # Need to define which columns in the to dataframe to drop. We will drop
#     # all columns from the csv that actuaslly exist in the to dataframe. We
#     # will also drop columns in the to_
#     drop_cols_before = []
#     drop_cols_after = []

#     for tup in adjust_cols:
#         # add to before drop
#         if tup[0] in df_to.columns:
#             drop_cols_before.append(tup[0])
            
#         # add to after drop
#         if tup[1] not in df_from.columns:
#             print('Column not in from df: ' + tup[1])
#             drop_cols_after.append(tup[0])

#     # Drop columns that are already in df_to
#     df_to = df_to.drop(columns=drop_cols_before)

#     # Create all output columns in the to_df
#     for tup in adjust_cols:
#         df_to[tup[0]] = pd.Series(dtype=object)

#     # construct r-tree spatial index. Creates minimum bounding rectangle about
#     # each geometry in df_from
#     si = df_from.sindex

#     # get centroid for al elements in df_from to take care of no intersection
#     # cases
#     df_from.loc[:, 'centroid'] = df_from.loc[:, 'geometry'].centroid

#     # iterate through every geometry in the to_df to match with from_df and set
#     # target values
#     for i, _ in df_to.iterrows():
    
#         # initialize current element's geometry and check which for minimum
#         # bounding rectangle intersections
#         df_to_elem_geom = df_to.at[i, 'geometry']
#         poss_df_from_elem = [df_from.index[i] for i in \
#                       list(si.intersection(df_to_elem_geom.bounds))]

#         # Initialize df_from_elem to be -1 to determine whether the centroid
#         # of the df_to_elem_geom was contained in a geometry in df_from
#         df_from_elem = -1

#         # If precinct's MBR only from_df geometry. Set it equal
#         if len(poss_df_from_elem) == 1:
#             df_from_elem = poss_df_from_elem[0]
#         else:
#             if label_type == 'greatest area':
#                 # for cases with multiple matches, compare fractional area
#                 frac_area = {}
#                 found_majority = False
#                 for j in poss_df_from_elem:
#                     if not found_majority:
#                         area = df_from.at[j, 'geometry'].intersection(\
#                                        df_to_elem_geom).area / \
#                                        df_to_elem_geom.area
#                         # Majority area means, we can assign
#                         if area > .5:
#                             found_majority = True
#                         frac_area[j] = area
    
#                 # if there was intersection get max of frac area
#                 if sum(frac_area.values()) > 0:
#                     df_from_elem = max(frac_area.items(), \
#                                      key=operator.itemgetter(1))[0]

#             elif label_type == 'first centroid':
#                 for j in poss_df_from_elem:
#                     # If centoid is contained by the geometry we stop
#                     if df_from.at[j, 'geometry'].contains(\
#                                  df_to_elem_geom.centroid):
#                         df_from_elem = j
#                         break
            
#             # If no matches were found with previous types or min dist type 
#             # was entered
#             if label_type == 'min centroid dist' or df_from_elem == -1:
#                 # get centroid for the current geometry
#                 c = df_to_elem_geom.centroid
#                 min_dist = -1
                
#                 # find the minimum distance index
#                 for j, _ in df_from.iterrows():
#                     cur_dist = c.distance(df_from.at[j, 'centroid'])
#                     if min_dist == -1 or cur_dist < min_dist:
#                         df_from_elem = j
#                         min_dist = cur_dist

#         # Set corresponding df_to values to df_from values if the column exist
#         # in from_df     
#         df_from_cols = df_from.columns
#         for tup in adjust_cols:
#             # Interpolate
#             if tup[1] in df_from_cols:
#                 input_str = df_from.at[df_from_elem, tup[1]]

#                 # Set formatting from input
#                 if tup[2] == 'U':
#                     input_str = input_str.upper()
#                 elif tup[2] == 'L':
#                     input_str = input_str.lower()
#                 elif tup[2] == 'T':
#                     input_str = titlecase(input_str)

#                 df_to.at[i, tup[0]] = input_str

#     # Delete and print columns that are missing in from dataframe
#     df_to = df_to.drop(columns=drop_cols_after)

#     # Return output dataframe
#     return df_to
    
# def interpolate_aggregate(df_to, df_from, adjust_cols, inter_type='fractional', 
#                           aggregate_on='area'):    
#     '''
#     Aggregate column values based on geometries in df_to from df_from based
#     on the interpolation type (inter_type) and what is decided to aggregate on
#     For from geometries that do not have any intersection with to geometries,
#     minimum centroid distance is used. For from geometries that are not
#     entirely contained within the to geometries, the leftover area is allocated
#     to the intersection with the largest area.
    
#     Arguments:
#         to_df_path: path to the shapefile containing the dataframe to be 
#         modified
#         from_df_path: path to the shapefile used to modify to_df
#         adjust_cols: list of tuples that determine which df_to columns are
#         set equal to which df_from cols. Round column is whether to round the
#         aggregated data. Preserve column is whether to preserve sums
#         [(df_to_col1, df_from_col1, round_col1, preserve_col1), 
#         (df_to_col2, df_from_col2, round_col2, preserve_col2),...]
#         inter_type: How to perform the labeling. Two valid inputs 
#         are 'winner take all' and 'fractional'
#         aggregate_on: Based on what value to perform the aggregation. For area
#         a new series is added
            
#     Output: To dataframe with the new series containing the labels
#     '''
#      # lowercase to help string matching
#     inter_type = inter_type.lower()
#     if aggregate_on.lower() == 'area':
#         aggregate_on = 'area'
    
#     # Default set to fractional        
#     if inter_type != 'fractional' and inter_type != 'winner take all':
#         inter_type = 'fractional'
        
#     if aggregate_on not in df_to.columns and aggregate_on != 'area':
#         print('aggregate_on value not in df_to columns')
#         print('interpolation cancelled for this dataframe')
#         return 0
    
#     # Get index for df_from
#     df_to.index = df_to.index.astype(int)
    
#     # Need to define which columns in the to dataframe to drop. We will drop
#     # all columns from the csv that actuaslly exist in the to dataframe. We
#     # will also drop columns in the to_
#     drop_cols_before = []
#     drop_cols_after = []

#     for tup in adjust_cols:
#         # add to before drop
#         if tup[0] in df_to.columns:
#             drop_cols_before.append(tup[0])
            
#         # add to after drop. This list will later be used to delete columns
#         # that will only contain null values
#         if tup[1] not in df_from.columns:
#             print('Column not in from df: ' + tup[1])
#             drop_cols_after.append(tup[0])

#     # Drop columns that are already in df_to
#     df_to = df_to.drop(columns=drop_cols_before)

#     # Create all output columns in the to_df
#     for tup in adjust_cols:
#         df_to[tup[0]] = pd.Series(0, dtype=float)

#     # construct r-tree spatial index. Creates minimum bounding rectangle about
#     # each geometry in df_from
#     si = df_to.sindex

#     # get centroid for al elements in df_from to take care of no intersection
#     # cases
#     df_to.loc[:, 'centroid'] = df_to.loc[:, 'geometry'].centroid

#     # iterate through every geometry in the to_df to match with from_df and set
#     # target values
#     for i, _ in df_from.iterrows():
    
#         # initialize current element's geometry and check which for minimum
#         # bounding rectangle intersections
#         i_geom = df_from.at[i, 'geometry']
#         poss_df_to_elem = [df_to.index[m] for m in 
#                       list(si.intersection(i_geom.bounds))]

#         # Get the fractional area for each intersecting geometry
#         frac_area = {}
#         for j in poss_df_to_elem:
#             # Get intersection of the two areas
#             j_geom = df_to.at[j, 'geometry']
#             area_intersection = i_geom.intersection(j_geom)
            
#             # Only add to the dictionary during if intersection is nonzero
#             if area_intersection > 0:
#                 frac_area[j] = area_intersection / i_geom.area
                
#         # Get nearest centroid if df_from element does not intersect with any
#         # df_to elements
#         if frac_area == {}:
#             # get centroid for the current geometry
#             c = i_geom.centroid
#             min_dist = -1
            
#             # find the minimum distance index
#             for j, _ in df_to.iterrows():
#                 cur_dist = c.distance(df_to.at[j, 'centroid'])
#                 if min_dist == -1 or cur_dist < min_dist:
#                     # Reset frac area and make area value equal to 1
#                     frac_area = {}
#                     frac_area[j] = 1
                    
#         # Add any remaining (non-intersected) area to the to geometry with
#         # the maximum overlapping area
#         unused_area = 1 - sum(frac_area.values())
#         if unused_area > 0:
#             max_elem = max(frac_area.items(), key=operator.itemgetter(1))[0]
#             frac_area[max_elem] += unused_area
                               
#         # Create frac_col out of frac area. This will contain the index
#         # in the to dataframe and the series value
#         if aggregate_on != 'area':
#             frac_col = {}
#             for key in frac_area.keys():
#                 frac_col[key] = df_to.at[key, aggregate_on]
#         # Use area to aggregate_on
#         else:
#             frac_col = frac_area
                    
#         # Iterate through the tupless containing data on columns as well as
#         # round/preserve
#         for tup in adjust_cols:
#             if tup[1] in df_from.columns:
#                 # Case for winner take all
#                 if inter_type == 'winner take all':
#                     # Get the maximum element
#                     df_to_elem = max(frac_col.items(), \
#                                      key=operator.itemgetter(1))[0]
#                     df_to.at[df_to_elem, tup[0]] += df_from.at[i, tup[1]]
                    
#                 elif inter_type == 'fractional':
#                     for to_ix, perc_col in frac_col.items():
#                         df_to.at[to_ix, tup[0]] += df_from.at[i, tup[1]] \
#                                                     * perc_col
                        
#                 # Round values based on value in tup
#                 if tup[2] == '1':
#                     # Save old values for preserve
#                     old_col = tup[0] + '_OLD'
#                     old_sum = df_to[old_col].sum()
#                     df_to[old_col] = df_to[tup[0]]
                    
#                     # Perform the round
#                     df_to[tup[0]] = df_to[tup[0]].round().astype(int)
                    
#                     # Preserve totals based on value in tup
#                     if tup[3] == '1':
#                         # Decrement randomly if rounding caused overestimate
#                         if df_to[tup[0]].sum() > old_sum:
#                             # Get indexes of geometries that were rounded up
#                             rnd_up = list(df_to[df_to[tup[0]] > \
#                                             df_to[old_col]].index)
            
#                             # Iterate until we have preserved total within 1
#                             while abs(old_sum - df_to[tup[0]].sum()) < 1:
#                                 # Apply decrement
#                                 ix = random.choice(rnd_up)
#                                 df_to.at[ix, tup[0]] = df_to.at[ix, tup[0]] - 1
                                
#                         # Increment randomly if rounding caused underestimate
#                         if df_to[tup[0]].sum() < old_sum:
#                              # Get indexes of geometries that were rounded down                      
#                             rnd_down = list(df_to[df_to[tup[0]] > \
#                                             df_to[old_col]].index)
                        
#                             # Iterate until we have preserved total within 1
#                             while abs(old_sum - df_to[tup[0]].sum()) < 1:
#                                 # Apply increment
#                                 ix = random.choice(rnd_down)
#                                 df_to.at[ix, tup[0]] = df_to.at[ix, tup[0]] + 1
                                
#                     # Drop old column
#                     df_to = df_to.drop(columns=[old_col])
                        
#     # Delete and print columns that are missing in from dataframe
#     df_to = df_to.drop(columns=drop_cols_after)

#     # Return output dataframe
#     return df_to
#     