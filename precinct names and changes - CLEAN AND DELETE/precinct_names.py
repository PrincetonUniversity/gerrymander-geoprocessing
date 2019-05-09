# -*- coding: utf-8 -*-
"""
Created on Wed Aug  1 21:47:03 2018

@author: conno
"""
import pandas as pd

def main():
    
    # initialize path to csv 
    csv_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/precinct names and changes/VA_precinct_2018_Changes.csv"

    # initialize list of columns from csv
    name_list = ['Name', 'Path', 'Join Cols', 'Join Delim', 'Split Cols', \
                 'Split Index','Split Delim', 'Remove Substr', 'Output',\
                 'Compare']
    
    list_col = ['Join Cols', 'Split Cols', 'Remove Substr', 'Compare']
                 
    # intialize dictionary that points to dataframe of reduced precinct names
    df_dict = {} 

    csv_df = pd.read_csv(csv_path, header=0, names=name_list, dtype=str)

    # Adjust strings delimited by commas into lists
    for col in list_col:
        csv_df[col] = csv_df[col].str.split(',')
     
    # Clean compare lists
    csv_df = csv_df.fillna(0)

    
    # Initialize Changes Dataframe
# =============================================================================
#     cols = ['Name', 'Error Type', 'Error Local 1', 'Error Local 2',\
#             'Error Num 1', 'Error Num 2', 'Error: First Elec Has Prec', \
#             'Error Second Elec Has Prec']
#     
# =============================================================================
    
    cols = ['Name', 'Error Type', 'Error Local 1', 'Error Local 2',\
        'Error Num 1', 'Error Num 2', 'Error Prec 1 (No Match in Elec 2)',\
        'Error Prec 2 (No Match in Elec 1)']
        
    change_df = pd.DataFrame(columns=cols, dtype=str)
        
    # Create precinct name dataframe and assign to name in dictionary
    for i, _ in csv_df.iterrows():
        df_dict[str(csv_df.at[i, 'Name'])] = create_prec_name_df(
               csv_df.at[i, 'Path'], csv_df.at[i, 'Join Cols'],
               csv_df.at[i, 'Join Delim'], csv_df.at[i, 'Split Cols'],
               csv_df.at[i, 'Split Index'], csv_df.at[i, 'Split Delim'], 
               csv_df.at[i, 'Remove Substr'])
        
        if int(csv_df.at[i, 'Output']):
            csv_out_path = join_list(csv_path.split('.')[:-1], '') + ' ' + \
                            str(csv_df.at[i, 'Name']) + '.csv'
            df_dict[str(csv_df.at[i, 'Name'])].to_csv(csv_out_path)
        
    # Add to error dataframe
    for i, _ in csv_df.iterrows():
        if csv_df.at[i, 'Compare']:
            for compare_name in csv_df.at[i, 'Compare']:
                name1 = str(csv_df.at[i, 'Name'])
                name2 = compare_name
                c_df = prec_matching_error_df(df_dict[name1], df_dict[name2],\
                                              name1, name2)
                change_df = pd.concat([change_df, c_df]).reset_index(drop=True)

    change_df.to_csv("C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/precinct names and changes/Changes_Sequential.csv")
    
def join_list(l, delimiter):
    ''' Takes list and returns a string containing the elements of the list
    delimited by delimiter
    
    Arguments
    l: list of elements to combine into a string
    delimiter'''
    return delimiter.join(map(str, l))

def upper_strip(l):
    ''' Makes every element of a list be in uppercase and strips whitespace
    from the beginning and end of the string. Also removes multiple spaces and
    converts into single space
    
    Argument
    l: list to convert'''
    return [' '.join(str(e).upper().strip().split()) for e in l]

def can_convert_to_int(s):
    ''' Check if the string can be converted to an int. Returns 1 if it can
    and returns 0 if it cannot
    
    Arguments:
        s: string to check if it can be converted to an int'''
        
    try:
        int(s)
        return 1
    except:
        return 0

def get_missing_list_elem(l1, l2):
    ''' determine which elements in two lists are not in the other. Returns a
    list containing two lists. First list is elements in list 1 not contained
    in list 2. Second list is elements in list 2 not contained in list 1
    
    Arguments:
        l1: first list to compare
        l2: second list to compare'''
        
    missing_l1 = list(set(l1) - set(l2))
    missing_l2 = list(set(l2) - set(l1))
    
    # return 0 if both are empty
    if len(missing_l1) == 0 and len(missing_l2) == 0:
        return 0
    
    # if not empty return lists
    return [missing_l1, missing_l2]
    
