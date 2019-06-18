'''
Tests for aggregate function
'''

import os, sys
os.chdir('../..')
sys.path.append(os.getcwd())
from edit_shapefiles import aggregate
import helper_tools.file_management as fm
import pandas as pd

def load_dfs(large_name, small_name):
	''' Load in large and small dataframe given the file names in test data 

	Output:
		large and small df'''

	# Load paths
	data_direc = os.getcwd() + "/testing/test_data/aggregate/"
	large_path = data_direc + large_name
	small_path = data_direc + small_name

	# load and return
	df_large = fm.load_shapefile(large_path)
	df_small = fm.load_shapefile(small_path)

	return df_large, df_small

class TestAggregate:
	def test_attribute_list_size_comparison(self):
		''' Check that False is returned when the size of attribute lists
		are not of the same length'''

		# load
		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')

		# Get different length column sizes
		large_cols = list(df_large.columns)
		small_cols = ['a']

		df = aggregate(df_small, small_cols, df_large, large_cols)

		assert df == False

	def test_attribute_subset(self):
		''' Check that False is returned when the an element of small is
		not in the dataframe itself'''

		# load dataframe
		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')

		# Get same length column sizes
		small_cols = list(df_small.columns)
		small_cols = [x + 'foo' for x in small_cols]

		df = aggregate(df_small, small_cols, df_large)

		assert df == False

	def test_aggregegation_type(self):
		''' Check that false is returned when 'fractional' or 'winner take all'
		is not entered into the agg_type argument'''

		# load dataframe
		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')
		small_cols = df_small.columns

		# enter with incorrect aggregation type
		df = aggregate(df_small, small_cols, df_large, agg_type='other')

		assert df == False

	def test_aggregation_attribute(self):
		''' Check that false is returned when aggregating attribute for df_large
		is not actually an attribute of df_large'''

		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')
		small_cols = df_small.columns

		# enter with incorrect aggregation attribute
		df = aggregate(df_small, small_cols, df_large, agg_on='other')

		assert df == False

	def test_centroid(self):
		''' Check when aggregating based on centroid. (i.e. no intersection
			between bounding boxes)'''
	
		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')
		print(df_large)
		small_cols = ['agg_col']

		# get aggregation
		df = aggregate(df_small, small_cols, df_large)

		# Value gets assigned to the proper large geometry (left)
		assert df.at[0, 'agg_col'] == 1
		assert df.at[1, 'agg_col'] == 0

	def test_within(self):
		''' Check aggregation when bounding box intersection is with only one
		large geometry'''

		df_large, df_small = load_dfs('large.shp', 'small_within.shp')
		small_cols = ['agg_col']

		# Apply aggregation

		# Check aggregation performed correctly
		df = aggregate(df_small, small_cols, df_large)

		# Check that the proper aggregation occurred
		assert df.at[0, 'agg_col'] == 2
		assert df.at[1, 'agg_col'] == 1

	def test_multiple_columns(self):
		''' Check aggregation for multiple columns being aggregated'''

		df_large, df_small = load_dfs('large.shp', 'small_within.shp')
		small_cols = ['agg_col', 'other_col']
		print(df_small)

		# Apply aggregation
		df = aggregate(df_small, small_cols, df_large)

		# Check that the proper aggregation occurred
		assert df.at[0, 'agg_col'] == 2
		assert df.at[1, 'agg_col'] == 1
		assert df.at[0, 'other_col'] == 4
		assert df.at[1, 'other_col'] == 3

	def test_delete_old_cols(self):
		''' Check that aggregation function replaces existing columns with the
		same name'''

		df_large, df_small = load_dfs('reset.shp', 'small_centroid.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large)

		# Check that the proper aggregation occurred
		assert df.at[0, 'agg_col'] == 1
		assert df.at[1, 'agg_col'] == 0

	def test_custom_large_cols(self):
		''' Check that the custom naming columns in large_cols list works '''
		df_large, df_small = load_dfs('large.shp', 'small_centroid.shp')
		small_cols = ['agg_col']
		large_cols = ['new_col']
		df = aggregate(df_small, small_cols, df_large, large_cols)

		# Check that the proper aggregation occurred
		assert df.at[0, 'new_col'] == 1
		assert df.at[1, 'new_col'] == 0

	def test_keep_existing_cols(self):
		''' Ensure that aggregation function doesn't delete existing columns in
		large_df'''

		df_large, df_small = load_dfs('keep.shp', 'small_centroid.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large)

		# Check that the proper aggregation occurred
		assert df.at[0, 'keep'] == 'keep'
		assert df.at[1, 'keep'] == 'keep'

	def test_shared_winnner_take_all(self):
		'''Test shared winner take all'''
		df_large, df_small = load_dfs('large.shp', 'small_shared.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large, 
			agg_type='winner take all')

		# Check proper aggregation
		assert df.at[0, 'agg_col'] == 3
		assert df.at[1, 'agg_col'] == 2

	def test_fractional_no_round(self):
		''' Test shared for a fractional aggregation where we do not round'''
		df_large, df_small = load_dfs('large.shp', 'small_shared.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large)

		left = 0.9 + 0.7 + 0.55 + 0.4 + 0.2
		assert round(df.at[0, 'agg_col'], 2) == round(left, 2)
		assert round(df.at[1, 'agg_col'], 2) == round(5 - left, 2)

	def test_fractional_round(self):
		''' Test shared for a fractional aggregation where we round'''
		df_large, df_small = load_dfs('large.shp', 'small_shared.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large, agg_round=True)

		left = 0.9 + 0.7 + 0.55 + 0.4 + 0.2

		assert df.at[0, 'agg_col'] == 3
		assert df.at[1, 'agg_col'] == 2

	def test_fractional_other_aggregation_attribute(self):
		''' Test aggregating on the dummy column 'col_agg_on' rather than area
		'''
		df_large, df_small = load_dfs('large.shp', 'small_shared.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large, agg_on='col_agg_on')

		assert round(df.at[0, 'agg_col'], 2) == round(10 / 3, 2)
		assert round(df.at[1, 'agg_col'], 2) == round(5 / 3, 2)

	def test_leftovers(self): 
		''' Test that the leftover values (i.e. area that does not intersect 
			with any geometry) gets assigned to large geometry with the 
			greatest area'''

		df_large, df_small = load_dfs('large.shp', 'small_leftover.shp')
		small_cols = ['agg_col']
		df = aggregate(df_small, small_cols, df_large)

		assert round(df.at[0, 'agg_col'], 2) == round(5 / 6, 2)
		assert round(df.at[1, 'agg_col'], 2) == round(1 / 6, 2)