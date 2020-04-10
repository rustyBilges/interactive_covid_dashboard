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

import random
import time
from dateutil.parser import parse

try:
    from iicudash.mappings import MAPPING, DUMMY_MAPPING
except ImportError:
    try:
        from mappings import MAPPING, DUMMY_MAPPING
    except:
        print("Could not import mappings.")

def icca_query(sql, db="CISReportingActiveDB0"):
    
    try:
        server = "ubhnt175.ubht.nhs.uk"
        database = db
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
        ''' interventions_attributes is a list of tuples.
            It is assumed that this list is ordered according to usage preference.
        '''
        pass
    
    def get_most_recent_value(self, time=None):
        pass
    
    def get_worst_value(self, start=None, end=None, metric_func=None):
        pass
    
    def get_series(self, start=None, end=None):
        pass

    def get_delta(self, time=None):
        pass

class Dummy_Intervention(implements(I_Intervention)):

    def __init__(self, means, stds, freq, name, integer=False, non_neg=True):

        self.name = name 
        self.integer = integer
        self.non_neg = non_neg
        self.start = None
        self.end = None
        self.df = self.populate(zip(means, stds), freq)
        
    def populate(self, interventions_attributes, column):
        ''' interventions_attributes is a list of tuples '''
        admission = pd.to_datetime(self.random_date("2019-12-01 13:40:00", "2020-02-24 14:50:00", random.random()))
        now = admission + pd.tseries.offsets.DateOffset(days=np.random.randint(0,20))
        
        if now==admission:
            now += pd.tseries.offsets.DateOffset(hours=np.random.randint(0,24))
            
        times = pd.date_range(admission, now, freq='H')
        
        data = pd.DataFrame()
        data['time'] = pd.Series([ti + pd.tseries.offsets.DateOffset(minutes=np.random.randint(0,60)) for ti in times])
        for i, (mean, std) in enumerate(interventions_attributes):
            data[self.name + '_%d' %i] = std*np.asarray([max(0,((500-i)/500.)**2) for i in range(len(data.time))]) * np.random.randn(len(data.time)) + mean*np.asarray([max(0,(500-i)/500.) for i in range(len(data.time))])
            
        if self.non_neg:
            for col in data.columns:
                if col!='time':
                    data[col] = data[col].abs()
                    
        ## then add holes based on frequency
        for i,col in enumerate(data.columns[1:]):
            p = column[i]
            mask = [1 if np.random.uniform()<p else np.nan for i in range(len(data.time))]
            data[col] *= mask
            
        ## then collapse into a single time series (with preference)
        for i in range(len(data.columns)-2):
            colA = data.columns[-2 - (i*1)]
            colB = data.columns[-1 - (i*1)]
            data[colA].fillna(data[colB], inplace=True)
        
        self.start = data.time.min()
        self.end = data.time.max()
               
        return data[['time', self.name + '_0']].rename(columns={self.name + '_0' : self.name}).dropna()
    
    def get_most_recent_value(self, time=None):
        
        if self.df.empty:
            return None
        elif time==None:
            return tuple(self.df.iloc[-1])
        else:
            return self.df.loc[self.df.time <= time].iloc[-1]
    
    def get_worst_value(self, start=None, end=None, metric_func=None):
        
        if self.df.empty:
            return None

        start = self.start if start is None else start
        end = self.end if end is None else end
        data = self.df.loc[(self.df.time >= start) & (self.df.time <= end)]
        
        if data.empty:
            return None
        
        name = self.name        
        if metric_func==None:
            return data.loc[data.iloc[::-1][name].idxmax()]
        else:
            data.loc[:,'metric'] = data[name].apply(metric_func)
            return data.loc[data.iloc[::-1].metric.idxmax()][['time', name]]
            
    
    def get_series(self, start=None, end=None):
                
        if self.df.empty:
            return None

        start = self.start if start is None else start
        end = self.end if end is None else end
        return self.df.loc[(self.df.time >= start) & (self.df.time <= end)]
        

    def get_delta(self, time=None):
                
        if self.df.empty:
            return None

        end = self.end if time is None else time
        data = self.df.loc[self.df.time <= end]
        return data[self.name].iloc[-1] - data[self.name].iloc[-2]
        
    
    def str_time_prop(self, start, end, format, prop):
        stime = time.mktime(time.strptime(start, format))
        etime = time.mktime(time.strptime(end, format))
        ptime = stime + prop * (etime - stime)
        return time.strftime(format, time.localtime(ptime))
    
    def random_date(self, start, end, prop, selected_format = '%Y-%m-%d %H:%M:%S'):
        return parse(self.str_time_prop(start, end, selected_format, prop)).strftime(selected_format)
        
    