def prec_matching_error_df(df1, df2, df1_name, df2_name):
    ''' Create a dataframe that contains all of the matching errors between
    two precincts. Contains a column that has the names of both input 
    dataframes. A column to describe the error type, and a column to describe
    the error information for both datframes
    
    Arguments:
        df1: first dataframe to compare. This will have at least the three
        columns Locality, Num Precincts, and Precinct Names
        df2: second ''
        df1_name: gives the name of the first dataframe. Usually the key in 
        the main dictionary
        df2_name: '' second ''
        '''
    
    # create dataframe
    cols = cols = ['Name', 'Error Type', 'Error Local 1', 'Error Local 2',\
        'Error Num 1', 'Error Num 2', 'Error Prec 1 (No Match in Elec 2)',\
        'Error Prec 2 (No Match in Elec 1)']
    error_p1_str = 'Error Prec 1 (No Match in Elec 2)'
    error_p2_str = 'Error Prec 2 (No Match in Elec 1)'
    error_df = pd.DataFrame(columns=cols, dtype=str)
    
    # create string that will gives names of the two years
    name_str = df1_name + ' & ' + df2_name
    
    # Check for locality name errors between the two dataframes
    df1_local = list(df1['Locality'])
    df2_local = list(df2['Locality'])
    loc_err = get_missing_list_elem(df1_local, df2_local)

    # Input the locality error
    if loc_err:
        ix = len(error_df)
        error_df.at[ix, 'Name'] = name_str
        error_df.at[ix, 'Error Type'] = 'Localities Do Not Match'
        error_df.at[ix, 'Error Local 1'] = join_list(loc_err[0], ',')
        error_df.at[ix, 'Error Local 2'] = join_list(loc_err[1], ',')
    
        # set all of the matching localities
        match_loc = set(df1_local) - set(loc_err[0])
        
    # ALl localities match
    else:
        match_loc = df1_local
    # Set locality as index to be able reference in for loop
    df1 = df1.set_index('Locality')
    df2 = df2.set_index('Locality')
    
    for loc in match_loc:

        # Check for number of precincts error
        num1 = df1.at[loc, 'Num Precincts']
        num2 = df2.at[loc, 'Num Precincts']
        
        ix = len(error_df)
        
        if num1 != num2:
            
            error_df.at[ix, 'Name'] = name_str
            error_df.at[ix, 'Error Type'] = loc
            error_df.at[ix, 'Error Num 1'] = str(num1)
            error_df.at[ix, 'Error Num 2'] = str(num2)
        
        # Check for name of precincts error
        df1_prec = df1.at[loc, 'Precinct Name'].split(',')
        df2_prec = df2.at[loc, 'Precinct Name'].split(',')
        prec_err = get_missing_list_elem(df1_prec, df2_prec)
            
        if prec_err:
            
            error_df.at[ix, 'Name'] = name_str
            
            error_df.at[ix, 'Error Type'] = loc
                                                
            error_df.at[ix, error_p1_str] = join_list(prec_err[0], ',')
            error_df.at[ix, error_p2_str] = join_list(prec_err[1], ',')
           
    return error_df
    
def unique_col_combine(df, combine_col_list, delimiter):
    ''' Combine columns in a dataframe into a single string with a delimiter
    
    Arguments
    df: dataframe containing elements we want to combine
    combine_col_list: names of columns in dataframe to combine
    delimeter: method to separate the elements in the columns in the final 
    string'''
    
    # Initialize the list of elements to combine with the first colum and 
    # delete the first column from the list
    combine_list = df[combine_col_list[0]]
    combine_col_list = combine_col_list[1:]
    
    # Iterate through all of the columns that we want to combine to the list
    for col in combine_col_list:
        add_col_list = list(df[col])
        combine_list = [str(m) + delimiter + str(n) for m, n in \
                        zip(combine_list, add_col_list)]
    
    # return unique list
    return list(set(combine_list))

def remove_str_with_substring_from_list(l, substr):
    ''' Returns a list that has removed any element in the input list that
    contains the given substringn
    
    Arguments
    l: list to be reduced
    substr: string that determines whether to remove elements'''
    return [elem for elem in l if substr not in elem]

