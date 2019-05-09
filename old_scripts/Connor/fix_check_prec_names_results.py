import numpy as np
from scipy.optimize import linear_sum_assignment
import geopandas as gpd
import helper_tools as ht
from fuzzywuzzy import fuzz

check_names_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/MI/CSV/MISC/received_check_prec_names_MI_10_20.csv"
check_names_result_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/MI/CSV/MISC/received_check_prec_names_MI_10_20 RESULTS.csv"

## Import the received_check_prec_names csv
direc_path = ht.read_one_csv_elem(check_names_path)
csv_col = ['Locality', 'CensusPath', 'Filename', 'InputCol', 'ElectionPrecincts']
check_names_df = ht.read_csv_to_df(check_names_path, 1, csv_col, [])

## Import the received_check_prec_names RESULTS csv
csv_col = ['Result', 'Locality', 'Match', 'SHP_no_match', 'NumSHP', 'Input_no_match', 'NumInput']
check_names_result_df = ht.read_csv_to_df(check_names_result_path, 0, csv_col, [])

## Match names between the election data and shapefile data
def get_matching_names(a, b):

    # Matching based on https://github.com/seatgeek/fuzzywuzzy
    a = a.split(",")
    b = b.split(",")

    # Create the cost matrix with fuzzy matching
    match_mat = np.zeros((len(a), len(b)))
    for i in range(len(a)):
        for j in range(len(b)):
            match_mat[i,j] = 100 - fuzz.token_set_ratio(a[i], b[j])

    # Choose the optimal assignment
    row_idx, col_idx = linear_sum_assignment(match_mat)

    # Make assignments to return
    matched_names = dict()
    for i, x in enumerate(a):
        matched_names[x] = b[col_idx[i]]

    return matched_names

## Iterate through results and attempt to fix errors
for (i, check_row), (j, result_row) in zip(check_names_df.iterrows(), check_names_result_df.iterrows()):

    # Log progress
    print("----------", check_row.Locality, "----------")
    if result_row.NumSHP != result_row.NumInput:
        print("ERROR: shapefile has", result_row.NumSHP, "precincts, election data has", result_row.NumInput, "precincts!")
        print("Status: 11")
        continue

    # Attempt matching if necessary
    if not result_row.Match:

        # Create a matching from Input_no_match to SHP_no_match
        # returns dict indexed by shapefile precinct name
        matches = get_matching_names(result_row.SHP_no_match, result_row.Input_no_match)

        # Load and update the shapefile
        if len(matches) > 0:
            try:
                shape_path = direc_path + check_row.Locality + "/" + check_row.Filename
                shape_file = gpd.read_file(shape_path)

                # Update the shapefile values
                for j, value in enumerate(shape_file[check_row.InputCol]):
                    if value.upper() in matches:
                        shape_file.at[j, check_row.InputCol] = matches[value.upper()]

                shape_file.to_file(shape_path)
            except:
                print("ERROR: Matching:", check_row.Locality, "shapefile does not exist")

        # Report results of matching
        if len(matches) < result_row.NumSHP:
            print("Matching: (10) Partially Completed")
            print("Status: 10")
            continue
        else:
            print("Matching: (2) Completed")
    else:
        print("Matching: (2) Completed")


    # Reload shapefiles and check correctness
    try:
        shape_path = direc_path + check_row.Locality + "/" + check_row.Filename
        shape_file = gpd.read_file(shape_path)

        # Compare precinct names in check_names_df and from shapefile
        shp_set = set([str(e).upper() for e in list(shape_file[check_row.InputCol])])
        input_set = set([str(e).upper() for e in check_row.ElectionPrecincts.split(',')])

        if len(list(shp_set - input_set)) == 0 and len(list(input_set - shp_set)) == 0:
            print("Checking: Completed")
            print("Status: 1")
        else:
            print("Checking: Failed")
            print("Status: 2")
    except:
        print("ERROR: Checking:", check_row.Locality, "shapefile does not exist")
