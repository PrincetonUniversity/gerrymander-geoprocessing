'''
Tests for dissolve function
'''
# need to change path to import helper tools in the path
import os, sys
import geopandas as gpd
os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.shp_manipulation as sm

def simple_grid_test():
	''' 3 x 3 grid that should dissolve into three columns. Check if dissolve
	function is working properly for this small example '''

	# load in correctly dissolved shapefile
	correct_path = os.getcwd()  + "/testing/test_data/dissolved_simple_correct.shp"
	correct =  gpd.read_file(correct_path)

	# load in initial data and apply dissolve function
	input_path = os.getcwd() + "/testing/test_data/test_dissolve_simple.shp"
	test = sm.dissolve(input_path, 'attribute')

	# Number of matches
	matches = 0

	# Check if we have three matches (double for loop is fine because n=3)
	for ix1, row1 in correct.iterrows():
		for ix2, row2 in test.iterrows():
			# Check if the geometries are equal
			if row1['geometry'].equals(row2['geometry']):
				matches += 1

	# Return true if each geometry matches
	if matches == 3:
		return True
	return False

if simple_grid_test() == True:
	print('Simple dissolve test PASSED')
else:
	print('Simple dissolve test FAILED')