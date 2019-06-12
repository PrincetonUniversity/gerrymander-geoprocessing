from helper_tools.shp_manipulation import set_CRS
import helper_tools.file_management as fm

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

'''
testing Notes
	see onenote

	Different projections
		default: epsg:4269
		other1: epsg:4326
		other2: epsg:3395
'''