'''
Tests for image classification
'''
import os, sys
if os.getcwd()[-5:] == 'tests':
	os.chdir('../..')
sys.path.append(os.getcwd())
from create_shapefiles import image_classification
import helper_tools.file_management as fm


def perform():
	'''Perform the classification'''

	# load
	direc = os.getcwd() + '/testing/test_data/image_classification/'
	img = direc  + 'test_img_cropped.jpg'
	shp = direc + 'img_class.shp'

	df, _ = image_classification(shp, img, 4)

	return df

class TestImageClassification:
	def test_region_areas(self):
		# Classify the file

		# There should be two squares on the right hand side both with area
		# 4 and two rectangles on the left hand side with areas 2 and 6
		df = perform()

		areas = [2, 4, 4, 6]

		for ix, row in df.iterrows():
			area =row['geometry'].area
			assert area in areas
			areas.remove(area)