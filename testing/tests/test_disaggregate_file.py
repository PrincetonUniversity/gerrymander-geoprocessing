'''
Tests for disaggregate file function
'''
# need to change path to import helper tools in the path
import os, sys, shutil
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.file_management as fm
import helper_tools.shp_manipulation as sm
from create_shapefiles import disaggregate_file
import shapely as shp
from shapely.geometry import Polygon

def folder_name(direc_path, attr, prefix, suffix):
	''' Check that folders are named correctly '''

	# Get name of folders
	folder_names = os.listdir(direc_path)

	# Check if folder was created for each attribute
	assert len(attr) == len(folder_names)

	# Check name of each folder
	for a in attr:
		correct_name = direc_path + '/' + prefix + a + suffix
		assert os.path.exists(correct_name)

	return True

def file_name(direc_path, attr, prefix, suffix):
	''' Check that files are named correclty '''

	# Check if all shapefiles exist
	for a in attr:
		correct_folder = direc_path + '/' + prefix + a + suffix
		correct_name = correct_folder + '/' + prefix + a + suffix + '.shp'
		assert os.path.exists(correct_name)

		# Ensure that there is only one shapefile
		for _, _, files in os.walk(correct_folder):
			num_shp = 0
			for name in files:
				if name[-3:] == 'shp':
					num_shp += 1

			assert num_shp == 1
	return True

def shapes(df_test, disaggregate_attr, direc_path, attr, prefix, suffix):
	''' Check that correct shapefiles were created for each attribute '''
	# Check if shapes are equal
	for a in attr:
		correct = df_test[df_test[disaggregate_attr] == a]
		correct_poly = shp.ops.cascaded_union(list(correct['geometry']))

		folder = direc_path + '/' + prefix + a + suffix
		name = folder + '/' + prefix + a + suffix + '.shp'
		test = fm.load_shapefile(name)
		test_poly = shp.ops.cascaded_union(list(test['geometry']))

		assert correct_poly.equals(test_poly)
	return True

def test_disaggregate_by_attribute():

	# Define Inputs
	test_data = "/testing/test_data/disaggregate_file/"
	test_data += "test_disaggregate_file.shp"
	shp_path = os.getcwd() +  test_data
	disaggregate_attr = 'attribute'
	prefix = 'prefix_'
	suffix ='_suffix'

	# Create directory to dump data into
	direc_path = os.getcwd() + "/testing/debug/disaggregate_file"
	if os.path.exists(direc_path):
		shutil.rmtree(direc_path)
	os.mkdir(direc_path)

	# Perform function
	disaggregate_file(shp_path, disaggregate_attr, direc_path, prefix, 
		suffix)

	# obtain test file and attributes
	df_test = fm.load_shapefile(shp_path)
	attr = list(set(df_test[disaggregate_attr]))

	# Perform Tests
	fold = folder_name(direc_path, attr, prefix, suffix)
	fname = file_name(direc_path, attr, prefix, suffix)
	shp = shapes(df_test, disaggregate_attr, direc_path, attr, prefix, 
		suffix)

	# Delete folder in debugging if all tests are passed
	if fold and fname and shp:
		shutil.rmtree(direc_path)
