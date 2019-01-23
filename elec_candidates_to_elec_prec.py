import pandas as pd
import geopandas as gpd
import numpy as np


#paste path to raw election results which have candidates as rows
raw_elec = '/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/VA/Election Results/2017 June Democratic Primary.csv'

elec_df = pd.read_csv(raw_elec)
elec_df['loc_prec'] = elec_df['LocalityName'].map(str) + ',' + elec_df['PrecinctName']

#make list of office titles
offices_tot = elec_df['office'].unique()
counties_tot = elec_df['LocalityName'].unique()
state_offices = []
counties_office = {}
#loop through offices and find statewide ones
for office in offices_tot:
    counties  = []
    counties.append(elec_df.loc[elec_df['office'] == office, 'LocalityName'])
    #list of counties that had an election for that office
    counties_office[office] = counties
    c = counties_office[office][0].values
    D = {I: True for I in c}
    count = D.keys()
    if len(count) ==  len(counties_tot):
        state_offices.append(office)
state_elec = elec_df.loc[elec_df['office'].isin(state_offices)]

#get table of elections by precinct
prec_elec = pd.pivot_table(state_elec, index = ['loc_prec'], columns = ['party','office'], values = ['votes'], aggfunc = np.sum)

prec_elec.columns = prec_elec.columns.to_series().str.join(' ')

columns = prec_elec.columns.values

#print columns and assign each one a 10 character name for the shapefile
print(columns)

#%%
#make dic for column name replacement using the columns printed in module above
#columns can only have 10 character names
prec_elec_rn = prec_elec.rename(columns = {'votes Democratic U.S. House': 'G18DHOR',
 'votes Democratic U.S. Senate': 'G18DSEN',
 'votes Libertarian U.S. House': 'G18OHOR',
 'votes Libertarian U.S. Senate': 'G18OSEN',
 'votes Republican U.S. House': 'G18RHOR',
 'votes Republican U.S. Senate': 'G18RSEN'})

#get rid of other columns and save
#this is ready to be matched to precinct names now
prec_elec_rn = prec_elec_rn[['G18DHOR','G18DSEN','G18OHOR', 'G18OSEN', 'G18RHOR', 'G18RSEN']]

prec_elec_rn.to_csv('/Volumes/GoogleDrive/Team Drives/princeton_gerrymandering_project/mapping/VA/Election Results/Cleaned Results/VAG18.csv')
