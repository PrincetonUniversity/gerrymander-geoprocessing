import pandas as pd
from titlecase import titlecase

input_csv_path = ""
output_tsv_path = ""

# Read in CSV that contains 'locality' and 'precinct' attributes
df_in = pd.read_csv(input_csv_path)

# initialize output dataframme
df_out = pd.DataFrame(columns=['Locality', 'Precincts', 'Num Precincts'])

# Iterate through all of the unique localities
for locality in set(df_in.locality.to_list()):
    # Get dataframe of only entries in the locality
    df_temp = df_in[df_in.locality == locality]

    # Get list of precinct names, sort alphabetically, and apply titlecase
    precincts = list(df_temp.precinct.unique())
    precincts.sort()
    precincts = [titlecase(elem) for elem in precincts]
    
    # Save num and list of precincts in out df and 
    new_row = len(df_out)
    df_out.at[new_row, 'Locality'] = locality
    df_out.at[new_row, 'Precincts'] = ', '.join(precincts)
    df_out.at[new_row, 'Num Precincts'] = len(precincts)
    
# Save TSV
df_out.to_csv(output_tsv_path, sep='\t')