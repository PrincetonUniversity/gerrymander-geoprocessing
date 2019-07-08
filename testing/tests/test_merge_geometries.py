'''
Tests for mege geometries
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_manipulation import merge_geometries
import helper_tools.file_management as fm

def perform_merge(ixs_to_merge, filename, cols_to_add=[]):
	'''Perform the merge of geometries'''
	# load
	direc_path = os.getcwd() + '/testing/test_data/merge_geometries/'
	file_path = direc_path + filename + '.shp'
	df = fm.load_shapefile(file_path)

	# merge
	return merge_geometries(df, ixs_to_merge, cols_to_add)

class TestMergeGeometries:
	def test_merge_small_correct_merge(self):
		'''Check that the small geometry merges to the medium geometry'''

		df = perform_merge([0], 'stack')

		# get index of medium
		medium_ix = df.index[df.name == 'medium'].to_list()[0]

		assert len(df) == 2
		assert df.at[medium_ix, 'geometry'].area == 3

	def test_merge_small_correct_nbrs(self):
		'''Check that the small geometry has the correct neighbors after
		merging'''

		df = perform_merge([0], 'stack')

		# get index of medium and large
		medium_ix = df.index[df.name == 'medium'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert list(df.at[medium_ix, 'neighbors'].keys()) == [large_ix]
		assert list(df.at[large_ix, 'neighbors'].keys()) == [medium_ix]

	def test_merge_small_correct_perims(self):
		'''Check that the small geometry has the correct perimeter value after
		merging'''

		df = perform_merge([0], 'stack')

		# get index of medium and large
		medium_ix = df.index[df.name == 'medium'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert df.at[medium_ix, 'neighbors'][large_ix] == 2
		assert df.at[large_ix, 'neighbors'][medium_ix] == 2 

	def test_merge_small_correct_add_cols(self):
		'''Check that the small geometry has the correct add columns after
		merging'''

		df = perform_merge([0], 'stack', ['add1', 'add2'])

		# get indexof medium and large
		medium_ix = df.index[df.name == 'medium'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert df.at[medium_ix, 'add1'] == 30
		assert df.at[medium_ix, 'add2'] == 300
		assert df.at[large_ix, 'add1'] == 30
		assert df.at[large_ix, 'add2'] == 300

	def test_merge_medium_correct_merge(self):
		'''Check that the medium geometry merges to the medium geometry'''

		df = perform_merge([1], 'stack')

		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert df.at[large_ix, 'geometry'].area == 5

	def test_merge_medium_correct_nbrs(self):
		'''Check that the medium geometry has the correct neighbors after
		merging'''

		df = perform_merge([1], 'stack')

		# get index of small and large
		small_ix = df.index[df.name == 'small'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert list(df.at[small_ix, 'neighbors'].keys()) == [large_ix]
		assert list(df.at[large_ix, 'neighbors'].keys()) == [small_ix]

	def test_merge_medium_correct_perims(self):
		'''Check that the medium geometry has the correct perimeter value after
		merging'''

		df = perform_merge([1], 'stack')

		# get index of small and large
		small_ix = df.index[df.name == 'small'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert df.at[small_ix, 'neighbors'][large_ix] == 1
		assert df.at[large_ix, 'neighbors'][small_ix] == 1 

	def test_merge_medium_correct_add_cols(self):
		'''Check that the medium geometry has the correct add columns after
		merging'''
		
		df = perform_merge([1], 'stack', ['add1', 'add2'])

		# get index of small and large
		small_ix = df.index[df.name == 'small'].to_list()[0]
		large_ix = df.index[df.name == 'large'].to_list()[0]

		assert df.at[small_ix, 'add1'] == 10
		assert df.at[small_ix, 'add2'] == 100
		assert df.at[large_ix, 'add1'] == 50
		assert df.at[large_ix, 'add2'] == 500

	def test_box_correct_merge(self):
		'''Check that the medium geometry merges to the medium geometry'''

		df = perform_merge([1], 'box')

		top_ix = df.index[df.name == 'top'].to_list()[0]

		assert df.at[top_ix, 'geometry'].area == 2.5

	def test_box_correct_nbrs(self):
		'''Check that the medium geometry has the correct neighbors after
		merging'''

		df = perform_merge([1], 'box')

		# get index of small and large
		left_ix = df.index[df.name == 'left'].to_list()[0]
		top_ix = df.index[df.name == 'top'].to_list()[0]

		assert list(df.at[left_ix, 'neighbors'].keys()) == [top_ix]
		assert list(df.at[top_ix, 'neighbors'].keys()) == [left_ix]

	def test_box_correct_perims(self):
		'''Check that the medium geometry has the correct perimeter value after
		merging'''

		df = perform_merge([1], 'box')

		# get index of small and large
		left_ix = df.index[df.name == 'left'].to_list()[0]
		top_ix = df.index[df.name == 'top'].to_list()[0]

		assert df.at[left_ix, 'neighbors'][top_ix] == 1.5
		assert df.at[top_ix, 'neighbors'][left_ix] == 1.5