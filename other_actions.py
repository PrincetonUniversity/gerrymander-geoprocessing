import shapely as shp
import helper_tools.file_management as fm

def compare_shapefile_difference(shp_paths1, shp_paths2, verbose=False):
	'''
	Compare shapefiles to check how much difference is between them in terms
	of ratio of the first shapefile. 

	A result of 0.90 ratio between the two shapefiles means that 90 percent
	of the first shapefile is NOT contained in the second shapefile. First path 
	in list1 is compared to first list in path 2. Second path in list1 is 
	compared to second path in list 2 and so on

	This is useful for comparing shapefiles received from local jurisdictions.

	Arguments:
		shp_paths1: LIST of paths to shapefiles to be compared 
		shp_paths2:
		verbose: whether to print the difference ratio as they
		are calculated

	Output:
		LIST of ratio of difference as described above for each shp pair.
		Returns false if the length of the lists are not the same
	'''

	# List of difference ratio to the first shapefile
	out = []

	# if list of shapefile lengths are not the same return false
	if len(shp_paths1) != len(shp_paths2):
		return False

	for ix in range(len(shp_paths1)):
		path1 = shp_paths1[ix]
		path2 = shp_paths2[ix]

		# Load in shapefiles
		shp1 = fm.load_shapefile(path1)
		shp2 = fm.load_shapefile(path2)

		# Get full geometries
		poly1 = shp.ops.cascaded_union(list(shp1['geometry']))
		poly2 = shp.ops.cascaded_union(list(shp2['geometry']))

		# calculate, store, and potentially print difference
		diff = poly2.difference(poly1).area
		out.append(diff)
		if verbose:
			name1 = path1.split('/')[-1]
			name2 = path2.split('/')[-1]
			print('Difference Between ' + name1 + ' and' + name2 + 
				': ' + str(out[ix]))

	return out

'''
testing Notes

Create two lists of paths compare path by path
Print out if verbose is on

Check that the ratio is calculated correct
Check when there are a different number of paths it prints that it did Notes
run

Check all difference, no difference, some difference just do 3 asserts in 
one function

Check two lists issue

Need to create a reference.shp, some_diffrence and all_difference shapefile

'''

