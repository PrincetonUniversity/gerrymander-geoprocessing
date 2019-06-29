'''
Tests for shared perimeters function
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from helper_tools.shp_calculations import calculate_shared_perimeters
import helper_tools.file_management as fm

class TestRealRookContiguity:
	def test_grid(self):
		''' Test for 2x2 box grid '''
		# load shp file
		direc_path = os.getcwd() + '/testing/test_data/calculate_shared_perimeters/'
		file_path = direc_path + 'grid.shp'
		df = fm.load_shapefile(file_path)

		# perform calculate shared perimeters
		df = calculate_shared_perimeters(df)

		# Check bottom left neighbors
		bot_left_dict = df.at[0, 'neighbors']
		assert bot_left_dict[1] == 1
		assert bot_left_dict[2] == 1

		# Check bottom right neighbors
		bot_right_dict = df.at[1, 'neighbors']
		assert bot_right_dict[0] == 1
		assert bot_right_dict[3] == 1

		# Check top left neighbors
		top_left_dict = df.at[2, 'neighbors']
		assert top_left_dict[0] == 1
		assert top_left_dict[3] == 1

		# Check top right neighbors
		top_right_dict = df.at[3, 'neighbors']
		assert top_right_dict[1] == 1
		assert top_right_dict[2] == 1

	def test_multiple_boundaries(self):
		''' Test when geometry has intersection in multiple locations'''
		# load shp file
		direc_path = os.getcwd() + '/testing/test_data/calculate_shared_perimeters/'
		file_path = direc_path + 'multiple_intersections.shp'
		df = fm.load_shapefile(file_path)

		# perform calculate shared perimeters
		df = calculate_shared_perimeters(df)

		# Check top piece
		top_dict = df.at[0, 'neighbors']
		assert top_dict[1] == 3
		assert top_dict[2] == 2

		# Check middle piece
		mid_dict = df.at[1, 'neighbors']
		assert mid_dict[0] == 3
		assert mid_dict[2] == 1

		# Check bottom piece
		bot_dict = df.at[2, 'neighbors']
		assert bot_dict[1] == 1
		assert bot_dict[0] == 2