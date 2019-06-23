'''
Tests for distribute_values function
'''

import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from edit_shapefiles import distribute_values
import helper_tools.file_management as fm
import pandas as pd

def load_dfs(target_name, source_name):
	''' Load in target and source dataframe given the file names in test data 

	Output:
		target and source df'''

	# Load paths
	data_direc = os.getcwd() + "/testing/test_data/distribute_values/"
	target_path = data_direc + target_name
	source_path = data_direc + source_name

	# load and return
	df_target = fm.load_shapefile(target_path)
	df_source = fm.load_shapefile(source_path)

	return df_target, df_source

class TestAggregate:

	def test_attribute_list_size_comparison(self):
		''' Check that False is returned when the size of attribute lists
		are not of the same length'''

		# load
		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')

		# Get different length column sizes
		target_cols = list(df_target.columns)
		source_cols = ['a']

		df = distribute_values(df_source, source_cols, df_target, target_cols)

		assert df == False

	def test_attribute_subset(self):
		''' Check that False is returned when the an element of source is
		not in the dataframe itself'''

		# load dataframe
		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')

		# Get same length column sizes
		source_cols = list(df_source.columns)
		source_cols = [x + 'foo' for x in source_cols]

		df = distribute_values(df_source, source_cols, df_target)

		assert df == False

	def test_aggregegation_type(self):
		''' Check that false is returned when 'fractional' or 'winner take all'
		is not entered into the distribute_type argument'''

		# load dataframe
		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')
		source_cols = df_source.columns

		# enter with incorrect aggregation type
		df = distribute_values(df_source, source_cols, df_target, distribute_type='other')

		assert df == False

	def test_aggregation_attribute(self):
		''' Check that false is returned when aggregating attribute for df_target
		is not actually an attribute of df_target'''

		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')
		source_cols = df_source.columns

		# enter with incorrect aggregation attribute
		df = distribute_values(df_source, source_cols, df_target, 
			distribute_on='other')

		assert df == False

	def test_centroid(self):
		''' Check when aggregating based on centroid. (i.e. no intersection)'''
	
		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')
		source_cols = ['dist_col']

		# get aggregation
		df = distribute_values(df_source, source_cols, df_target)

		# Value gets assigned to the proper target geometry (left)
		assert df.at[0, 'dist_col'] == 1
		assert df.at[1, 'dist_col'] == 0

	def test_within_distribute_values(self):
		''' Check aggregation intersection is with only one target geometry'''

		df_target, df_source = load_dfs('target.shp', 'source_within.shp')
		source_cols = ['dist_col']

		# Apply aggregation
		df = distribute_values(df_source, source_cols, df_target)

		# Check that the proper aggregation occurred
		assert df.at[0, 'dist_col'] == 2
		assert df.at[1, 'dist_col'] == 1

	def test_multiple_columns(self):
		''' Check aggregation for multiple columns being aggregated'''

		df_target, df_source = load_dfs('target.shp', 'source_within.shp')
		source_cols = ['dist_col', 'other_col']

		# Apply aggregation
		df = distribute_values(df_source, source_cols, df_target)

		# Check that the proper aggregation occurred
		assert df.at[0, 'dist_col'] == 2
		assert df.at[1, 'dist_col'] == 1
		assert df.at[0, 'other_col'] == 4
		assert df.at[1, 'other_col'] == 3

	def test_delete_old_cols(self):
		''' Check that aggregation function replaces existing columns with the
		same name'''

		df_target, df_source = load_dfs('reset.shp', 'source_centroid.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target)

		# Check that the proper aggregation occurred
		assert df.at[0, 'dist_col'] == 1
		assert df.at[1, 'dist_col'] == 0

	def test_custom_target_cols(self):
		''' Check that the custom naming columns in target_cols list works '''
		df_target, df_source = load_dfs('target.shp', 'source_centroid.shp')
		source_cols = ['dist_col']
		target_cols = ['new_col']
		df = distribute_values(df_source, source_cols, df_target, target_cols)

		# Check that the proper aggregation occurred
		assert df.at[0, 'new_col'] == 1
		assert df.at[1, 'new_col'] == 0

	def test_keep_existing_cols(self):
		''' Ensure that aggregation function doesn't delete existing columns in
		target_df'''

		df_target, df_source = load_dfs('keep.shp', 'source_centroid.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target)

		# Check that the proper aggregation occurred
		assert df.at[0, 'keep'] == 'keep'
		assert df.at[1, 'keep'] == 'keep'

	def test_shared_winnner_take_all(self):
		'''Test shared winner take all'''
		df_target, df_source = load_dfs('target.shp', 'source_shared.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target, 
			distribute_type='winner take all')

		# Check proper aggregation
		assert df.at[0, 'dist_col'] == 3
		assert df.at[1, 'dist_col'] == 2

	def test_fractional_no_round(self):
		''' Test shared for a fractional aggregation where we do not round'''
		df_target, df_source = load_dfs('target.shp', 'source_shared.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target)

		left = 0.9 + 0.7 + 0.55 + 0.4 + 0.2
		assert round(df.at[0, 'dist_col'], 2) == round(left, 2)
		assert round(df.at[1, 'dist_col'], 2) == round(5 - left, 2)

	def test_fractional_round(self):
		''' Test shared for a fractional aggregation where we round'''
		df_target, df_source = load_dfs('target.shp', 'source_shared.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target, 
			distribute_round=True)

		left = 0.9 + 0.7 + 0.55 + 0.4 + 0.2

		assert df.at[0, 'dist_col'] == 3
		assert df.at[1, 'dist_col'] == 2

	def test_fractional_other_aggregation_attribute(self):
		''' Test aggregating on the dummy column 'col_dist_on' rather than area
		'''
		df_target, df_source = load_dfs('target.shp', 'source_shared.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target, 
			distribute_on='dist_on')

		assert round(df.at[0, 'dist_col'], 2) == round(10 / 3, 2)
		assert round(df.at[1, 'dist_col'], 2) == round(5 / 3, 2)

	def test_leftovers(self): 
		''' Test that the leftover values (i.e. area that does not intersect 
			with any geometry) gets assigned to target geometry with the 
			greatest area'''

		df_target, df_source = load_dfs('target.shp', 'source_leftover.shp')
		source_cols = ['dist_col']
		df = distribute_values(df_source, source_cols, df_target)

		assert round(df.at[0, 'dist_col'], 2) == round(5 / 6, 2)
		assert round(df.at[1, 'dist_col'], 2) == round(1 / 6, 2)