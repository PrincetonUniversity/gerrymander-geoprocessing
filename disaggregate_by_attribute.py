import os
import shutil
import geopandas as gpd
import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm

def disaggregate_by_attribute(shp_path, disaggregate_attr, direc_path, 
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

# print('start')

# # testing
# shp_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/test_data/disaggregate_by_attribute/test_disaggregate.shp"
# disaggregate_attr = 'attribute'
# direc_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/testing/debug/disagg_test"
# prefix = 'prefix_'
# suffix ='_suffix'

# disaggregate_by_attribute(shp_path, disaggregate_attr, direc_path, prefix, suffix)
