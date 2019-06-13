'''
Tests for remove function
'''

import os, sys
os.chdir('../..')
sys.path.append(os.getcwd())
from edit_shapefiles import remove_geometries
import helper_tools.file_management as fm

def apply_remove_geometries_test(thresh):
	''' Apply remove geometries to test files with the given threshold and
	return the number of geometries remaining. Don't save the file'''

	# Get correct file paths
	data_direc = os.getcwd() + "/testing/test_data/remove_geometries/"
	reference_path = data_direc + 'reference.shp'
	delete_path = data_direc + 'delete.shp'

	# Apply remove geometries
	df_del = remove_geometries(delete_path, False, reference_path, thresh)

	# return number of elements remaining in dataframe after removing geometries
	return len(df_del)


class TestRemoveGeometries:
	def test_remove_all(self):
		''' Use threshold that removes all geometries'''
		assert apply_remove_geometries_test(0.9) == 0

	def test_remove_some(self):
		''' Use threshold that removes two of the four geometries'''
		assert apply_remove_geometries_test(0.7) == 2

	def test_remove_none(self):
		''' Use threshold that removes none of the four geometries'''
		assert apply_remove_geometries_test(0.4) == 4
