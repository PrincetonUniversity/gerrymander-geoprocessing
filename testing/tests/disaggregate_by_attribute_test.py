'''
Tests for disaagregate_by_attribute script
'''
# need to change path to import helper tools in the path
import os, sys, shutil
os.chdir('../..')
sys.path.append(os.getcwd())

import helper_tools.file_management as fm
import helper_tools.shp_manipulation as sm
from create_shapefiles import disaggregate_by_attribute
import shapely as shp
from shapely.geometry import Polygon

def folder_name_test(direc_path, attr, prefix, suffix):
	''' Check that folders are named correctly '''

	# Get name of folders
	folder_names = os.listdir(direc_path)

	# Check if folder was created for each attribute
	if len(attr) != len(folder_names):
		print('Folder Creation Test FAILED: incorrect number of folders')
		return False

	# Check name of each folder
	for a in attr:
		correct_name = direc_path + '/' + prefix + a + suffix
		if not os.path.exists(correct_name):
			print('Folder Creation Test FAILED: incorrect folder name')
			return False
	print('Folder Creation Test PASSED')
	return True

def file_name_test(direc_path, attr, prefix, suffix):
	''' Check that files are named correclty '''



	# Check if all shapefiles exist
	for a in attr:
		correct_folder = direc_path + '/' + prefix + a + suffix
		correct_name = correct_folder + '/' + prefix + a + suffix + '.shp'
		if not os.path.exists(correct_name):
			print('File Name Test FAILED: incorrect file name')
			return False

		# Ensure that there is only one shapefile
		for _, _, files in os.walk(correct_folder):
			num_shp = 0
			for name in files:
				if name[-3:] == 'shp':
					num_shp += 1

			if num_shp != 1:
				print('File Name Test FAILED: not exactly one .shp per folder')
				return False

	print('File Name Test PASSED')
	return True

def shapes_test(df_test, disaggregate_attr, direc_path, attr, prefix, suffix):
	''' Check that correct shapefiles were created for each attribute '''
	# Check if shapes are equal
	for a in attr:
		correct = df_test[df_test[disaggregate_attr] == a]
		correct_poly = shp.ops.cascaded_union(list(correct['geometry']))

		folder = direc_path + '/' + prefix + a + suffix
		name = folder + '/' + prefix + a + suffix + '.shp'
		test = fm.load_shapefile(name)
		test_poly = shp.ops.cascaded_union(list(test['geometry']))

		if not correct_poly.equals(test_poly):
			print('Shapes Test FAILED: Incorrect shape for ' + str(a))
			return False
	print('Shapes Test PASSED')
	return True

# Define Inputs
test_data = "/testing/test_data/disaggregate_by_attribute/test_disaggregate.shp"
shp_path = os.getcwd() +  test_data
disaggregate_attr = 'attribute'
prefix = 'prefix_'
suffix ='_suffix'

# Create directory to dump data into
direc_path = os.getcwd() + "/testing/debug/disaggregate_by_attribute_test"
if os.path.exists(direc_path):
	shutil.rmtree(direc_path)
os.mkdir(direc_path)

# Perform function
disaggregate_by_attribute(shp_path, disaggregate_attr, direc_path, prefix, suffix)

# obtain test file and attributes
df_test = fm.load_shapefile(shp_path)
attr = list(set(df_test[disaggregate_attr]))

# Perform Tests
folder = folder_name_test(direc_path, attr, prefix, suffix)
file_name = file_name_test(direc_path, attr, prefix, suffix)
shapes = shapes_test(df_test, disaggregate_attr, direc_path, attr, prefix, suffix)

# Delete folder in debugging if all tests are passed
if folder and file_name and shapes:
	shutil.rmtree(direc_path)
