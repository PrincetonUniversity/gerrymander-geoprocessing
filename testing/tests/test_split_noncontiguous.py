'''
Tests for split noncontiguous
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_manipulation import split_noncontiguous
import helper_tools.file_management as fm

class TestSplitNoncontiguous:
	def test_two_pieces(self):
		'''Correctly splits a geometry with two noncontiguous pieces'''

		# load
		direc_path = os.getcwd() + '/testing/test_data/split_noncontiguous/'
		file_path = direc_path + '/two_pieces.shp'
		df = fm.load_shapefile(file_path)

		# Split
		df = split_noncontiguous(df)

		# Check
		assert len(df) == 2


	def test_four_pieces(self):
		'''Correctly splits a geometry with four noncontiguous pieces'''

		# load
		direc_path = os.getcwd() + '/testing/test_data/split_noncontiguous/'
		file_path = direc_path + '/four_pieces.shp'
		df = fm.load_shapefile(file_path)

		# Split
		df = split_noncontiguous(df)

		# Check
		assert len(df) == 4

	def test_retain_cols(self):
		'''Retains_cols keeps specified values of columns'''

		# load
		direc_path = os.getcwd() + '/testing/test_data/split_noncontiguous/'
		file_path = direc_path + '/two_pieces.shp'
		df = fm.load_shapefile(file_path)

		# Split
		df = split_noncontiguous(df, ['value1', 'value2'])

		# Check
		assert df.at[0, 'value1'] == '1'
		assert df.at[0, 'value2'] == '2'
		assert df.at[1, 'value1'] == '1'
		assert df.at[1, 'value2'] == '2'