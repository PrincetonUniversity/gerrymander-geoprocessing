import shutil, os
import geopandas as gpd
import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm
import pandas as pd

def dissolve_by_attribute(in_path, dissolve_attribute, out_path=False):
	''' 
	Dissolve boundaries for shapefile(s) according to a given attribute. we will
	also check for contiguity after boundaries have been dissolved.

	Arguments:
		in_path: full path to input shapefile to be dissolved
		out_path: full path to save created shapefile
		disolve_attribute: attribute to dissolve boundaries by
	'''
	#  Generate dissolved shapefile
	df = fm.load_shapefile(in_path)
	df = sm.dissolve(df, dissolve_attribute)

	# Print potential errors
	sc.check_contiguity_and_contained(df, dissolve_attribute)

	# Save shapefile
	if out_path:
		fm.save_shapefile(df, out_path)

	return df

def create_bounding_frame(in_path, out_path=False):
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

	if out_path:
		fm.save_shapefile(bounding_frame_df, out_path)

	return df

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


def merge_shapefiles(paths_to_merge, out_path=False, keep_cols='all'):
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

	if out_path:
		fm.save_shapefile(df_final, out_path, exclude_cols)

	return df_final

def clean_manual_classification(in_path, classification_col, out_path=False):
	'''Generate a dissolved boundary file given of larger geometries after 
	being given a geodataframe with smaller geometries assigned to a value
	designated by the classification column.

	Will auto-assign unassigned geometries using the greedy shared perimeters
	method.

	Will also split non-contiguous geometries and merge fully contained 
	geometries

	Usually used when a user has manually classified census blocks into
	precincts and needs to clean up their work

	Arguments:
		in_path: path dataframe containing smaller geometries

		classification_col: name of colum in df that identifies which
			larger "group" each smaller geometry belongs to.

		out_path: path to save final dataframe file if applicable. Default
			is false and will not save
	'''

	df = fm.load_shapefile(in_path)

	# obtain unique values in classification column
	class_ids = list(df[classification_col].unique())

	# determine the number of larger "groups"
	num_classes = len(class_ids)

	# Check if there are any unassigned census blocks
	if None in class_ids:
		# decrement number of regions because nan is not an actual region
		num_classes -= 1

		# Assign unassigned blocks a unique dummy name
		for i, _ in df[df[classification_col].isnull()].iterrows():
			df.at[i, classification_col] = 'foobar' + str(i)

	# Update the classes to include the dummy groups
	class_ids = list(df[classification_col].unique())

	# Dissolve the boundaries given the group assignments for each small geom
	df = sm.dissolve(df, classification_col)

	# Split noncontiguous geometries after the dissolve
	df = sm.split_noncontiguous(df)

	# Merge geometries fully contained in other geometries
	df = sm.merge_fully_contained(df)

	# Get the correct number of regions
	df_nan = df[df[classification_col].str.slice(0, 6) == 'foobar']
	ixs_to_merge = df_nan.index.to_list()
	df = sm.merge_geometries(df, ixs_to_merge)

	# drop neighbor column and reset the indexes
	df = df.drop(columns=['neighbors'])
	df = df.reset_index(drop=True)

	# save file if necessary
	if out_path:
		fm.save_shapefile(df, out_path)

	return df