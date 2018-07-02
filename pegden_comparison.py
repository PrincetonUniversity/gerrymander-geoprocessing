# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 09:38:22 2018

@author: Connor Moffatt
"""

import pandas as pd
import numpy as np


#%%
# cross reference populations and areas to get number of each precinct in 
# Pegden's inputPA.txt for use in GIS to see if there is a method to how he 
# ordered the neighbors 
def getPegdenNumbers():
    numPrecincts = len(pa_df)
    pegdenNumbers = dict()
    pa_pop = np.array(pa_df['POP100']).round()
    peg_pop = np.array(peg_df['pop'])
    
    # get population matches
    pop = np.where(peg_pop == pa_pop[: , np.newaxis])

    for i in range(len(pop[0])):
        j = pop[0][i]
        k = pop[1][i]
        # Get area matches
        if abs(peg_df['area'][k] - pa_df['area'][j]) < 1e-12:
            pegdenNumbers[j] = k
    
    # Return pegden number. If no pegden number exists set to -0.5. Did not
    # want to set to negative integers due to neighbors with negative integers
    # representing the state boundary
    return [pegdenNumbers[i] if i in pegdenNumbers.keys() else -0.5 for i \
            in range(numPrecincts)]
    
#%% Load in Pegden Data
pgp = 'G:/Team Drives/princeton_gerrymandering_project/'
peg_df = pd.read_csv(pgp + 'pegden_algo/InputPA.txt',
                 sep='\t', header=2, names=['src', 'nbr', 'shared_perim', 
                                            'unshared', 'area', 'pop', 
                                            'voteA', 'voteB', 'congD'])

peg_df = peg_df.astype(dtype={'src': str, 'nbr': str})
peg_df['nbr'] = peg_df['nbr'].apply(lambda x: x.split(','))
peg_df['shared_perim'] = peg_df['shared_perim'].apply(lambda x: [float(i) \
      for i in x.split(',')])

#%% Add columns to pa_df to check with Pegden
    
# Load final dataframe
pa_df = pd.read_pickle('./df_final.pkl')
PegNums = getPegdenNumbers()

# Initialize new columns in dataframe. peg_num is the corresponding pegden 
# number, num_nb_correct is a variable dependent on whether our number of
# neighbors matches with pegden's number of neighbors. nb_order correct is 
# a variable dependent on whether our neighbors match with pegden's neighbors
# peg_nb gives pegden's neighbors in his numbers. # peg_nb_geoid gives
# pegden's neighbors in our GEOID10s, and # peg_num_nb gives how many neighbors
# in pegden's text file
new_cols = ['peg_num', 'num_nb_correct', 'nb_order_correct', 'peg_nb',
            'peg_nb_geoid', 'peg_num_nb']
for col in new_cols:
    pa_df[col] = pd.Series(dtype=object)

# Set pegden numbers for each GEOID10
count = 0
for i, _ in pa_df.iterrows():
    pa_df.at[i, 'peg_num'] = PegNums[count]
    count += 1

#%%
# Note, we will let -0.5 be the error value for no match
    
# 0.5 will mean Pegden number that doesn't match one of our values
# -0.5 means one of our values does not match Pegden Number


# Check that the number of neighbors are correct, and whether the order of
# neighbors is correct. 0 means false, 1 means true


count1 = 0
# Itereate through every precinct
for i,_ in pa_df.iterrows():

    # Get our nb list and degree
    our_nb = pa_df.at[i, 'neighbors']
    our_nb_len = len(our_nb)
    
    # Get pegden's neighbor list in pg nums
    peg_ix = pa_df.at[i, 'peg_num']
    
    # If no pegden number exists, set values correctness values to -0.5
    if peg_ix == -0.5:
        pa_df.at[i, 'num_nb_correct'] = -0.5
        pa_df.at[i, 'nb_order_correct'] = -0.5
    else:
        # Get pegden neighbors and degree
        peg_nb = peg_df.at[peg_ix, 'nbr']
        peg_nb = list(map(int, peg_nb))
        peg_nb_len = len(peg_nb)
        
        # convert pegden's neighbor list to our geoID values
        peg_nb_geoid = []
        for j in peg_nb:
            # Append State boundary
            if j < 0:
                peg_nb_geoid.append(j)
            else:
                # Append GEOID10 if one exists
                df_row = pa_df[pa_df['peg_num']==j]
                if len(df_row) == 1:
                    peg_nb_geoid.append(df_row.index[0])
                # If no match exists append 0.5
                elif len(df_row) == 0:
                    peg_nb_geoid.append(0.5)
                else:
                    print('Multiple Match Error')
                    print(j)
                    print(i)
           
        # Set values of Pegden neigbhors into the df
        pa_df.at[i, 'peg_nb'] = peg_nb
        pa_df.at[i, 'peg_nb_geoid'] = peg_nb_geoid
        pa_df.at[i, 'peg_num_nb'] = peg_nb_len
        
        # Check that number of neighbors is the same and set value 
        # num_nb_correct
        if peg_nb_len == our_nb_len:
            pa_df.at[i, 'num_nb_correct'] = 1
            our_nb_copy = our_nb
            peg_nb_geoid_copy = peg_nb_geoid
            
            # Get rid of the negative index mismatch problem
            for l in range(our_nb_len):
                # only boundaries are integers
                if peg_nb[l] < 0:
                    peg_nb_geoid_copy[l] = 0

                if isinstance(our_nb_copy[l], int):
                    our_nb_copy[l] = 0
                    
            # Check if lists are equal for any rotation of our_nb
            for k in range(our_nb_len):
                if our_nb_copy == peg_nb_geoid_copy:
                    correct_order = 1
                    break
                else:
                    our_nb_copy = our_nb_copy[1:] + our_nb_copy[:1]
                
            # Set values
            if correct_order:
                pa_df.at[i, 'nb_order_correct'] = 1
            else:
                pa_df.at[i, 'nb_order_correct'] = 0
            
        else:
            pa_df.at[i, 'num_nb_correct'] = 0
            
            # neighbor order cannot be the same
            pa_df.at[i, 'nb_order_correct'] = 0
        
pa_df.to_pickle('./after_pegden')
        
    
#%%

# print out different discrepancy types to csv

# Number of Neighbors Discrepancy
pa_num_nb = pa_df[pa_df['num_nb_correct']==0]
pa_num_nb.to_csv('Discrepancy_Num_Neighbors.csv')

# Order of Neighbors Discrepancy
pa_order_nb = pa_df[pa_df['nb_order_correct']==0]
pa_order_nb.to_csv('Discrepancy_Order_Neighbors.csv')

# No Match Discrepancy
pa_match = pa_df[pa_df['peg_num']==-0.5]
pa_match.to_csv('Discrepancy_Match.csv')
    