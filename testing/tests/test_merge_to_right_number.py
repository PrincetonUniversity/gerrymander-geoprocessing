'''
Tests for merge to right number
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_manipulation import merge_to_right_number
import helper_tools.file_management as fm

def perform_merge(num):
	'''Perform the merge of geometries to "num" geometries remaining'''
	# load
	direc_path = os.getcwd() + '/testing/test_data/merge_to_right_number/'
	file_path = direc_path + 'right_number.shp'
	df = fm.load_shapefile(file_path)

	# merge
	return merge_to_right_number(df, num)

class TestMergeToRightNumber:
	def test_merge_to_one(self):
		'''Merge the geometries to a single geometry'''
		df = perform_merge(1)

		ixs = df.index.to_list()
		ixs.sort()

		assert ixs == [3]

	def test_merge_to_two(self):
		'''Merge the geometries to two geometries'''
		df = perform_merge(2)

		ixs = df.index.to_list()
		ixs.sort()

		assert ixs == [2, 3]

	def test_merge_to_three(self):
		'''Merge the geometries to three geometries'''
		df = perform_merge(3)

		ixs = df.index.to_list()
		ixs.sort()

		assert ixs == [1, 2, 3]

