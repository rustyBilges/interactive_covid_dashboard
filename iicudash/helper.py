#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 10:54:53 2020

@author: rustybilges
"""

import numpy as np
import pandas as pd
import pyodbc
from interface import implements, Interface

def icca_query(sql):
    
    try:
        server = "ubhnt175.ubht.nhs.uk"
        database = "CISReportingDB"
        tc ="yes"  
    
        cnxn = pyodbc.connect('trusted_connection='+tc+';DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
        data = pd.read_sql(sql,cnxn)
    except:
        print("Error: Could not complete query. Returning empty dataframe.")
        data = pd.DataFrame()
        
    return data

class I_Intervention(Interface):
    '''
    Interface class to define how intervention time series (for a single patient) will be created and processed. 
    '''
    def populate(self, interventions_attributes, column):
        ''' interventions_attributes is a list of tuples '''
        pass
    
    def get_most_recent_value(self, time):
        pass
    
    def get_worst_value(self, start, end, metric_func):
        pass
    
    def get_series(self, start, end):
        pass

    def get_delta(self, time):
        pass

class Dummy_Intervention(implements(I_Intervention)):

    def __init__(self, means, stds, freq, integer=False):

        self.integer = integer
        self.df = self.populate(zip(means, stds), freq)
        
    def populate(self, interventions_attributes, column):
        ''' interventions_attributes is a list of tuples '''
        np.random.rand
    
    def get_most_recent_value(self, time):
        pass
    
    def get_worst_value(self, start, end, metric_func):
        pass
    
    def get_series(self, start, end):
        pass

    def get_delta(self, time):
        pass

    
    
#class Icca_Intervention(implements(I_Intervention)):