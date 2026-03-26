from pynhd import NLDI
import geopandas as gpd
import pandas as pd
from supporting_scripts import getData, SNOTEL_Analyzer, dataprocessing, mapping
from shapely.geometry import box, Polygon
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings("ignore")

station_id = "11274790" # NWIS id for Tuolumne river at the mouth of Hetch Hetchy Reservoir
basinname = 'TuolumneRiverBasin'

#load snotel data
unprocessed_SNOTEL = {}
#read all files in the following path into the dictionary
path = 'files/SNOTEL'
for filename in os.listdir(path):
    if filename.endswith('.csv'):
        #select the name of the file between the _ and _
        name = filename.split('_')[1] 
        unprocessed_SNOTEL[name] = pd.read_csv(os.path.join(path, filename))
        #make the date a datetime object and set to the index
        unprocessed_SNOTEL[name]['Date'] = pd.to_datetime(unprocessed_SNOTEL[name]['Date'])
        unprocessed_SNOTEL[name].set_index('Date', inplace=True)
        #rename the Snow Water Equivalent (m) Start of Day Values to SWE_cm
        unprocessed_SNOTEL[name].rename(columns={'Snow Water Equivalent (m) Start of Day Values': f"{name}_SWE_cm"}, inplace=True)
        #convert SWE_m to cm
        unprocessed_SNOTEL[name][f"{name}_SWE_cm"] = unprocessed_SNOTEL[name][f"{name}_SWE_cm"] * 100
        #remove the Water_Year column
        unprocessed_SNOTEL[name].drop(columns=['Water_Year'], inplace=True)
        #we need to know how many obs for each DF, print the df name, its length, and the start/end dates
        print(f"{name}: {len(unprocessed_SNOTEL[name])} start date: {unprocessed_SNOTEL[name].index.min()} end date: {unprocessed_SNOTEL[name].index.max()}")
    
#The TES site is missing many values and will not be useful for our analysis, remove it
unprocessed_SNOTEL.pop('TES', None)

#The site with the latest start date will guide the rest
latest_start_date = max([df.index.min() for df in unprocessed_SNOTEL.values()])

#The site with the earliest end date will guide the rest
soonest_end_date = min([df.index.max() for df in unprocessed_SNOTEL.values()])
for key in unprocessed_SNOTEL.keys():
    unprocessed_SNOTEL[key] = unprocessed_SNOTEL[key][unprocessed_SNOTEL[key].index >= latest_start_date]
    unprocessed_SNOTEL[key] = unprocessed_SNOTEL[key][unprocessed_SNOTEL[key].index <= soonest_end_date]

#merge all dictionary dataframes into one larger dataframe
SNOTEL_df = pd.concat(unprocessed_SNOTEL.values(), axis=1)
#set the date index to be the index of the first dataframe in the dictionary

SNOTEL_df.head()

#Read the data from PyDayMet 
PyDayMet_df = pd.read_csv(f"files/PyDayMet/PyDayMet_{station_id}.csv")
#set the date column to be a datetime object and set it to the index
PyDayMet_df['Date'] = pd.to_datetime(PyDayMet_df['Date'])
PyDayMet_df.set_index('Date', inplace=True)
PyDayMet_df.head()

#Read the data from NLDAS 
NLDAS_df = pd.read_csv(f"files/NLDAS/NLDAS_{station_id}.csv")
#set the date column to be a datetime object and set it to the index
NLDAS_df['Date'] = pd.to_datetime(NLDAS_df['Date'])
NLDAS_df.set_index('Date', inplace=True)
NLDAS_df.head()

basin_info = pd.read_csv(f"files/basin_info/basin_info_{station_id}.csv")
basin_info.head()

#find the latest start date and the earliest end date for SNOTEL_df, met_df, cleaned
begin_date = max([df.index.min() for df in [SNOTEL_df, PyDayMet_df, NLDAS_df]]) 
end_date = min([df.index.max() for df in [SNOTEL_df, PyDayMet_df, NLDAS_df]]) 

#clip each dataframe to have the same begin and end dates
SNOTEL_df = SNOTEL_df[(SNOTEL_df.index >= begin_date) & (SNOTEL_df.index <= end_date)]
PyDayMet_df = PyDayMet_df[(PyDayMet_df.index >= begin_date) & (PyDayMet_df.index <= end_date)]
NLDAS_df = NLDAS_df[(NLDAS_df.index >= begin_date) & (NLDAS_df.index <= end_date)]

#find the latest start date and the earliest end date for SNOTEL_df, met_df, cleaned
begin_date = max([df.index.min() for df in [SNOTEL_df, PyDayMet_df, NLDAS_df]]) 
end_date = min([df.index.max() for df in [SNOTEL_df, PyDayMet_df, NLDAS_df]]) 

#clip each dataframe to have the same begin and end dates
SNOTEL_df = SNOTEL_df[(SNOTEL_df.index >= begin_date) & (SNOTEL_df.index <= end_date)]
PyDayMet_df = PyDayMet_df[(PyDayMet_df.index >= begin_date) & (PyDayMet_df.index <= end_date)]
NLDAS_df = NLDAS_df[(NLDAS_df.index >= begin_date) & (NLDAS_df.index <= end_date)]

#merge the SNOTEL_df, met_df, and streamflow dataframes
Hydro_df = pd.concat([SNOTEL_df, PyDayMet_df, NLDAS_df], axis=1)
#put the site_no column, second to last, and streamfow column, last column, as the first two columns in the dataframe
cols = Hydro_df.columns.tolist()
cols = cols[-2:] + cols[:-2]
Hydro_df = Hydro_df[cols]
Hydro_df.head()

#all of the NaN values here should be 0, fill them
Hydro_df = Hydro_df.fillna(0)
Hydro_df.head()

#add in the basin info as columns in the dataframe, repeat the values for each row
for col in basin_info.columns:
    Hydro_df[col] = basin_info[col][0]

Hydro_df.head()

#take a look around peak SWE to make sure we have snotel values, early season can be tricky to assess
Hydro_df.loc['2019-03-01':'2019-04-01']

Hydro_df.tail()



