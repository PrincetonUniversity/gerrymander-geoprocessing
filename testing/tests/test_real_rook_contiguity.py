'''
Tests for real rook contiguity function
'''

import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_calculations import real_rook_contiguity
import helper_tools.file_management as fm

class TestRealRookContiguity:
	def test_grid_list(self):
		''' Test rook contiguity on a 2x2 grid when function returns a list'''

		# Load shp file
		direc_path = os.getcwd() + '/testing/test_data/real_rook_contiguity/'
		file_path = direc_path + 'grid.shp'
		df = fm.load_shapefile(file_path)

		# perform real rook contiguity
		df = real_rook_contiguity(df)

		print(df)

		# Check bottom left neighbors
		bot_left_neighbors_list = df.at[0, 'neighbors']
		assert 0 not in bot_left_neighbors_list
		assert 1 in bot_left_neighbors_list
		assert 2 in bot_left_neighbors_list
		assert 3 not in bot_left_neighbors_list

		# Check bottom right neighbors
		bot_right_neighbors_list = df.at[1, 'neighbors']
		assert 0 in bot_right_neighbors_list
		assert 1 not in bot_right_neighbors_list
		assert 2 not in bot_right_neighbors_list
		assert 3 in bot_right_neighbors_list

		# Check top left neighbors
		top_left_neighbors_list = df.at[2, 'neighbors']
		assert 0 in top_left_neighbors_list
		assert 1 not in top_left_neighbors_list
		assert 2 not in top_left_neighbors_list
		assert 3 in top_left_neighbors_list

		# Check top right neighbors
		top_right_neighbors_list = df.at[3, 'neighbors']
		assert 0 not in top_right_neighbors_list
		assert 1 in top_right_neighbors_list
		assert 2 in top_right_neighbors_list
		assert 3 not in top_right_neighbors_list

	def test_grid_dict(self):
		''' Test rook contiguity on a 2x2 grid when function returns a dict'''
		
		# Load shp file
		direc_path = os.getcwd() + '/testing/test_data/real_rook_contiguity/'
		file_path = direc_path + 'grid.shp'
		df = fm.load_shapefile(file_path)

		# perform real rook contiguity
		df = real_rook_contiguity(df, struct_type='dict')

		# Check bottom left neighbors
		bot_left_neighbors_list = list(df.at[0, 'neighbors'].keys())
		assert 0 not in bot_left_neighbors_list
		assert 1 in bot_left_neighbors_list
		assert 2 in bot_left_neighbors_list
		assert 3 not in bot_left_neighbors_list

		# Check bottom right neighbors
		bot_right_neighbors_list = list(df.at[1, 'neighbors'].keys())
		assert 0 in bot_right_neighbors_list
		assert 1 not in bot_right_neighbors_list
		assert 2 not in bot_right_neighbors_list
		assert 3 in bot_right_neighbors_list

		# Check top left neighbors
		top_left_neighbors_list = list(df.at[2, 'neighbors'].keys())
		assert 0 in top_left_neighbors_list
		assert 1 not in top_left_neighbors_list
		assert 2 not in top_left_neighbors_list
		assert 3 in top_left_neighbors_list

		# Check top right neighbors
		top_right_neighbors_list = list(df.at[3, 'neighbors'].keys())
		assert 0 not in top_right_neighbors_list
		assert 1 in top_right_neighbors_list
		assert 2 in top_right_neighbors_list
		assert 3 not in top_right_neighbors_list

	def test_small_border(self):
		''' Test rook contiguity on 2x2 grid when there is a small border
		between the top right and bottom left shapes'''
		
				# Load shp file
		direc_path = os.getcwd() + '/testing/test_data/real_rook_contiguity/'
		file_path = direc_path + 'small_border.shp'
		df = fm.load_shapefile(file_path)

		# perform real rook contiguity
		df = real_rook_contiguity(df)

		print(df)

		print(df.at[1, 'geometry'].intersection(df.at[2, 'geometry']))

		# Check bottom left neighbors
		bot_left_neighbors_list = df.at[0, 'neighbors']
		assert 0 not in bot_left_neighbors_list
		assert 1 in bot_left_neighbors_list
		assert 2 in bot_left_neighbors_list
		assert 3 not in bot_left_neighbors_list

		# Check bottom right neighbors
		bot_right_neighbors_list = df.at[1, 'neighbors']
		assert 0 in bot_right_neighbors_list
		assert 1 not in bot_right_neighbors_list
		assert 2 in bot_right_neighbors_list
		assert 3 in bot_right_neighbors_list

		# Check top left neighbors
		top_left_neighbors_list = df.at[2, 'neighbors']
		assert 0 in top_left_neighbors_list
		assert 1 in top_left_neighbors_list
		assert 2 not in top_left_neighbors_list
		assert 3 in top_left_neighbors_list

		# Check top right neighbors
		top_right_neighbors_list = df.at[3, 'neighbors']
		assert 0 not in top_right_neighbors_list
		assert 1 in top_right_neighbors_list
		assert 2 in top_right_neighbors_list
		assert 3 not in top_right_neighbors_list

	# def test_gap(self):
	# 	''' Test contiguity on two shapes that share no border '''
	# 	return







