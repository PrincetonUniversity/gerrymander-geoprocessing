from helper_tools.shp_manipulation import set_CRS
import helper_tools.file_management as fm
import shapely as shp
import pandas as pd

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
		shp = set_CRS(shp, crs)
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

    We use the greatest area method. However, when no intersection with bounding
    box occurs, we simply use the nearest centroid.

    NOTE: By default interpolates a string type because it is a label

    Arguments:

        df_large: larger shapefile giving the labels
        large_cols: LIST of attributes from larger shp to interpolate to 
            smaller shp
        df_small: smaller shapefile receiving the labels
        small_cols: LIST of names for attributes given by larger columns.
            Default will be False, which means to use the same attribute names
        small_path: path to save the new dataframe to
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
    for col in large_cols:
        df_small[col] = pd.Series(dtype=object)

    # construct r-tree spatial index. Creates minimum bounding rectangle about
    # each geometry in df_from
    si = df_large.sindex

    # Get centroid for each geometry in the large shapefile
    df_large['centroid'] = df_large['geometry'].centroid

    # Find appropriate matching large geometry for each small geometry
    for ix, row in df_small.iterrows():
        # Get potential matches
        small_poly = row['geometry']
        potential_matches = [df_large.index[i] for i in 
            list(si.intersection(small_poly.bounds))]

        # No intersections with bounding boxes. Find nearest centroid
        if len(potential_matches) == 0:
            small_centroid = small_poly.centroid
            dist_series = df_large['centroid'].apply(lambda x:
                small_centroid.distance(x))
            large_ix = dist_series.idxmin()             

        # One intersection with bounding box. Only one match
        elif len(potential_matches) == 1:
            large_ix = potential_matches[0]

        # Multiple intersections with bounding box. compare fractional area
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