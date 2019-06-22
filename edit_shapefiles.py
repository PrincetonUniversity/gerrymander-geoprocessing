import helper_tools.file_management as fm
import shapely as shp
import pandas as pd
import numpy as np

def transform_crs(shp_paths, crs='epsg:4269'):
	'''
	Update the coordinate refernce system for a set of shapefiles

	Arguments:
		shp_paths: LIST of paths to shapefiles to be edited
		crs: the coordinate reference system to convert to. Default is above

	Output:
		None, but the original file will be edited and updated
	'''

	# Iterate over all paths
	for path in shp_paths:
		# load, add crs, and save
		shp = fm.load_shapefile(path)
		shp = fm.set_CRS(shp, crs)
		fm.save_shapefile(shp, path)

def remove_geometries(path_delete, save_path, path_reference, thresh):
	'''	Delete geometries from a shapefile that does not have a percent area
		intersetion above a inputted threshold.

		Arguments:
			path_delete: path to shapefile that we are editing (deleting 
				shapes without enough intersection)
			save_path: path to save edited shapefile after geometries have
				been removed from the path_delete shapefile. If false, we will
				not save
			path_reference: path to shapefile we will be comparing the
				intersection with. Intersections will be taken with respect
				to the union of all of these geometries
			thresh: fraction threshold required to keep a shape. If thresh is
				0.9 then any shape with an intersection ratio greater than or
				equal to 0.9 will remain and anything below will be deleted

		Output:
			edited dataframe with shapes removed
	'''
	# Load shapefiles
	df_del = fm.load_shapefile(path_delete)
	df_ref = fm.load_shapefile(path_reference)

	# Get full reference poly
	ref_poly = shp.ops.cascaded_union(list(df_ref['geometry']))

	# Get ratio for each element
	df_del['ratio'] = df_del['geometry'].apply(lambda x:
		x.intersection(ref_poly).area / x.area)

	# Filter out elements less than threshold
	df_del = df_del[df_del.ratio >= thresh]

	# drop ratio series
	df_del = df_del.drop(columns=['ratio'])

	# Save and return
	if save_path:
		fm.save_shapefile(df_del, save_path)

	return df_del

def distribute_label(df_large, large_cols, df_small, small_cols=False, 
        small_path=False):
    ''' Take labels from a shapefile that has larger boundaries and interpolate
    said labels to shapefile with smaller boundaries. By smaller boundaries we
    just mean more fine geographic boundaries. (i.e. census blocks are smaller
    than counties)

    We use the greatest area method. However, when no intersection occurs, we 
    simply use the nearest centroid.

    NOTE: By default interpolates a string type because it is a label

    Arguments:

        df_large: larger shapefile giving the labels
        large_cols: LIST of attributes from larger shp to interpolate to 
            smaller shp
        df_small: smaller shapefile receiving the labels
        small_cols: LIST of names for attributes given by larger columns.
            Default will be False, which means to use the same attribute names
        small_path: path to save the new dataframe to

    Output:
    	edited df_small dataframe
    '''

    # handle default for small_cols
    if small_cols == False:
        small_cols = large_cols

    # Check that large and small cols have same number of attributes
    if len(small_cols) != len(large_cols):
        return False
    
    if not set(large_cols).issubset(set(df_large.columns)):
        return False

    # Let the index by an integer for spatial indexing purposes
    df_large.index = df_large.index.astype(int)

    # Drop small_cols in small shp if they already exists
    drop_cols = set(small_cols).intersection(set(df_small.columns))
    df_small = df_small.drop(columns=drop_cols)

    # Initialize new series in small shp
    for col in small_cols:
        df_small[col] = pd.Series(dtype=object)

    # construct r-tree spatial index
    si = df_large.sindex

    # Get centroid for each geometry in the large shapefile
    df_large['centroid'] = df_large['geometry'].centroid

    # Find appropriate matching large geometry for each small geometry
    for ix, row in df_small.iterrows():
        # Get potential matches
        small_poly = row['geometry']
        potential_matches = [df_large.index[i] for i in 
            list(si.intersection(small_poly.bounds))]

        # Only keep matches that have intersections
        potential_matches = [m for m in potential_matches 
            if df_large.at[m, 'geometry'].intersection(small_poly).area > 0]

        # No intersections. Find nearest centroid
        if len(potential_matches) == 0:
            small_centroid = small_poly.centroid
            dist_series = df_large['centroid'].apply(lambda x:
                small_centroid.distance(x))
            large_ix = dist_series.idxmin()             

        # One intersection. Only one match
        elif len(potential_matches) == 1:
            large_ix = potential_matches[0]

        # Multiple intersections. compare fractional area
        # of intersection
        else:
            area_df = df_large.loc[potential_matches, :]
            area_series = area_df['geometry'].apply(lambda x: 
                x.intersection(small_poly).area / small_poly.area)
            large_ix = area_series.idxmax()

        # Update values for the small geometry
        for j, col in enumerate(large_cols):
            df_small.at[ix, small_cols[j]] = df_large.at[large_ix, col]

    # Save and return the updated small dataframe
    if small_path:
        fm.save_shapefile(df_small, small_path)
    return df_small

