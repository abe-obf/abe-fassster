#
#   IMPORT THE FOLLOWING
#
from handlers.BaseHandler import BaseHandler
import pandas as pd
import ast
import json
import tornado
import datetime
import os

#
#   DEFINE CLASS AS SUBCLASS OF BasHandler
#   @author ABE
#
class DeathsHandler(BaseHandler) :
    
    folder = 'covid-lgu' # directory name

    #
    #   GET LATEST FILE
    #   @reference SocialRiskHandler.py
    #
    def getLatestFile(self, folder):
        latest = [x for x in os.listdir("datasets/{}/latest/".format(folder)) if x.endswith(".csv")][0]
        print(latest)
        return latest

    #
    #   METHOD FOR DEATHS PER DAY (GRAPH NUMBER 5)
    #   COMPUTES DAILY DEATHS, MEDIAN, 75TH PERCENTILE
    # 
    def processDeaths(self, reg, prov, city, brgy) :
        data_types = {
                        'regsionPSGC': str,
                        'provincePSGC': str,
                        'cityPSGC': str,
                        'barangayPSGC': str
                    }

        latestFile = self.getLatestFile(self.folder)
        data = pd.read_csv('datasets/' + self.folder + '/latest/' + latestFile,
            dtype=data_types)
        data = data.apply(lambda x: x.fillna('NDA'))

        #   assign 1 death instance per row
        data['count'] = 1
        died = data[data['Status'] == 'Died'] # filter only those who 'Died'

        #
        #   applying PSGC filters
        #  
        if reg != '' :
            died = died[died['regionPSGC'].apply(str).str.slice(0, len(reg)) == reg]
        if prov != '' :
            died = died[died['provincePSGC'] == prov]
        if city != '' :
            died = died[died['cityPSGC'] == city]
        if brgy != '' :
            died = died[died['brgyPSGC'] == brgy]

        # get daily deaths
        deaths_per_day = died.groupby(['Date Died'])['count'].aggregate(sum) # group deaths by their date
        # or
        # died.groupby(['Date Died']).agg({'count': ['sum']})

        
        # get MEDIAN of deaths per day
        dpd_median = deaths_per_day.median()
        
        # get 75th PERCENTILE of deaths per day
        dpd_percentile_75 = deaths_per_day.quantile(0.75)
        

        # resetting columns
        deaths_per_day = deaths_per_day.reset_index() # reset columns

        # get 7 DAY MOVING AVERAGE
        deaths_per_day['7dma'] = deaths_per_day.iloc[:,1].rolling(window=7).mean()
        deaths_per_day = deaths_per_day.apply(lambda x: x.fillna('NDA'))

        # sort dataframe
        deaths_per_day = deaths_per_day.sort_index(ascending=True) # sort

        # convert to (date, count) instances
        deaths_per_day = deaths_per_day.to_records().tolist()
                
        return {
            'dpd': deaths_per_day,
            'dpd_med': dpd_median,
            'dpd_per75': dpd_percentile_75
        }

    #
    ## SAMPLE METHOD TO GET URL PARAMS
    #
    def sampleMethod(self, reg, prov, city, brgy) :
        return {
            'region' : reg,
            'provinve' : prov,
            'city' : city,
            'barangay' : brgy
        }


    #
    ## GET METHOD
    #
    def get(self):
        status = 1
        result = ''

        try:

            # GET PSGC VARIABLE FROM URL
            reg = self.get_argument('r', default = '', strip=False)
            prov = self.get_argument('p', default = '', strip=False)
            city= self.get_argument('c', default = '', strip=False)
            brgy = self.get_argument('b', default = '', strip=False)

            # RETURN DATA 
            # result = self.sampleMethod(reg, prov, city, brgy)
            result = self.processDeaths(reg, prov, city, brgy)
            
        except:
            status = 0
        
        response = {
            'status' : status,
            'result' : result
        }
        self.write(response)
