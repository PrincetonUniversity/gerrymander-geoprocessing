import pandas as pd
import geopandas as gpd
import operator
import os
import csv
from titlecase import titlecase

# Transfer an attribute column to another shapefile using areal interpolation.
# This can also be used to change the formatting of another 

def main():
    # Get path to our CSV file
    csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Areal Interpolate CSV/Interpolate_Portsmouth_Aug18.csv"
    
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        # Import Google Drive path
        with open(csv_path) as f:
            reader = csv.reader(f)
            data = [r for r in reader]
        direc_path = data[0][1]

        # Import table from CSV into pandas dataframe
        csv_df_names = ['locality', 'to_df path', 'to_df cols', 'format', \
                        'from_df path', 'from_df cols']
        csv_df = pd.read_csv(csv_path, header=1, names=csv_df_names)
        
        # Adjust strings delimited by commas into lists
        list_col = ['to_df cols', 'from_df cols', 'format']
        for col in list_col:
            csv_df[col] = csv_df[col].str.split(',')

        # Iterate through all of the interpolations
        for i, _ in csv_df.iterrows():
            
            local = csv_df.at[i, 'locality']
            print('\n' + local)
            try: 
                
                # Set adjust cols
                adjust_cols = []
                from_cols = csv_df.at[i, 'from_df cols']
                to_cols = csv_df.at[i, 'to_df cols']
                format_cols =  csv_df.at[i, 'format']
                
                if len(from_cols) != len(to_cols):
                    raise Exception('# of from and to cols are unequal')
            
                for ix, elem in enumerate(to_cols):
                    adjust_cols.append((elem, from_cols[ix], format_cols[ix]))
                    
                # set to path
                to_path = csv_df.at[i, 'to_df path']
                
                if to_path == 'census_block':
                    filename = local + '_census_block.shp'
                    filename = filename.replace(' ', '_')
                    to_path = direc_path + '/' + local + '/' + filename
                                    
                if to_path == 'precinct':
                    filename = local + '_precincts.shp'
                    to_path = direc_path + '/' + local + '/' + filename
                    
                if to_path == 'precinct_final':
                    filename = local + '_precincts_final.shp'
                    filename = filename.replace(' ', '_')
                    to_path = direc_path + '/' + local + '/' + filename
                
                # set from path
                from_path = csv_df.at[i, 'from_df path']
                
                if from_path == 'census_block':
                    filename = local + '_census_block.shp'
                    filename = filename.replace(' ', '_')
                    from_path = direc_path + '/' + local + '/' + filename
                                    
                if from_path == 'precinct':
                    filename = local + '_precincts.shp'
                    from_path = direc_path + '/' + local + '/' + filename
                    
                if from_path == 'precinct_final':
                    filename = local + '_precincts_final.shp'
                    filename = filename.replace(' ', '_')
                    from_path = direc_path + '/' + local + '/' + filename
                    
                # Delete CPG files. Throws incorrect encoding error due to 
                # ArcGIS incorrectly writing the encoding type
                cpg_path_to = ''.join(to_path.split('.')[:-1]) + '.cpg'
                if os.path.exists(cpg_path_to):
                    os.remove(cpg_path_to)
                    
                cpg_path_from = ''.join(from_path.split('.')[:-1]) + '.cpg'
                if os.path.exists(cpg_path_from):
                    os.remove(cpg_path_from)

                # run majority areal interpolation
                new_df_to = majority_areal_interpolation(to_path, from_path, \
                                                          adjust_cols)
                
                # Change to correct datatypes if numbers
                for col in new_df_to.columns:
                    new_df_to[col] = pd.to_numeric(new_df_to[col], \
                                                      errors='ignore')
                # save new "to" dataframe
                new_df_to.to_file(to_path)
                
            except Exception as e:
                print('exception')
                print(e)

    # CSV file could not be read in or exported
    except:
        print('ERROR: Reading in CSV file')
        
