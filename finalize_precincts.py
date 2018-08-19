import time
import pandas as pd
import geopandas as gpd
import os
import shapely as shp
import csv

# Get path to our CSV file
csv_path = "G:/Team Drives/princeton_gerrymandering_project/mapping/VA/Precinct Shapefile Collection/CSV/Finalize/Finalize_All_Aug18.csv"

def main():
    # Initial try and except to catch improper csv_path or error exporting the
    # results of the transfer
    try:
        # Import Google Drive path
        with open(csv_path) as f:
            reader = csv.reader(f)
            data = [r for r in reader]
        direc_path = data[0][1]
        # Import table from CSV into pandas dataframe
        name_list = ['Locality', 'Census Path', 'Out Folder']
        csv_df = pd.read_csv(csv_path, header=1, names=name_list)

        # Initialize out_df, which contains the results of the transfers and
        # contains what will be copied into the conversion page of the Google
        # sheet
        new_cols = ['Result', 'Time Taken', 'Num Census Blocks']
        out_df = pd.DataFrame(columns=new_cols)
        
        # Iterate through each county we are creating a shapefile for
        for i, _ in csv_df.iterrows():
            
            # Create shapefile out of precincts
            try:
                # Begin Start time
                start_time = time.time()
                
                # Set unique variables for the current county
                local = csv_df.at[i, 'Locality']
                shape_path = csv_df.at[i, 'Census Path']
                out_folder = csv_df.at[i, 'Out Folder']

                # Change census shapefile path and out folder if set to default
                if shape_path == 1:
                    census_filename = local + '_census_block.shp'
                    census_filename = census_filename.replace(' ', '_')
                    shape_path = direc_path + '/' + local + '/' + \
                                    census_filename
                
                if out_folder == 1:
                    out_folder = direc_path + '/' + local
                
                # Print Locality Name to see where errors are from
                print('\n' + local)
                
                # Generate precinct shapefile and add corresponding precinct
                # index to the attribute field of the census block shapefile
                result = generate_precinct_final(local, shape_path, \
                                                      out_folder)
                
                row = len(out_df)
                out_df.at[row, 'Result'] = 'SUCCESS'
                out_df.at[row, 'Time Taken'] = time.time() - start_time
                out_df.at[row, 'Num Census Blocks'] = result
                
            # Shapefile creation failed
            except Exception as e:
                print(e)
                print('ERROR:' + csv_df.at[i, 'Locality'])
                row = len(out_df)
                out_df.at[row, 'Result'] = 'FAILURE'
        
        # Create path to output our results CSV file and output
        csv_out_path = csv_path[:-4] + ' RESULTS.csv'
        out_df.to_csv(csv_out_path)
    
    # CSV file could not be read in or exported
    except:
        print('ERROR: Path for csv file does not exist OR close RESULTS csv')
    
def generate_precinct_final(local, shape_path, out_folder):    
    ''' Generates the final precinct level shapefile from census block data
    and an update "precinct" region attribute column. Also gives the locality
    as an attribute column for each precinct
    
    Arguments:
        local: name of the locality
        shape_path: full path to the census block shapefile
        out_folder: directory that precinct level shapefile will be saved in
        
    Output:
        Number of census blocks in the county
        '''        
    # Delete CPG file if it exists
    cpg_path = ''.join(shape_path.split('.')[:-1]) + '.cpg'
    if os.path.exists(cpg_path):
        os.remove(cpg_path)

    # read in census block shapefile
    df = gpd.read_file(shape_path)
    
    ###########################################################################
    ###### CREATE PRECINCTS USING ID ##########################################
    ###########################################################################
    
    # Get unique values in the df ID column
    prec_names = list(df['precinct'].unique())
    
    # Create dataframe of precincts
    df_prec = pd.DataFrame(columns=['precinct', 'geometry', 'locality'])

    # Iterate through all of the precinct IDs and set geometry of df_prec with
    # union
    for i, elem in enumerate(prec_names):
        df_poly = df[df['precinct'] == elem]
        polys = list(df_poly['geometry'])
        
        geometry = shp.ops.cascaded_union(polys)
        df_prec.at[i, 'geometry'] = geometry
        df_prec.at[i, 'precinct'] = elem

    # Initialize Locality Name
    df_prec['locality'] = local
    
    ###########################################################################
    ###### Save Shapefiles ####################################################
    ###########################################################################
    
    # Save Precinct Shapefile
    out_name = local + '_precincts_final'
    out_name = out_name.replace(' ', '_')

    df_prec = gpd.GeoDataFrame(df_prec, geometry='geometry')
    df_prec.to_file(out_folder + '/' + out_name + '.shp')
        
    return len(df)
        
if __name__ == '__main__':
    main()