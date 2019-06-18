'''
Tests for distribute label function
'''

import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from edit_shapefiles import distribute_label
import helper_tools.file_management as fm
import pandas as pd


def check_df(df, col_names, default=False):
	''' Check the correctness of a dataframe given a list of column names 

	We have preset correct values for each column

	We check that it works for string, integer, float, and that the small 
	dataframe keeps existing columns

	Argument:
		df: dataframe to be checked

	Output:
		true or false depending on if values in dataframe beig equal to correct
		values'''

	# define correct values
	correct = {}
	if default:
		correct['large_str'] = pd.Series(['a', 'b'])
		correct['large_int'] = pd.Series([0, 1])
		correct['large_flt'] = pd.Series([0.5, 1.5])
		correct['keep_col'] = pd.Series(['keep', 'keep'])
	else:
		correct['col_str'] = pd.Series(['a', 'b'])
		correct['col_int'] = pd.Series([0, 1])
		correct['col_flt'] = pd.Series([0.5, 1.5])
		correct['keep_col'] = pd.Series(['keep', 'keep'])

	for col in col_names:
		df['test_' + col] = (df[col] == correct[col])
		assert df['test_' + col].all()


def load_dfs(large_name, small_name):
	''' Load in large and small dataframe given the file names in test data 

	Output:
		large and small df'''

	# Load paths
	data_direc = os.getcwd() + "/testing/test_data/distribute_label/"
	large_path = data_direc + large_name
	small_path = data_direc + small_name

	# load and return
	df_large = fm.load_shapefile(large_path)
	df_small = fm.load_shapefile(small_path)

	return df_large, df_small


class TestDistributeLabel:
	def test_attribute_list_size_comparison(self):
		''' Check that False is returned when the size of attribute lists
		are not of the same length'''

		# load
		df_large, df_small = load_dfs('reference.shp', 'within.shp')

		# Get different length column sizes
		large_cols = df_large.columns
		small_cols = ['a']

		df = distribute_label(df_large, large_cols, df_small, small_cols)

		assert df == False

	def test_attribute_subset(self):
		''' Check that False is returned when the an element of large_cols is
		not in the dataframe itself'''

		# load dataframe
		df_large, df_small = load_dfs('reference.shp', 'within.shp')

		# Get same length column sizes
		large_cols = df_large.columns
		large_cols = [x + 'foo' for x in large_cols]

		df = distribute_label(df_large, large_cols, df_small)

		assert df == False

	def test_within(self):
		''' Check label distribution when bounding box intersection is with 
		only one large geometry'''

		df_large, df_small = load_dfs('reference.shp', 'within.shp')
		large_cols = ['large_str']
		small_cols = ['col_str']

		# Apply and test
		df = distribute_label(df_large, large_cols, df_small, small_cols)
		check_df(df, small_cols)

	def test_shared(self):
		''' Check label distribution when bounding box interesects with 
		multiple larger geometries'''
		df_large, df_small = load_dfs('reference.shp', 'shared.shp')
		large_cols = ['large_str']
		small_cols = ['col_str']

		# Apply and test
		df = distribute_label(df_large, large_cols, df_small, small_cols)
		check_df(df, small_cols)


	def test_centroid(self):
		''' Check label distribution when bounding box does not intersect with
		any larger geometry'''
		df_large, df_small = load_dfs('reference.shp', 'centroid.shp')
		large_cols = ['large_str']
		small_cols = ['col_str']

		# Apply and test
		df = distribute_label(df_large, large_cols, df_small, small_cols)
		check_df(df, small_cols)

	def test_default_small_cols(self):
		''' test that the default columns work. This will just use all of the
		large_cols'''
		df_large, df_small = load_dfs('reference.shp', 'within.shp')
		large_cols = ['large_str', 'large_int', 'large_flt']

		# Apply and test
		df = distribute_label(df_large, large_cols, df_small)
		check_df(df, large_cols, True)

	def test_reset_small_cols(self):
		''' test that prior duplicate columns in df_small will be deleted'''

		df_large, df_small = load_dfs('reference.shp', 'reset.shp')
		large_cols = ['large_str', 'large_int', 'large_flt']

		# Apply and test
		df = distribute_label(df_large, large_cols, df_small)
		check_df(df, large_cols, True)

	def test_keep_existing_small_cols(self):
		''' test that columns that already exist in df_small are retained'''
		df_large, df_small = load_dfs('reference.shp', 'keep.shp')
		large_cols = ['large_str']
		small_cols = ['col_str']

		df = distribute_label(df_large, large_cols, df_small, small_cols)
		check_df(df, ['col_str', 'keep_col'])