def generate_df_from_str_list(delimited_list, col_names, delimiter):
    ''' Converts a list that contains delimited strings and converts it into
    a datframe
    
    Arguments
    delimited_list: list containing the delimited string
    col_names: list containing the names of columns
    delimiter: string to separate strings in list'''

    # initialize dataframe
    cols = ['original'] + col_names
    df = pd.DataFrame(columns=cols, dtype=str)
    df['original'] =  delimited_list

    # print errors
    for i in delimited_list:
        if len(i.split(delimiter)) > 3:
            print(i)
    
    # set other columns in dataframe. ALso remove whitespace before and after
    # the delimiter    
    for ix, col in enumerate(col_names):
        df[col] = [i.split(delimiter)[ix].strip() for i in delimited_list] 
        
    # Virginia specific to eliminitate entries for city councils
    drop_rows = []
    for i, _ in df.iterrows():
        if not can_convert_to_int(df.at[i, 'Precinct ID']):
            drop_rows.append(i)
            
    df = df.drop(drop_rows)
        
    return df

def reduce_df(df, col_join, col_split, delim_join, delim_split, remove_substr):
    ''' Takes a dataframe and list of columns from the dataframe to create a 
    unique list of strings formed by concatenting the elements in each of the
    columns row by row through delim_join. This list of unique strings will 
    then be used to create a new dataframe. The new dataframe will have the 
    column original which contains the string from the unique list of strings.
    The new dataframe will also contain the columns in col_split which
    correspond to the unique string being slit by delim_split
    
    df: datframe to be parsed
    col_join: columns to merge unique string
    col_split: columns to form in reduced datframe
    delim_join: delimiter used during joining process
    delim_split: delimiter used during splitting process
    remove_substr: list of substrings that will remove elements in the list
    if a string contains the substring'''

    # Generate a list containing unique names
    unique_list = unique_col_combine(df, col_join, delim_join)
    
    # Remove substrings
    for substr in remove_substr:
        unique_list = remove_str_with_substring_from_list(unique_list, substr)
    
    # Create reduced dataframe
    return generate_df_from_str_list(unique_list, col_split, delim_split)

def reduce_df_by_ix(df, ix_col, all_cols, delimiter):
    ''' Takes a dataframe and reduces to a dataframe with ix_col acting as an
    index. For cols that are in other_col, each row that matches the index
    in the original col will be written as a string split by the delimiter
    
    Arguments
    df: dataframe to be reduced
    ix_col: single column that will act as a pseudo-index
    other_cols: list of columns to create strings in reduced dataframe
    delimiter: how to separate strings in reduced dataframe'''

    # initialize empty data with columns ix_col and other_col
    red_df = pd.DataFrame(columns=all_cols, dtype=str)
    
    # Create a list of unique values from the index col. Make upper case and
    # remove whitespace from beginning and end
    ix_list = list(set(df[ix_col]))
    ix_list = upper_strip(ix_list)
    
    # define other other_cols (not index col)
    other_cols = all_cols
    other_cols.remove(ix_col)
    
    # Iterate through every element in the index list
    for i, ix in enumerate(ix_list):
        # set current index in the reduced dataframe
        red_df.at[i, ix_col] = ix
        
        # make temporary dataframe that only contains current ix
        temp_df = df[df[ix_col] == ix]
        
        # set the other cols
        for col in other_cols:
            
            # get list of alphanumeric elements of the columns that are in the
            # same row as ix
            col_elem_list = upper_strip(list(temp_df[col]))
            
            # Set reduced dataframe to string merged by delimiter
            red_df.at[i, col] = join_list(col_elem_list, delimiter)
            
    return red_df

    
def create_prec_name_df(path, col_join, delim_join, col_split, col_split_ix, \
                        delim_split, remove_substr):
    '''
    Arguments
    path: path to a csv file containing election results
    '''
    
    # read in election results csv
    orig_df = pd.read_csv(path, header=0, dtype=str)
    
    # reduce dataframe to the only necessary columns
    red_df = reduce_df(orig_df, col_join, col_split, delim_join, delim_split,
                       remove_substr)
    

    
    # create precinct dataframe according to ix
    prec_name_df = reduce_df_by_ix(red_df, col_split_ix, col_split, ',')
    
    # get the number of precincts. ??? need to make this easier to get
    # Maybe add variable count columns
    prec_name_df['Num Precincts'] = prec_name_df[col_split[-1]].\
                                    str.split(',').apply(len)
    
    # Get alphabetical order and reset indexes
    prec_name_df = prec_name_df.sort_values(col_split_ix)
    prec_name_df = prec_name_df.reset_index(drop=True)
    
    return prec_name_df

if __name__ == '__main__':
    main()