def majority_areal_interpolation(to_df_path, from_df_path, adjust_cols):
    ''' Perform majority area areal interpolation on two dataframes. Returns
    the modified dataframe (to_df)
    
    Arguments:
        to_df_path: path to the shapefile containing the dataframe to be 
        modified
        from_df_path: path to the shapefile used to modify to_df
        adjust_cols: list of tuples that determine which df_to columns are
        set equal to which df_from cols. Format column is string manipulation
        to apply such as upper/lower/title case [(df_to_col1, df_from_col1, 
        format_col1), (df_to_col2, df_from_col2, format_col2),...]'''

    # Read in input dataframe
    df_from = gpd.read_file(from_df_path)
    df_from.index = df_from.index.astype(int)

    # Read in output dataframe
    df_to = gpd.read_file(to_df_path)
    
    # Need to define which columns in the to dataframe to drop. We will drop
    # all columns from the csv that actually exist in the to dataframe. We
    # will also drop columns in the to_
    drop_cols_before = []
    drop_cols_after = []
    for tup in adjust_cols:
        # add to before drop
        if tup[0] in df_to.columns:
            drop_cols_before.append(tup[0])
            
        # add to after drop
        if tup[1] not in df_from.columns:
            print('Column not in from df: ' + tup[1])
            drop_cols_after.append(tup[0])
            
    # Drop columns that are already in df_to
    df_to = df_to.drop(columns=drop_cols_before)

    # Create all output columns in the to_df
    for tup in adjust_cols:
        df_to[tup[0]] = pd.Series(dtype=object)

    # construct r-tree spatial index. Creates minimum bounding rectangle about
    # each geometry in df_from
    si = df_from.sindex

    # get centroid for al elements in df_from to take care of no intersection
    # cases
    df_from['centroid'] = pd.Series(dtype=object) 
    for j, _ in df_from.iterrows():
        df_from.at[j, 'centroid'] = df_from.at[j, 'geometry'].centroid

    # iterate through every geometry in the to_df to match with from_df and set
    # target values
    for i, _ in df_to.iterrows():
    
        # initialize current element's geometry and check which for minimum
        # bounding rectangle intersections
        df_to_elem_geom = df_to.at[i, 'geometry']
        poss_df_from_elem = [df_from.index[i] for i in \
                      list(si.intersection(df_to_elem_geom.bounds))]

        # If precinct's MBR only from_df geometry. Set it equal
        if len(poss_df_from_elem) == 1:
            df_from_elem = poss_df_from_elem[0]
        else:
            # for cases with multiple matches, compare fractional area
            frac_area = {}
            found_majority = False
            for j in poss_df_from_elem:
                if not found_majority:
                    area = df_from.at[j, 'geometry'].intersection(\
                                   df_to_elem_geom).area / \
                                   df_to_elem_geom.area
                    # Majority area means, we can assign
                    if area > .5:
                        found_majority = True
                    frac_area[j] = area

            # if there was intersection get max of frac area
            if len(frac_area) > 0:
                df_from_elem = max(frac_area.items(), \
                                 key=operator.itemgetter(1))[0]
            # No intersection so found nearest centroid
            else:
                # get centroid on the current geometry
                c = df_to.at[i, 'geometry'].centroid
                min_dist = -1
                
                # find the minimum distance index
                for j, _ in df_from.iterrows():
                    cur_dist = c.distance(df_from.at[j, 'centroid'])
                    if min_dist == -1 or cur_dist < min_dist:
                        df_from_elem = j
                        min_dist = cur_dist

        # Set corresponding df_to values to df_from values if the column exist
        # in from_df     
        df_from_cols = df_from.columns
        for tup in adjust_cols:
            # Interpolate
            if tup[1] in df_from_cols:
                input_str = df_from.at[df_from_elem, tup[1]]

                # Set formatting from input
                if tup[2] == 'U':
                    input_str = input_str.upper()
                elif tup[2] == 'L':
                    input_str = input_str.lower()
                elif tup[2] == 'T':
                    input_str = titlecase(input_str)

                df_to.at[i, tup[0]] = input_str

    # Delete and print columns that are missing in from dataframe
    df_to = df_to.drop(columns=drop_cols_after)

    # Return output dataframe
    return df_to

if __name__ == '__main__':
    main()