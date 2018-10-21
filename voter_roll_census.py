import time
import pandas as pd
#import geopandas as gpd
import math
import censusbatchgeocoder
#import shapely as shp
import warnings
warnings.filterwarnings("ignore")
#import helper_tools as ht

# import original CSV voter file as DataFrame
raw_path = 
raw_cols = ['id', 'address', 'city', 'state', 'zipcode', 'precinct']
df_raw = pd.read_csv(raw_path, names=raw_cols, header=0)
df_raw = df_raw.set_index('id')
df_raw['address'] = df_raw['address'].str.strip()

# Define how large and many batches to use. Maximum batch size for cenus 
# geocoding is 1000. However, there will sometimes be a timeout request
batch_size = 500
batches = math.ceil(len(df_raw) / batch_size)

# initialize single calls indexes. List of lists where the first
# element is the starting index and the second element is the ending index
missed_ix = []

# initialize geocoded dataframe
df_geo =  pd.DataFrame()
df_missed = pd.DataFrame()
df_remaining = pd.DataFrame()

# Get start time
start = time.time()
last_save = time.time()
save_gap = 60

out_path = 
missed_path = 
remain_path = 


# Iterate through the necessary number of batches
for batch_ix in range(batches):
    print('Batch Index: ' + str(batch_ix) + '/' + str(batches))
    batch_time = time.time()
    
    if time.time() - last_save > save_gap:
        
        # Save current geocoding
        df_geo.to_csv(out_path)
        last_save = time.time()
        print('HERE')
        # Save remaining csv
        df_remaining = df_raw[batch_ix*batch_size:][:]
        df_remaining.to_csv(remain_path)
        
        
    try:
        # Get starting and ending rows in the batch. Loc does not care if index
        # is greater than  length
        batch_start = batch_ix * batch_size
        batch_end = (batch_ix + 1) * batch_size - 1
        
        # Initialize the batch dataframe
        batch_df = df_raw.loc[batch_start:batch_end][:]

        # create dummy csv to load batches into the census API wrapper
        filename = './dummy.csv'
        batch_df.to_csv(filename)
    
        # reset result dataframe
        result_df = pd.DataFrame()
    
        # Put batch through census API
        result_dict = censusbatchgeocoder.geocode(filename)
        result_df = pd.DataFrame.from_dict(result_dict)
        
        # append to the geo dataframe
        df_geo = df_geo.append(result_df)
        
        print('Batch Time: ' + str(time.time() - batch_time))

    except:
        print('Above batch did not run')
        print(batch_ix)
        missed_ix.append([batch_start, batch_end])
        
        # iterate through all the missed indexes individaully and call
        for missed in missed_ix:
            print(missed)
            for i in range(missed[0], missed[1] + 1):
                df_missed = pd.DataFrame()
                df_missed = df_missed.append(df_raw.loc[i][:])
                df_missed.to_csv(missed_path)

        
        
# Convert geocoded dataframe into our desired geodataframe
df_geo.to_csv(out_path)

# iterate through all the missed indexes individaully and call
for missed in missed_ix:
    print(missed)
    for i in range(missed[0], missed[1] + 1):
        df_missed = pd.DataFrame()
        df_missed = df_missed.append(df_raw.loc[i][:])
        df_missed.to_csv(missed_path)
