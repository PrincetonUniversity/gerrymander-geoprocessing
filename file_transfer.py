import os
import csv
import pandas as pd
import shutil
import helper_tools as ht

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/Transfer CSVs/SHP_transfer_all.csv"

# Initial try and except to catch improper csv_path or error exporting the
# results of the transfer
try:
    # Import Google Drive path
    direc_path = ht.read_one_csv_elem(csv_path)
    
    # Import table from CSV into pandas df
    csv_col = ['Folder', 'Source', 'Single File', 'Path']
    csv_list = []
    csv_df = ht.read_csv_to_df(csv_path, 1, csv_col, csv_list)

    # Initialize out_df, which contains the batching output
    new_cols = ['Result', 'Locality', 'File ix', 'Original Name', 'File Type',\
               'Origin', 'Modified Name']
    out_df = pd.DataFrame(columns=new_cols)
    
    # Set list of extension types that do not get entries into out_df
    no_entry_ext = ['cpg', 'dbf', 'prj', 'xml', 'shx', 'sbn', 'sbx', 'lock']
    
    # Iterate through each row/folder we are transferring files form
    for i, _ in csv_df.iterrows():

        # Create Check that determines whether any files exist
        no_files_exist = True
        
        # Path to single file case. Single File will equal 1
        if csv_df.at[i, 'Single File']:
            
            # Boolean to determine if
            no_files_exist = False
            
            # Identify current and new full path names
            file = csv_df.at[i, 'Path'].split('/')[-1]
            file_type = file.split('.')[-1]                            
            new_name = 'source-' + csv_df.at[i, 'Source'] + \
                        '-originally-' + file
            # ensure no spaces in filename
            new_name = new_name.replace(' ', '_')
        
            # Ensure that the new file name is not too l ong
            if len(new_name) > 255:
                len_delete = len(new_name) - 255
                ext = new_name.split('.')[-1]
                len_ext = len(ext) + 1
                new_name = new_name.split('.')[0][:-len_delete] + '.' + ext
                
            # Get current paths
            cur_path = csv_df.at[i, 'Path']
            new_path = direc_path + '/' + csv_df.at[i, 'Folder'] + '/' + \
                        new_name
                        
            # Try to copy file, otherwise print error in results csv and
            # skip the file
            try:
                # Make copy of file in new location with the new name
                shutil.copy(cur_path, new_path)
                
                # Set out_df if extension is not in no_entry list
                if file_type not in no_entry_ext:
                    row = len(out_df)
                    out_df.at[row, 'Locality'] = csv_df.at[i, 'Folder']
                    out_df.at[row, 'Origin'] = csv_df.at[i, 'Source']
                    out_df.at[row, 'File ix'] = -1
                    out_df.at[row, 'File Type'] = file_type.upper()
                    out_df.at[row, 'Modified Name'] = new_name
                    out_df.at[row, 'Original Name'] = file
                    out_df.at[row, 'Result'] = 'Successful Transfer'
                    
            # Exception and RESULTS csv if shutil.copy doesn't work
            except:
                error_str = 'FILE ERROR: The copying of ' + cur_path + \
                            ' to ' + new_path + \
                            ' has failed. File may already be in folder.\n'
                fail_str = 'FAILURE to TRANSFER: ' + error_str
                print(error_str)
                row = len(out_df)
                out_df.at[row, 'Locality'] = csv_df.at[i, 'Folder']
                out_df.at[row, 'Origin'] = csv_df.at[i, 'Source']
                out_df.at[row, 'File ix'] = -1
                out_df.at[row, 'File Type'] = file_type.upper()
                out_df.at[row, 'Modified Name'] = new_name
                out_df.at[row, 'Original Name'] = file
                out_df.at[row, 'Result'] = fail_str
                
        else:
            # Get the files in the current folder
            for _, _, files in os.walk(csv_df.at[i, 'Path']):
                
                # Note that files exist in the folder, 
                no_files_exist = False
    
                # Iterate through every file in the current folder
                for file in files:
                    
                    # Identify current and new full path names
                    file_type = file.split('.')[-1]                            
                    new_name = 'source-' + csv_df.at[i, 'Source'] + \
                                '-originally_' + file
                    # ensure no spaces in filename
                    new_name = new_name.replace(' ', '_')
                                
                    # Ensure that the new file name is not too l ong
                    if len(new_name) > 255:
                        len_delete = len(new_name) - 255
                        ext = new_name.split('.')[-1]
                        len_ext = len(ext) + 1
                        new_name = new_name.split('.')[0][:-len_delete] + '.' + ext
                    
                    # Get current paths
                    cur_path = csv_df.at[i, 'Path'] + '/' + file
                    new_path = direc_path + '/' + csv_df.at[i, 'Folder'] + '/' + \
                                new_name
                                
                    # Try to copy file, otherwise print error in results csv and
                    # skip the file
                    try:
                        # Make copy of file in new location with the new name
                        shutil.copy(cur_path, new_path)
                        
                        # Set out_df if extension is not in no_entry list
                        if file_type not in no_entry_ext:
                            row = len(out_df)
                            out_df.at[row, 'Locality'] = csv_df.at[i, 'Folder']
                            out_df.at[row, 'Origin'] = csv_df.at[i, 'Source']
                            out_df.at[row, 'File ix'] = -1
                            out_df.at[row, 'File Type'] = file_type.upper()
                            out_df.at[row, 'Modified Name'] = new_name
                            out_df.at[row, 'Original Name'] = file
                            out_df.at[row, 'Result'] = 'Successful Transfer'
                            
                    # Exception and RESULTS csv if shutil.copy doesn't work
                    except:
                        error_str = 'FILE ERROR: The copying of ' + cur_path + \
                                    ' to ' + new_path + \
                                    ' has failed. Check Google Drive path\n'
                        fail_str = 'FAILURE to TRANSFER: ' + error_str
                        print(error_str)
                        row = len(out_df)
                        out_df.at[row, 'Locality'] = csv_df.at[i, 'Folder']
                        out_df.at[row, 'Origin'] = csv_df.at[i, 'Source']
                        out_df.at[row, 'File ix'] = -1
                        out_df.at[row, 'File Type'] = file_type.upper()
                        out_df.at[row, 'Modified Name'] = new_name
                        out_df.at[row, 'Original Name'] = file
                        out_df.at[row, 'Result'] = fail_str
        
        # Error and RESULTS csv if no files in the current folder exist
        if no_files_exist:
            error_str = 'FOLDER ERROR: Either (1) No files exist in the ' \
                        'folder or (2) the following path is incorrect: ' + \
                        csv_df.at[i, 'Path'] + '\n'
            fail_str = 'FAILURE to TRANSFER:' + error_str
            print(error_str)
            row = len(out_df)
            out_df.at[row, 'Result'] = fail_str
        
    # Create path to output our results CSV file and output
    csv_out_path = csv_path[:-4] + ' RESULTS.csv'
    out_df.to_csv(csv_out_path)
# CSV file could not be read in or exported
except:
    print('ERROR: Path for csv file does not exist AND/OR close RESULTS csv')