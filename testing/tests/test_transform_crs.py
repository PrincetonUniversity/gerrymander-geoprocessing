'''
Tests for merge shapefiles function
'''

import os, sys
os.chdir('../..')
sys.path.append(os.getcwd())
from edit_shapefiles import transform_crs
import helper_tools.file_management as fm
import shutil

def intitialize_test_files(filename):
	''' Initialize files to be edited for a given test 

	Argument:
		filename: file name of testing file with extension

	Output:
		path to shapefile to be edited'''

	# Get input data path given filename
	data_direc = os.getcwd() + "/testing/test_data/transform_crs/"
	data_path = data_direc + filename

	# Create directory to dump data into
	direc_path = os.getcwd() + "/testing/debug/transform_crs"
	if os.path.exists(direc_path):
		shutil.rmtree(direc_path)
	os.mkdir(direc_path)

	# get testing path
	test_path = direc_path + '/' + filename

	# copy file to our debugging directory
	shp = fm.load_shapefile(data_path)
	fm.save_shapefile(shp, test_path)

	# return testing path
	return test_path

def clean_test_files():
	''' Clean files that were used for testing '''
	direc_path = os.getcwd() + "/testing/debug/transform_crs"
	if os.path.exists(direc_path):
		shutil.rmtree(direc_path)

def apply_crs_test(filename, crs='epsg:4269', default=True):
	''' Apply coordinate reference system transform 

	Arguments:
		filename: name of testing shapefile
		crs: coordinate reference system to convert to'''

	# Initialize files for this specific test
	path = intitialize_test_files(filename)
	paths = [path]

	# perform transform_crs
	transform_crs(paths, crs)

	# Check that the projection is epsg:4269
	shp = fm.load_shapefile(path)


	if default:
		assert shp.crs == {'init': crs}
	else:
		converted_3395_dict = {'lon_0': 0,
								'datum': 'WGS84',
								'y_0': 0,
								'no_defs': True,
								'proj': 'merc',
								'x_0': 0,
								'units': 'm',
								'lat_ts':0}
		assert shp.crs == converted_3395_dict

	# clean up testing folders
	clean_test_files()

class TestTranformCRS:
	def test_default_with_projection(self):
		''' Test conversion to default CRS given that the shapefile already
		has a projection '''
		filename = 'projection.shp'
		apply_crs_test(filename)

	def test_default_no_projection(self):
		''' Test conversion to default CRS given that the shapefile doesn't 
		already have a projection '''
		filename = 'no_projection.shp'
		apply_crs_test(filename)

	def test_input_with_projection(self):
		''' Test conversion to input CRS given that the shapefile already
		has a projection '''
		filename = 'projection.shp'
		apply_crs_test(filename, 'epsg:3395', False)

	def test_input_no_projection(self):
		''' Test conversion to input CRS given that the shapefile doesn't 
		already have a projection '''
		filename = 'no_projection.shp'
		apply_crs_test(filename, 'epsg:3395', False)




