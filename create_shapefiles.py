import helper_tools.shp_manipulation as sm
import helper_tools.shp_calculations as sc
import helper_tools.file_management as fm

def dissolve_by_attribute(in_path, out_path, dissolve_attribute):
	''' 
	Dissolve boundaries for shapefile(s) according to a given attribute. we will
	also check for contiguity after boundaries have been dissolved.

	Arguments:
		in_path: full path to input shapefile to be dissolved
		out_path: full path to save created shapefile
		disolve_attribute: attribute to dissolve boundaries by
	'''
	#  Generate dissolved shapefile
	geo_df = fm.load_shapefile(in_path)
	geo_df = sm.dissolve(geo_df, dissolve_attribute)

	# Print potential errors
	sc.check_contiguity_and_contained(geo_df, dissolve_attribute)

	# Save shapefile
	fm.save_shapefile(geo_df, out_path)

def create_bounding_frame(in_path, out_path):
''' 
Create a bounding box around the extents of a shapefile. 

This will be used to overlay on top of a georeferenced image in GIS to allow for
automated cropping in the algorithm that converts converting precinct images to 
shapefiles. Will usually use a census block shapfile to generate this bounding
frame

Arguments:
	in_path: full path to input shapefile to create bounding frame for
	out_path: full path to save bounding frame shapefile
'''
	# Generate bounding frame and save
	df = fm.load_shapefile(in_path)
	bounding_frame_df = sm.generate_bounding_frame(df)
	fm.save_shapefile(bounding_frame_df, out_path)