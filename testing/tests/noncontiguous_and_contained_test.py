'''
Tests for noncontigous and contained check
'''
# need to change path to import helper tools in the path
import os, sys
import geopandas as gpd
os.chdir('../..')
sys.path.append(os.getcwd())
import helper_tools.shp_calculations as sc

def noncontiguous_test():
	''' 3 x 3 grid that surrounds a single element. It should return that a 
	noncontigous element exists'''

	# load in testing shapefile
	input_path = os.getcwd()  + "/testing/test_data/test_noncontiguous.shp"
	df = gpd.read_file(input_path)

	if len(sc.check_contiguity_and_contained(df, 'attribute')[0]) == 0:
		return False
	return True

def contained_test():
	''' 3 x 3 grid that surrounds a single element. It should return that a 
	noncontigous element exists'''

	# load in testing shapefile
	input_path = os.getcwd()  + "/testing/test_data/test_contained.shp"
	df = gpd.read_file(input_path)

	if len(sc.check_contiguity_and_contained(df, 'attribute')[1]) == 0:
		return False
	return True

noncontiguous = noncontiguous_test()
contained = contained_test()

print('\n-------------------------------------\n')
if noncontiguous == True:
	print('Simple dissolve test PASSED')
else:
	print('Simple dissolve test FAILED')

if contained == True:
	print('Simple dissolve test PASSED')
else:
	print('Simple dissolve test FAILED')