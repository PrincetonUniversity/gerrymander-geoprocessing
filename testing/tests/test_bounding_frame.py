'''
Tests for dissolve function
'''
# need to change path to import helper tools in the path
import os, sys
import geopandas as gpd
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.shp_manipulation as sm
import helper_tools.file_management as fm
import shapely as shp
from shapely.geometry import Polygon

def frame(input_path, correct_path):
	''' Input is a 3 x 3 grid. The bounding frame should be created around the
	extents of the input shapefile that is contiguous

	input_path: path to shapefile that we will be created a bounding frame around
	correct_path: path to correct bounding frame shapefile
	'''
	# load in correct bounding frame shapefile
	correct = fm.load_shapefile(correct_path)
	correct = gpd.read_file(correct_path)

	# load testing shapefile and create bounding frame shapefile
	df = fm.load_shapefile(input_path)
	created = sm.generate_bounding_frame(df)

	# Check if polygon created by correct_frame's and created_frame's interior
	# are equal

	# Get polygon created by the frame's interior
	ix = correct.index.values[0]
	correct_frame = correct.at[ix, 'geometry']
	correct_interior = Polygon(correct_frame.interiors[0])

	# Get polygon created by the bounds of the input
	ix = correct.index.values[0]
	created_frame = created.at[ix, 'geometry']
	created_interior = Polygon(created_frame.interiors[0])

	# Check equality between the two interiors
	assert correct_interior.equals(created_interior)

class TestBoundingFrame:
	def test_continguous_input(self):
		'''Bounding frame around contiguous shapefile'''
		# Get correct file paths
		folder = "/testing/test_data/bounding_frame/"
		in_str = "input_bounding_frame_contiguous.shp"
		correct_str = "correct_bounding_frame_contiguous.shp"

		input_path = os.getcwd() + folder + in_str
		correct_path = os.getcwd() + folder + correct_str
			
		frame(input_path, correct_path)

	def test_noncontiguous_input(self):
		'''Bounding frame around noncontiguous shapefile'''

		folder = "/testing/test_data/bounding_frame/"
		in_str = "input_bounding_frame_noncontiguous.shp"
		correct_str = "correct_bounding_frame_noncontiguous.shp"

		input_path = os.getcwd() + folder + in_str
		correct_path = os.getcwd() + folder + correct_str

		frame(input_path, correct_path)


