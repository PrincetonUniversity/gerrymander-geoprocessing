'''
Tests for compare shapefile diffrence function
'''

import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_calculations import compare_shapefile_difference
import helper_tools.file_management as fm


class TestCompareShapefileDifference:
	def test_geometry_differences(self):
		''' Test when there is no difference, some difference, and all
		all difference between the two geometries.

		The size of shapefiles is set to an area of 1. The some difference will
		have a ratio of 0.5. The all difference will have 1 because of of it 

		'''
		# initialize the correct output
		correct = set([0, 0.25, 1])

		# initialize both sets of paths
		folder = os.getcwd() + "/testing/test_data/compare_shapefile_difference/"

		shp_paths1 = []
		shp_paths1.append(folder + "reference.shp")
		shp_paths1.append(folder + "reference.shp")
		shp_paths1.append(folder + "reference.shp")

		# Get second set of shapefiles
		shp_paths2 = []
		shp_paths2.append(folder + "reference.shp")
		shp_paths2.append(folder + "some_difference.shp")
		shp_paths2.append(folder + "all_difference.shp")

		out = set(compare_shapefile_difference(shp_paths1, shp_paths2, True))

		assert out == correct

	def test_num_paths_difference(self):
		''' Check that false is returned when the paths don't have the same
		length
		'''

		shp_paths1 = []
		shp_paths2 = ['dummy.shp']
		out = compare_shapefile_difference(shp_paths1, shp_paths2)
		assert not out
