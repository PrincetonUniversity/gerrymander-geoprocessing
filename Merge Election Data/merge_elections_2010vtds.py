import geopandas as gpd
import pandas as pd
import re

#%%

elec = pd.read_csv('../openelections-results-va/raw/20081104__va__general__'\
                   'precinct__raw.csv')

#%%
m = re.compile('state:va\/(.*)\/precinct')

def find_muni(x):
    match = m.search(x)
    if match:
        # some have underscores, some have spaces
        return match[1].replace('_', ' ') 
    else:
        return ''

elec['muni'] = elec['division'].apply(find_muni)

# alexandria is incorrectly referred to as a county in OpenElections
elec.loc[elec['muni']=='county:alexandria', 'muni'] = 'place:alexandria' 
# same for bristol
elec.loc[elec['muni']=='county:bristol', 'muni'] = 'place:bristol' 

counties = pd.read_csv('https://www2.census.gov/geo/docs/reference/codes/'\
                       'files/st51_va_cou.txt', header=None, \
                       names=['STATE', 'STATEFP', 'COUNTYFP', 'COUNTYNAME', \
                              'CLASSFP'], dtype=str)

municipality = {'county': 'county',
                'city': 'place'}

for _, county in counties.iterrows():
    name = county['COUNTYNAME']
    name_start = name.rsplit(' ', 1)[0].lower() # drop last word
    name_end = name.split()[-1].lower() # take end
    match_str = municipality[name_end] + ':' + name_start
    
    for i, _ in elec.iterrows():
        if elec.loc[i, 'muni'] == match_str:
            elec.loc[i, 'COUNTYFP'] = county['COUNTYFP']
    
#%%

def vtd(x):
    match = re.match('^[0-9]{3}', x[:3])
    if match:
        return match[0]
    else:
        return ''

elec['VTDST10'] = elec['jurisdiction'].apply(vtd)


def zero_if_multiple(x):
    if len(x)==1:
        return x
    else:
        return 0

elec_p = elec.pivot_table(index=['COUNTYFP', 'VTDST10'], columns='last_name',\
                          values='votes', aggfunc=zero_if_multiple)
elec_p = elec_p[['Obama', 'McCain']].astype(int)


df = gpd.read_file('tl_2012_51_vtd10.shp')

# ensure leading zeros, 3 digits

df['VTDST10'] = df['VTDST10'].apply(lambda x: str(int(x)).zfill(3)) 
for i, row in df.iterrows():
    index = (row['COUNTYFP10'], row['VTDST10'])
    for cand in ['Obama', 'McCain']:
        if index in elec_p.index:
            df.at[i, '2008_' + cand] = elec_p.loc[index][cand]
        else:
            if len(row['VTDST10']) == 4:
                # some VTDs come in multiple parts in the shapefile but are merged in the OE file.
                # for a VTD coded in OE as '402', the VTDST10 codes will be '4021' and '4022'
                # this is a hack because i know that repeat VTDS only come in pairs.
                # TODO: have this check for the number of multipart VTDs
                df.at[i, '2008_' + cand] = elec_p.loc[(index[0], index[1][:3])][cand] / 2 
            else:
                df.at[i, '2008_' + cand] = None

#%%

df['twoparty'] = df['2008_Obama'] / (df['2008_Obama'] + df['2008_McCain'])

sum(df['2008_Obama'].isnull()) / len(df)
        
'''
Pretty good, 1% of VTDs are unmatched.

Other problem is that there are rows in OE data that are unaccounted for.

TODO: mark rows in openelections as they are accounted for. unaccounted rows 
should get distributed among the county by the population of each VtD

ACTUALLY IT LOOKS LIKE THE DATAVERSE FILE IS JUST BUGGY AND HAS MISSING 
GEOMETRIES. SHOULD BE EASY TO JUST FILL THESE IN.
'''

df.to_file('2008pres_added.shp')

