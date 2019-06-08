'''
Tests for noncontigous and contained check
'''
# need to change path to import helper tools in the path
import os, sys
import geopandas as gpd
os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm

def test_noncontiguous():
	''' 3 x 3 grid that surrounds a single element. It should return that a 
	noncontigous element exists'''

	# load in testing shapefile
	folder = "/testing/test_data/noncontiguous_and_contained/"
	input_path = os.getcwd()  + folder + "test_noncontiguous.shp"
	df = fm.load_shapefile(input_path)

	assert len(sc.check_contiguity_and_contained(df, 'attribute')[0])

def test_contained():
	''' 3 x 3 grid that surrounds a single element. It should return that a 
	noncontigous element exists'''

	# load in testing shapefile
	folder = "/testing/test_data/noncontiguous_and_contained/"
	input_path = os.getcwd()  + folder + "test_contained.shp"
	df = fm.load_shapefile(input_path)

	assert len(sc.check_contiguity_and_contained(df, 'attribute')[1])