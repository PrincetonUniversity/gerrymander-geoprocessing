'''
Tests for merge shapefiles function
'''

import os, sys, shutil
import geopandas as gpd
os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.shp_manipulation as sm
import helper_tools.file_management as fm
import shapely as shp
from shapely.geometry import Polygon
from create_shapefiles import merge_shapefiles

def apply_merge(keep_cols):
	''' Apply merging of shapefiles for testing 
	Takes in list of columns to keep'''

	folder = os.getcwd()
	folder += "/testing/test_data/merge_shapefiles/"

	# Get smaller shapefiles that are to be merged
	in_paths = []
	in_paths.append(folder + "input_part1.shp")
	in_paths.append(folder + "input_part2.shp")
	in_paths.append(folder + "input_part3.shp")

	# get the path to put the output
	out_direc = os.getcwd() + "/testing/debug/merge_shapefiles/"
	out_path = out_direc + "merge.shp"
	if not os.path.exists(out_direc):
		os.mkdir(out_direc)

	# Perform merge
	merge_shapefiles(in_paths, out_path, keep_cols)

class TestMergeShapfiles:
	def test_geometry_merge(self):
		'''Ensure geometries merged correctly. Don't keep any columns
		Merge three files together then check against a known correct file'''

		folder = os.getcwd() + "/testing/test_data/merge_shapefiles/"

		# Get correct path and output path to check
		correct_str = "input_full.shp"
		correct_path = folder + correct_str

		# get the path to put the output
		out_direc = os.getcwd() + "/testing/debug/merge_shapefiles/"
		out_path = out_direc + "merge.shp"

		# Perform merge
		apply_merge([])

		# Load test and correct shapefiles
		test = fm.load_shapefile(out_path)
		correct = fm.load_shapefile(correct_path)

		# Perform geometry comparison
		test_poly = shp.ops.cascaded_union(list(test['geometry']))
		correct_poly = shp.ops.cascaded_union(list(correct['geometry']))
		assert correct_poly.equals(test_poly)

		# remove folder in debug
		shutil.rmtree(out_direc)

	def test_keep_colummns_input(self):
		'''Check that all of the columns were kept after the merge'''

		# Correct columns
		correct_cols = ['col1', 'col2', 'geometry']

		apply_merge(correct_cols)

		# get the path to put the output
		out_direc = os.getcwd() + "/testing/debug/merge_shapefiles/"
		out_path = out_direc + "merge.shp"

		# Load test and check columns
		test = fm.load_shapefile(out_path)
		assert set(test.columns) == set(correct_cols)

		# remove folder in debug
		shutil.rmtree(out_direc)


	def test_keep_columns_default(self):
		'''Check that only the desired columns are remaining after the merge'''

				# Correct columns
		correct_cols = ['col1', 'col2', 'col3', 'geometry']

		apply_merge('all')

		# get the path to put the output
		out_direc = os.getcwd() + "/testing/debug/merge_shapefiles/"
		out_path = out_direc + "merge.shp"

		# Load test and check columns
		test = fm.load_shapefile(out_path)
		assert set(test.columns) == set(correct_cols)

		# remove folder in debug
		shutil.rmtree(out_direc)