import time
import pandas as pd
import math
import censusbatchgeocoder
import warnings
import os
warnings.filterwarnings("ignore")

n = 2

# name of path to save census geocoded results to
out_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/PA/Voter Roll/missed_" + str(n) + "_census_geocode.csv"

# Initialize temporary csv name to feed into csv geocoder
temp_name = './dummy.csv'

# import original CSV voter file as DataFrame
raw_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/PA/Voter Roll/missed_" + str(n) + ".csv"
raw_cols = ['id', 'city', 'state', 'zipcode', 'precinct', 'address']
df_raw = pd.read_csv(raw_path, names=raw_cols, header=0)
df_raw = df_raw.set_index('id')
df_raw['address'] = df_raw['address'].str.strip()

# Define how large and how many batches to use. Max batch size allowed for the
# census is 1000. However, there will sometimes be a timeout request. In this
# case the following code will subdivide the batch until the addresses are
# successfully returned
batch_size = 1000
batches = math.ceil(len(df_raw) / batch_size)

# List of row indexes that cannot be ran through census geocoder
missed_ix = []

# initialize geocoded dataframe
df_geo =  pd.DataFrame()
df_remaining = pd.DataFrame()

# Get start time. And initialize last_save time. Don't actually save here
start = time.time()
last_save = start

# Number of seconds between saving the census geocode and remaining
save_gap = 60

# Let missed path and remain path be 
missed_path = '.'.join(out_path.split('.')[:-1]) + '_missed.csv'
remain_path = '.'.join(out_path.split('.')[:-1]) + '_remain.csv'

def tryBatch(batch_start, batch_end, missed_ix, df_raw, df_geo, temp_csv_name): 
    ''' Executes a batch of addresses through the census geocoder. Dataframe
    containing column raw data must have the correct column names: 'id',
    'city', 'state', 'zipcode', 'precinct', 'address'. 
    
    Arguments:
        batch_start: first numerical index of the raw dataframe to add to 
                    the batch
        batch_end: last numerical index of the raw dataframe to add to the
                    batch
        missed_ix: list of indexes of rows that have been missed for a 
                    given input csv. Must be returned.        
        df_raw: input raw dataframe containing information in description above
        df_geo: geocoded results dataframe. Must be returned
        temp_csv_name: temporary file name to save name './dummy.csv'
        
    Output:
        A list containing two arguments. The first argument is the updated
        census geocode dataframe, and the second argument is the list of 
        single indexes that are unable to be ran
    '''
    
    print('Current batch indexes: ' + str(batch_start) + ' to ' + 
          str(batch_end))
    
    # If the batch size is smaller than tw simply add it to the missed
    # dataframe in case that specific address is causing the timeout errors            
    if batch_end - batch_start < 2:
        missed_ix.append(batch_start)
        df_missed = pd.DataFrame()
        # Iterate through all the individual indresses missed and append to the
        # missed dataframe. 
        for m in missed_ix:
            df_missed = df_missed.append(df_raw.iloc[m][:])
        
        # Save to missed_path
        df_missed.to_csv(missed_path)
        
        # return missed index and census geocode dataframe
        return [df_geo, missed_ix]

    # run batch through census api
    else:
        try:
            # Initialize the batch dataframe
            batch_df = df_raw.iloc[batch_start:batch_end][:]

            # create temp csv to load batches into the census API wrapper
            batch_df.to_csv(temp_csv_name)
    
            # Put batch through census API
            result_dict = censusbatchgeocoder.geocode(temp_csv_name)
            result_df = pd.DataFrame.from_dict(result_dict)
        
            # Print time for batch 
            print('Batch Time: ' + str(time.time() - batch_time))
            
            # append results to the geocoded results dataframe and return
            return [df_geo.append(result_df), missed_ix]

        except:
            print('Above batch did not run')
            # Divide batch size in half and run with half the size
            batch_mid = (int)((batch_end+batch_start)/2)
            df_geo, missed_ix = tryBatch(batch_start, batch_mid, missed_ix,
                                         df_raw, df_geo, temp_csv_name)
            df_geo, missed_ix = tryBatch(batch_mid, batch_end, missed_ix, 
                                         df_raw, df_geo, temp_csv_name)
            
# Iterate through the necessary number of batches
for batch_ix in range(batches):
    print('\nBatch Index: ' + str(batch_ix) + '/' + str(batches - 1))
    batch_time = time.time()

    if time.time() - last_save > save_gap:
        # Save current geocoding
        df_geo.to_csv(out_path)
        last_save = time.time()

        # Save remaining csv
        df_remaining = df_raw[batch_ix*batch_size:][:]
        df_remaining.to_csv(remain_path)
        
    # try running batch through census API
    batch_start = batch_ix * batch_size
    batch_end = (batch_ix + 1) * batch_size - 1
    
    # Run current batch
    df_geo, missed_ix = tryBatch(batch_start, batch_end, missed_ix, df_raw, 
                                 df_geo, temp_name)
        
# Convert geocoded dataframe into our desired geodataframe
df_geo.to_csv(out_path)

# Delete remaining file if finished
os.remove(remain_path)