class Icca_Intervention(implements(I_Intervention)):
    
    def __init__(self, interventions, attributes, columns, name, encounterId, tables):

        self.name = name
        self.start = None
        self.end = None
        self.encounterId = encounterId
        self.tables = tables
        self.df = self.populate(zip(interventions, attributes), columns)
        
    def populate(self, interventions_attributes, column):
        ''' interventions_attributes is a list of tuples '''
        
        data = []
        for i,(inter,attr) in enumerate(interventions_attributes):
            sql = """SELECT P.chartTime as time, P.%s
                FROM %s P
                INNER JOIN D_Intervention D
                ON P.interventionId=D.interventionId
                INNER JOIN D_Attribute DA
                ON P.attributeId=DA.attributeId
                WHERE P.encounterId=%d AND D.interventionId=%d AND DA.attributeId=%d
                """ %(column[i], self.tables[i], self.encounterId, inter, attr)
            data.append(icca_query(sql))
        
        df = data[0]
        for d in data[1:]:
            df = pd.merge_ordered(df,d, how='outer', on='time')
            cols = [c for c in df.columns if c!='time']
            colr = {col : 'col%d' %i for i,col in enumerate(cols)}
            df.rename(columns=colr, inplace=True)
            
        cols = [c for c in df.columns if c!='time']
        df = df[['time'] + cols]
        df.drop_duplicates(inplace=True)
        
        #print(df.columns)
        #df.reset_index(inplace=True, drop=True)
        ## then collapse into a single time series (with preference)
        for i in range(len(df.columns)-2):
            colA = df.columns[-2 - (i*1)]
            colB = df.columns[-1 - (i*1)]
            df[colA].fillna(df[colB], inplace=True)
        
        cols = df.columns[0:2]
        df = df.loc[:,cols]
        df.rename(columns={cols[1] : self.name}, inplace=True)
        
        ## Check for entires like '<5' or >5 and fix... (could be present in other string types)
        #if self.name = 'Bilirubin':
        
        df[self.name] = pd.to_numeric(df[self.name], errors='coerce')
        df.dropna(inplace=True)
        df = df.sort_values(by='time')
        
        if self.name=='FiO2':
            df[self.name] /= float(100)
        
        #print(self.name)
        #print(df)
        
        self.start = df.time.min()
        self.end = df.time.max()
               
        return df
    
    def get_most_recent_value(self, time=None):
        
        if self.df.empty:
            return None
        elif time==None:
            return tuple(self.df.iloc[-1])
        else:
            return self.df.loc[self.df.time <= time].iloc[-1]
    
    def get_worst_value(self, start=None, end=None, metric_func=None):
        
        if self.df.empty:
            return None

        start = self.start if start is None else start
        end = self.end if end is None else end
        data = self.df.loc[(self.df.time >= start) & (self.df.time <= end)]
        
        if data.empty:
            return None
        
        name = self.name        
        if metric_func==None:
            return data.loc[data.iloc[::-1][name].idxmax()]
        else:
            data.loc[:,'metric'] = data[name].apply(metric_func)
            return data.loc[data.iloc[::-1].metric.idxmax()][['time', name]]
            
    
    def get_series(self, start=None, end=None):
                
        if self.df.empty:
            return None

        start = self.start if start is None else start
        end = self.end if end is None else end
        return self.df.loc[(self.df.time >= start) & (self.df.time <= end)]
        

    def get_delta(self, time=None):
                
        if self.df.empty:
            return None

        end = self.end if time is None else time
        data = self.df.loc[self.df.time <= end]
        return data[self.name].iloc[-1] - data[self.name].iloc[-2]
    
    
