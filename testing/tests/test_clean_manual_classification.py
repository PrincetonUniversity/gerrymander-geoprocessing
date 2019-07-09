'''
Tests for clean manual classification
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from create_shapefiles import clean_manual_classification
import helper_tools.file_management as fm

def perform(filename):
	'''Perform the merge of geometries to "num" geometries remaining'''
	# load
	direc_path = os.getcwd() + '/testing/test_data/clean_manual_classification/'
	file_path = direc_path + filename + '.shp'

	# merge
	return clean_manual_classification(file_path, 'class')

class TestCleanManualClassification:
	def test_general_merge(self):
		'''Merge the general file'''
		df = perform('general')

		assert len(df) == 2

		area_one = df.at[0, 'geometry'].area == 2
		area_five = df.at[0, 'geometry'].area == 4
		assert area_one or area_five

		area_one = df.at[1, 'geometry'].area == 2
		area_five = df.at[1, 'geometry'].area == 4
		assert area_one or area_five

	def test_split_noncontiguous(self):
		'''Clean classification when there is a noncontiguous geometry'''
		df = perform('sn')

		assert len(df) == 5

	def test_fully_contained(self):
		'''Clean classification when one is fully contained'''
		df = perform('fc')

		assert len(df) == 1

