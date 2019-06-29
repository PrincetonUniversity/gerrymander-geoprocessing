'''
Tests for  merge fully contained
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_manipulation import merge_fully_contained
import helper_tools.file_management as fm

class TestMergeFullyContained:
	def test_regular_contained(self):
		''' Test donut hole type case. Checks correct merge'''
		direc_path = os.getcwd() + '/testing/test_data/merge_fully_contained/'
		file_path = direc_path + '/regular.shp'
		df = fm.load_shapefile(file_path)

		# merge
		df = merge_fully_contained(df)

		assert len(df) == 1

	def test_cols_to_add(self):
		''' Check that columns sum correctly when in cols to add'''
		direc_path = os.getcwd() + '/testing/test_data/merge_fully_contained/'
		file_path = direc_path + '/regular.shp'
		df = fm.load_shapefile(file_path)
		df['value'] = df['value'].astype(float)

		# merge
		df = merge_fully_contained(df, cols_to_add=['value'])

		assert df.at[0, 'value'] == 2

	def test_nested_contained(self):
		''' Test geometry surrounded by other geometries then contained by 
		a larger geometry'''
		direc_path = os.getcwd() + '/testing/test_data/merge_fully_contained/'
		file_path = direc_path + '/nested.shp'
		df = fm.load_shapefile(file_path)

		df = merge_fully_contained(df)

		assert len(df) == 1