def aggregate(df_small, small_cols, df_large, large_cols=False, 
    agg_type='fractional', agg_on='area', agg_round=False, large_path=False):
    '''
    Aggregate attribute values of small geometries into the larger geometry.

    An example of this would be calculating population in generated precincts.
    We would take census blocks (the small geometries) and sum up their 
    values into the precincts (larger geometries)

    There are two types of aggregation. fractional or winner take all. 

    We also can aggregate on area or on another attribute

    For small geometries that do not have any intersection with large
    
    Arguments:
        df_small: smaller shapefile providing the aggregation values
        small_cols: LIST of columns/attributes to aggregate on
        df_large: larger shapefile receiving aggregated values
        large_cols: LIST of names of attributes for values being aggregated.
            elements in this list correspond to elements in small_cols with
            the same index. Default is just the names of the columns in
            small_cols
        agg_type: 'fractional' or 'winner take all'. form of aggregation. If 
            a small geometry intersects two larger geometries, then its 
            values will be either fractionally distributed if 'fractional'
            or given to the large geometry with the most intersection if
            'winner take all'. Default is fractional, which is most common
        agg_on: attribute to aggregate on. Default will be area
        agg_round: whether to round values. If it is True, then keep fractional
            sums rather than rounding the value. If we round the value, we
            will retain totals
        large_path: path to save df_large to. Default is to not save

    Output:
        edited df_large dataframe'''

    # Handle default for large_cols
    if large_cols == False:
            large_cols = small_cols

    # Check that large_cols and small_cols have same number of attributes
    if len(small_cols) != len(large_cols):
        print('Different number of small_cols and large_cols')
        return False

    # Check that small_cols are actually in dataframe
    if not set(small_cols).issubset(set(df_small.columns)):
        print('small_cols are not in dataframe')
        return False

    # Check that the type is either fractional area or winner take all
    if agg_type != 'fractional' and agg_type != 'winner take all':
        print('incorrect aggregation type')
        return False

    # If we are not aggregating on area check if the aggregation attribute
    # is in the dataframe
    if agg_on != 'area' and agg_on not in df_large.columns:
        print('aggregation attribute not in dataframe')
        return False

    # Let the index of ths large dataframe be an integer for indexing purposes
    df_large.index = df_large.index.astype(int)

    # Drop large_cols in large shp
    drop_cols = set(large_cols).intersection(set(df_large.columns))
    df_large = df_large.drop(columns=drop_cols)

    # Initialize the new series in the large shp
    for col in large_cols:
        df_large[col] = 0.0

    # construct r-tree spatial index
    si = df_large.sindex

    # Get centroid for each geometry in large shapefile
    df_large['centroid'] = df_large['geometry'].centroid

    # Find appropriate match between geometries
    for ix, row in df_small.iterrows():

        # initialize fractional area series, this will give what ratio to
        # aggregate to each large geometry
        frac_agg = pd.Series(dtype=float)

        # Get potential matches
        small_poly = row['geometry']
        potential_matches = [df_large.index[i] for i in 
            list(si.intersection(small_poly.bounds))]

        # Only keep matches that have intersections
        potential_matches = [m for m in potential_matches 
            if df_large.at[m, 'geometry'].intersection(small_poly).area > 0]

        # No intersections. Find nearest centroid
        if len(potential_matches) == 0:
            small_centroid = small_poly.centroid
            dist_series = df_large['centroid'].apply(lambda x:
                small_centroid.distance(x)) 
            frac_agg.at[dist_series.idxmin()] = 1

        # Only one intersecting geometry
        elif len(potential_matches) == 1:
            frac_agg.at[potential_matches[0]] = 1

        # More than one intersecting geometry
        else:
            agg_df = df_large.loc[potential_matches, :]

            # Aggregate on proper column
            if agg_on == 'area':
                frac_agg = agg_df['geometry'].apply(lambda x:
                    x.intersection(small_poly).area / small_poly.area)

                # Add proportion that does not intersect to the large geometry
                # with the largest intersection
                leftover = 1 - frac_agg.sum()
                frac_agg.at[frac_agg.idxmax()] += leftover

            else:
                agg_df[agg_on] = agg_df[agg_on].astype(float)
                agg_col_sum = agg_df[agg_on].sum()
                print(agg_col_sum)
                frac_agg = agg_df[agg_on].apply(lambda x:
                    float(x) / agg_col_sum)

        # Update value for large geometry depending on aggregate type
        for j, col in enumerate(large_cols):
            # Winner take all update
            if agg_type == 'winner take all':
                large_ix = frac_agg.idxmax()
                df_large.at[large_ix, col] += df_small.at[ix, small_cols[j]]

            # Fractional update
            elif agg_type == 'fractional':
                # Add the correct fraction
                for ix2, val in frac_agg.iteritems():
                    df_large.at[ix2, col] += df_small.at[
                        ix, small_cols[j]] * val

                # Round if necessary
                if agg_round:

                    # round and find the indexes to round up
                    round_down = df_large[col].apply(lambda x: np.floor(x))
                    decimal_val = df_large[col] - round_down
                    n = int(np.round(decimal_val.sum()))
                    round_up_ix = list(decimal_val.nlargest(n).index)

                    # Round everything down and then increment the ones that
                    # have the highest decimal value
                    df_large[col] = round_down
                    for ix3 in round_up_ix:
                        df_large.at[ix3, col] += 1

    # Set column value as integer
    if agg_round:
        df_large[col] = df_large[col].astype(int)

    # Save and return. also drop centroid attribute
    df_large = df_large.drop(columns=['centroid'])
    if large_path:
        fm.save_shapefile(df_large, large_path)
    return df_large