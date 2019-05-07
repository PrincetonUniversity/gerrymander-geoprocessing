import time
import pandas as pd
import math
import censusbatchgeocoder
import warnings
import os
warnings.filterwarnings("ignore")
redo = [0,1,3,4,6,8,9,21,28,34,36]
for n in redo:
    # import original CSV voter file as DataFrame
    raw_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/Voter Roll/OH_voter_roll_" + str(n) + ".csv"
    df_raw = pd.read_csv(raw_path, header=0)
    df_raw = df_raw.rename(columns={'Unnamed: 0':'id','RESIDENTIAL_ADDRESS1':'address','RESIDENTIAL_CITY':'city','RESIDENTIAL_STATE':'state','RESIDENTIAL_ZIP':'zipcode','PRECINCT_NAME':'precinct'})
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
    
    out_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/Voter Roll/OH_voter_roll_" + str(n) + "_census_geocode.csv"
    missed_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/Voter Roll/OH_voter_roll_" + str(n) + "_census_missed.csv"
    remain_path = "/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/OH/Voter Roll/OH_voter_roll_" + str(n) + "_census_remaining.csv"
    
    
    # Iterate through the necessary number of batches
    for batch_ix in range(batches):
        print('\nBatch Index: ' + str(batch_ix) + '/' + str(batches))
        batch_time = time.time()
        
        if time.time() - last_save > save_gap:
            
            # Save current geocoding
            df_geo.to_csv(out_path)
            last_save = time.time()
    
            # Save remaining csv
            df_remaining = df_raw[batch_ix*batch_size:][:]
            df_remaining.to_csv(remain_path)
            
            
        try:
            # Get starting and ending rows in the batch. Loc does not care if index
            # is greater than  length
            batch_start = batch_ix * batch_size
            batch_end = (batch_ix + 1) * batch_size - 1
            
            # Initialize the batch dataframe
            batch_df = df_raw.iloc[batch_start:batch_end][:]
    
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
            df_missed = pd.DataFrame()
            # iterate through all the missed indexes individaully and call
            for missed in missed_ix:
                df_missed = df_missed.append(df_raw.iloc[missed[0]:missed[1]+1][:])
                df_missed.to_csv(missed_path)
            
    # Convert geocoded dataframe into our desired geodataframe
    df_geo.to_csv(out_path)
    
    # Delete remaining file if finished
    os.remove(remain_path)

