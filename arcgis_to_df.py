import pandas as pd
from itertools import compress

pgp = '/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/'

# load in Madeleine's data
df = pd.read_csv(pgp + 'mapping/PA/ArcGIS_neighbors/ArcGIS_neighbors.txt',
                   dtype={'src_GEOID10': str, 'nbr_GEOID10': str, 'LENGTH': float, 'NODE_COUNT': int},
                   names=['id', 'src', 'nbr', 'shared_perim', 'nodes'],
                   header=0)

df = df[df['nodes']==0]
df = df[['src', 'nbr', 'shared_perim']]

state_code = '42' # PA state code

nbrs = df.groupby('src')['nbr'].apply(list)
lengths = df.groupby('src')['shared_perim'].apply(list)


df = pd.concat([nbrs, lengths], axis=1).reset_index()

df = df[df['nbr'].apply(len)>1] # get rid of precincts with only one neighbor (donut hole precincts)



# find all precincts with adjacent state neighbors, replace them with consecutive negative integers, sum the shared perimeter
counter = -1
for row in df.index:
    adj_state_neighbors = [not i.startswith(state_code) for i in df.loc[row, 'nbr']]
    if any(adj_state_neighbors):
        df.loc[row, 'nbr'] = (list(compress(df.loc[row, 'nbr'], [not i for i in adj_state_neighbors]))
                              + [str(counter)])
        df.loc[row, 'shared_perim'] = (list(compress(df.loc[row, 'shared_perim'], [not i for i in adj_state_neighbors]))
                                       + [sum(list(compress(df.loc[row, 'shared_perim'], adj_state_neighbors)))])
        counter -= 1

# load dataverse voting data, D and R senate vote 2010, as well as population
dataverse = pd.read_csv(pgp + 'mapping/PA/dataverse/pa_final.tab', sep='\t', usecols=['geoid10', 'pop100', 'ussdv2010', 'ussrv2010'],
                        dtype={'geoid10': str, 'pop100': int, 'ussdv2010': float, 'ussrv2010': float})

df = df.merge(dataverse, left_on='src', right_on='geoid10').drop(columns='geoid10')
