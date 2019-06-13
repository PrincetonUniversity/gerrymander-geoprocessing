import shutil, os
import geopandas as gpd
import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm
import pandas as pd

def dissolve_by_attribute(in_path, out_path, dissolve_attribute):
	''' 
	Dissolve boundaries for shapefile(s) according to a given attribute. we will
	also check for contiguity after boundaries have been dissolved.

	Arguments:
		in_path: full path to input shapefile to be dissolved
		out_path: full path to save created shapefile
		disolve_attribute: attribute to dissolve boundaries by
	'''
	#  Generate dissolved shapefile
	geo_df = fm.load_shapefile(in_path)
	geo_df = sm.dissolve(geo_df, dissolve_attribute)

	# Print potential errors
	sc.check_contiguity_and_contained(geo_df, dissolve_attribute)

	# Save shapefile
	fm.save_shapefile(geo_df, out_path)

def create_bounding_frame(in_path, out_path):
	''' 
	Create a bounding box around the extents of a shapefile. 

	This will be used to overlay on top of a georeferenced image in GIS to allow for
	automated cropping in the algorithm that converts converting precinct images to 
	shapefiles. Will usually use a census block shapfile to generate this bounding
	frame

	Arguments:
		in_path: full path to input shapefile to create bounding frame for
		out_path: full path to save bounding frame shapefile
	'''
	# Generate bounding frame and save
	df = fm.load_shapefile(in_path)
	bounding_frame_df = sm.generate_bounding_frame(df)
	fm.save_shapefile(bounding_frame_df, out_path)

def disaggregate_file(shp_path, disaggregate_attr, direc_path, 
	prefix = '', suffix=''):
	'''
	Take a larger shapefile and disaggreagate it into smaller shapefiles 
	according to an attribute. The directory and shapefile name will be 
	prefix + disaggregate_attribute value + suffix.

	NOTE: direc_path SHOULD NOT END WITH '/'

	Example: Use to disaggregate statewide census block file to county census
	block files

	If available load in shp_path withh a pickle file rather than the actual
	shapefile. Loading in statewide census files takes a while

	Arguments:
		shp_path: path to shapefile to disaggregate
		disaggregate_attr: attribute to disaggregate on
		direc_path: path to directory to create subdirectory of smaller 
		shapefiles for each unique value.
		prefix: string to put in front name of smaller shapefiles
		suffix: string to put behind name of smaller shapefiles
	'''

	# load shapefile
	df = fm.load_shapefile(shp_path)

	# Get unique elements of each attribute
	attributes = set(df[disaggregate_attr])

	# For each attribute create subdirectory, create smaller shapefile, and save
	for attr in attributes:

		# name of subdirectory and new shapefile
		name = prefix + attr + suffix
		subdirec = direc_path + '/' + name
		shp_name = name + '.shp'

		# create subdirectory
		if os.path.exists(subdirec):
			shutil.rmtree(subdirec)
		os.mkdir(subdirec)

		# create shapefile with the correct attributes
		df_attr = df[df[disaggregate_attr] == attr]
		df_attr = gpd.GeoDataFrame(df_attr, geometry='geometry')
		fm.save_shapefile(df_attr, subdirec + '/' + name + '.shp')


def merge_shapefiles(paths_to_merge, out_path, keep_cols='all'):
	'''
	Combine multiple shapefiles into a single shapefile

	Arguments:
		paths_to_merge: LIST of path strings of shapfiles to merge
		out_path: path to save new shapefile
		keep_cols: default -> 'all' meeans to keep all, otherwise this input 
			takes a LIST of which columns/attributes to keep

	'''
	# Initalize Output DatFarme
	df_final = pd.DataFrame()

	# Loop through paths and merge
	for path in paths_to_merge:

		# Load and append current dataframe
		df_current = fm.load_shapefile(path)
		df_final = df_final.append(df_current, ignore_index=True, sort=True)


	# reduce to only columns/attributes we are keeping
	if keep_cols == 'all':
		exclude_cols = []
	else:
		exclude_cols = list(set(df_final.columns) - set(keep_cols))

	# Save final shapefile
	df_final = gpd.GeoDataFrame(df_final, geometry='geometry')
	fm.save_shapefile(df_final, out_path, exclude_cols)



'''
testing notes
	check that the correct columns are there
	check that the correct shapes are there

	What shapefiles do I need to create

	Correct shapefile
	Three individual shapefiles
	3 columns named ['col1', 'col2', 'col3']
'''