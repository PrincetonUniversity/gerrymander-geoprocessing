import pandas as pd
import numpy as np
# Define path to CSV

# initialize path to load csv 
csv_path = "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/precinct names and changes/precinct_changes_between_election_test2.csv"

# initizize path to save csv
out_path =  "C:/Users/conno/Documents/GitHub/Princeton-Gerrymandering/gerrymander-geoprocessing/precinct names and changes/precinct_changes_between_election_result.csv"

# initialize list of columns from csv
name_list = ['Name', 'Path', 'Locality', 'Precinct', 'Compare']
csv_df = pd.read_csv(csv_path, header=0, names=name_list, dtype=str)


# Change comma delimited strings into list
csv_df['Compare'] = csv_df['Compare'].str.split(',')
csv_df = csv_df.fillna(0)

# Add precinct change dataframe
cols = ['Name', 'Error Type', 'Error Local 1', 'Error Local 2',\
        'Error Num 1', 'Error Num 2', 'Error Prec 1 (No Match in Elec 2)',\
        'Error Prec 2 (No Match in Elec 1)']

cols = ['A', 'B', 'Locality', '# A', '# B', 'Only in A', 'Only in B']

change_df = pd.DataFrame(columns=cols, dtype=str)

# Load in all results dataframes
dict_df = {}
for ix, row in csv_df.iterrows():
    df = pd.read_csv(row.Path)
    
    # Drop duplicates and clean strings
    df = df.loc[:, [row.Locality, row.Precinct]].drop_duplicates()
    df[row.Precinct] = df[row.Precinct].str.strip()
    df[row.Locality] = df[row.Locality].str.strip()
    
    # Add to dictionary of data frame series
    dict_df[row.Name] = df.groupby(row.Locality)[row.Precinct].apply(list)
    
# Compare between dataframes
for ix, row in csv_df.iterrows():
    # Set name for results "A"
    A = row.Name
    
    # Check if there is anything
    # Loop through results "B" to compare to
    if row.Compare != 0:
        for B in row.Compare:
            
            # First check for differences in localities 
            A_localities = set(dict_df[A].index)
            B_localities = set(dict_df[B].index)
            A_not_B = A_localities - B_localities
            B_not_A = B_localities - A_localities
            A_and_B = A_localities.intersection(B_localities)
            
            # Save discrepancies if they exists        
            if len(A_not_B) > 0:
                error_str = 'Discrepancy! Localities in A but Not B: ' + \
                ', '.join(A_not_B)
                
                r =  len(change_df)
                change_df.at[r, 'A'] = A
                change_df.at[r, 'B'] = B
                change_df.at[r, 'Locality'] = error_str
                
            if len(B_not_A) > 0:
                error_str = 'Discrepancy! Localities in B but Not A: ' + \
                ', '.join(B_not_A)
                
                r =  len(change_df)
                change_df.at[r, 'A'] = A
                change_df.at[r, 'B'] = B
                change_df.at[r, 'Locality'] = error_str
            
            # Now check for precinct changes within localities that are in both
            for locality in A_and_B:
                
                # First check for differences in localities 
                A_precincts = set(dict_df[A][locality])
                B_precincts = set(dict_df[B][locality])
                A_not_B = A_precincts - B_precincts
                B_not_A = B_precincts - A_precincts
                
                # Save discrepancies if they exists        
                if len(A_not_B) + len(B_not_A) > 0:
                    r =  len(change_df)
                    change_df.at[r, 'A'] = A
                    change_df.at[r, 'B'] = B
                    change_df.at[r, 'Locality'] = locality
                    change_df.at[r, '# A'] = len(A_precincts)
                    change_df.at[r, '# B'] = len(B_precincts)
                    change_df.at[r, 'Only in A'] = ', '.join(A_not_B)
                    change_df.at[r, 'Only in B'] = ', '.join(B_not_A)
                      
change_df.to_csv(out_path, index=False)