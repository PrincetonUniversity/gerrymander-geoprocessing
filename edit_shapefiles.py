from helper_tools.shp_manipulation import set_CRS
import helper_tools.file_management as fm
import shapely as shp

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