class Intervention_Factory():
    
    def __init__(self, dummy=True, encounterId=None):
        
        self.dummy = dummy
        self.mapping = DUMMY_MAPPING if self.dummy else MAPPING 
        self.encounterId = encounterId
        
    def get(self, intervention):
        params = self.mapping[intervention]
        
        if self.dummy:
            return Dummy_Intervention(params['interventionIds'],
                                              params['attributeIds'],
                                              params['column'],
                                              intervention)
        else:
            return Icca_Intervention(params['interventionIds'],
                                              params['attributeIds'],
                                              params['column'],
                                              intervention, 
                                              self.encounterId,
                                              params['table'])
            
    
class Sofa_Score():
    ## At the moment this sets component to zero is variable not recorded during previous 24 hours
    ## Also, this takes worst FiO2 and worst PaO2 seaprately.
    ## Defines mechanically ventilated as ANY peep in last 24 hours
    
    def __init__(self, factory, time=None, verbose=False):

        self.factory = factory
        self.interventions = {'GCS' : self.factory.get('GCS'),
                              'MAP' : self.factory.get('MAP'),
                              'Adrenaline' : self.factory.get('Adrenaline'),
                              'Noradrenaline' : self.factory.get('Noradrenaline'),
                              'Dobutamine' : self.factory.get('Dobutamine'),
                              'Dopamine' : self.factory.get('Dopamine'),
                              'Bilirubin' : self.factory.get('Bilirubin'),
                              'Platelets' : self.factory.get('Platelets'),
                              'Creatinine' : self.factory.get('Creatinine'),
                              'PEEP' : self.factory.get('PEEP'),
                              'FiO2' : self.factory.get('FiO2'),
                              'PO2' : self.factory.get('PO2')}
        
        max_time = np.max(pd.Series([self.interventions[key].df.time.max() for key in self.interventions]).dropna())
        self.time = max_time if time is None else time
        self.nervous = self.calculate_nervous()
        self.cardio =  self.calculate_cardio()
        self.liver =  self.calculate_liver()
        self.coagulation =  self.calculate_coagulation()
        self.kidneys =  self.calculate_kidneys()
        self.respiratory =  self.calculate_respiratory()
        
        self.score = np.sum([self.nervous, self.cardio, self.liver, 
                            self.coagulation, self.kidneys, self.respiratory])
        
        print("Nervous: ", self.nervous)
        print("Cardio: ",self.cardio)
        print("Liver: ",self.liver)
        print("Coag: ",self.coagulation)
        print("Kidney: ",self.kidneys)
        print("Resp: ",self.respiratory)
        print("Total score = ", self.score)
        
    def calculate_nervous(self):
        gcs = self.interventions['GCS']
        worst = gcs.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
    
        nervous = 0
        if worst is not None:
            val = worst.GCS
            if (val<=14) & (val>=13):
                nervous = 1
            elif (val<=12) & (val>=10):
                nervous = 2
            elif (val<=9) & (val>=6):
                nervous = 3
            elif (val<6):
                nervous = 4
        return nervous
        
    def calculate_cardio(self):
        mabp = self.interventions['MAP']
        worst = mabp.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
        
        cardio = 0
        if worst is not None:
            val = worst.MAP
            if val < 70:
                cardio = 1
                
        adr = self.interventions['Adrenaline']
        worst_adr = adr.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
        nor = self.interventions['Noradrenaline']
        worst_nor = nor.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
        dob = self.interventions['Dobutamine']
        worst_dob = dob.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
        dop = self.interventions['Dopamine']
        worst_dop = dop.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)  
        
        vaso0, vaso1, vaso2, vaso3 = 0,0,0,0
        if worst_adr is not None:
            val = worst_adr.Adrenaline
            if val <= 0.1:
                vaso0 = 3
            else:
                vaso0 = 4
                
        if worst_nor is not None:
            val = worst_nor.Noradrenaline
            if val <= 0.1:
                vaso1 = 3
            else:
                vaso1 = 4
                
        if worst_dob is not None:
            vaso2 = 2
            
        if worst_dop is not None:
            val = worst_dop.Dopamine
            if val <= 5:
                vaso3 = 2
            elif val > 15:
                vaso3 = 4
            else:
                vaso3 = 3
        
        cardio = max(cardio,vaso0,vaso1,vaso2,vaso3)
        return cardio
    
    def calculate_liver(self):
        bili = self.interventions['Bilirubin']
        worst = bili.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time)
    
        liver = 0
        if worst is not None:
            val = worst.Bilirubin
            if (val<33) & (val>=20):
                liver = 1
            elif (val<102) & (val>=33):
                liver = 2
            elif (val<12.0) & (val>=102):
                liver = 3
            elif val>=204:
                liver = 4
        return liver
    
    def calculate_coagulation(self):
        plat = self.interventions['Platelets']
        worst = plat.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
    
        coag = 0
        if worst is not None:
            val = worst.Platelets
            if (val<150) & (val>=100):
                coag = 1
            elif (val<100) & (val>=50):
                coag = 2
            elif (val<50) & (val>=20):
                coag = 3
            elif (val<20):
                coag = 4
        return coag
    
    def calculate_kidneys(self):
        creat = self.interventions['Creatinine']
        worst = creat.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time)
    
        kidneys = 0
        if worst is not None:
            val = worst.Creatinine
            if (val<171) & (val>=110):
                kidneys = 1
            elif (val<300) & (val>=171):
                kidneys = 2
            elif (val<5.0) & (val>=300):
                kidneys = 3
            elif val>=440:
                kidneys = 4
        return kidneys
    
    def calculate_respiratory(self):
        fio2 = self.interventions['FiO2']
        worst_fio2 = fio2.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time)
        
        po2 = self.interventions['PO2']
        worst_po2 = po2.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
    
        peep = self.interventions['PEEP']
        worst_peep = peep.get_worst_value(self.time - pd.tseries.offsets.DateOffset(hours=24), self.time, np.min)
        if worst_peep is not None:
            mechvent = True
        else:
            mechvent = False
        
        respiratory = 0    
        if (worst_fio2 is None) or (worst_po2 is None):
            return respiratory
        
        val = 7.50062 * worst_po2.PO2 / float(worst_fio2.FiO2)
    
        if (val<=400) & (val>300):
            respiratory = 1
        elif (val<=300):
            respiratory = 2
            
        if (val<=100) & mechvent:
            respiratory = 4
        elif (val<=200) & mechvent:
                respiratory = 3
        return respiratory
    

if __name__=='__main__':
    
    import matplotlib.pyplot as plt
    DUMMY = False
    
    sql = 'SELECT encounterId, clinicalUnitId FROM PtCensus WHERE outTime is null and clinicalUnitId=5'
    patients = icca_query(sql)
    eid = patients.iloc[np.random.randint(0,len(patients))].encounterId
    
    
    factory = Intervention_Factory(dummy=DUMMY, encounterId=eid)
    sofa = Sofa_Score(factory, verbose=True)
    
    plt.figure(figsize=(20,20))
    for i,key in enumerate(sofa.interventions):
        plt.subplot(4,3,i+1)
        series = sofa.interventions[key].get_series()
        if series is not None:
            plt.plot(series['time'], series[key], '+-')      
            #plt.title(key)
            plt.xlabel("time")
            plt.ylabel(key)
    plt.tight_layout()
    plt.show()
    
    print('EncounterId = ' + str(eid))
        
    
    