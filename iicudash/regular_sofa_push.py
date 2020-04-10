# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 10:16:38 2020

@author: mcwilliamschr.admin
"""
import pyodbc
from helper import *

if __name__=='__main__':
    
    def write_to_ubhnt175(sofa, eid, tnum, bed):
        time = sofa.time.strftime('%Y-%m-%d %H:%M:%S')
        print(time)
        
        server = "ubhnt175.ubht.nhs.uk"
        database = "CISReportingDB"
        tc ="yes"  
    
        cnxn = pyodbc.connect('trusted_connection='+tc+';DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
        cursor = cnxn.cursor()
    
        cursor.execute("""INSERT INTO UHB.SOFA_python  
                       (chartTime, encounterId, sofa, nervous, cardio, respiratory, coagulation, liver, kidneys, bedLabel, lifeTimeNumber) 
                        VALUES (convert(datetime,'%s',20),%d,%d,%d,%d,%d,%d,%d,%d,'%s','%s')"""
                        %(time,int(eid),int(sofa.score),int(sofa.nervous),int(sofa.cardio),int(sofa.respiratory),int(sofa.coagulation), int(sofa.liver), int(sofa.kidneys),bed,tnum))    
        cnxn.commit()
        cursor.close()
        del cursor
        cnxn.close()
            
    
    sql = """SELECT P.encounterId as eid, P.bedLabel as bed, D.lifeTimeNumber as tnum
           FROM PtBedStay P INNER JOIN D_Encounter D 
           ON P.encounterId = D.encounterId
           WHERE P.outTime is null and clinicalUnitId in (5,8)"""
           
    data = icca_query(sql)
    print(data)
#   eid = patients.iloc[np.random.randint(0,len(patients))].encounterId
#    row = data.iloc[10]
    for ri,row in data.iterrows():
        if row.tnum[0]=='T':
            sofa = None
            
            try:
            
                factory = Intervention_Factory(dummy=False, encounterId=row.eid)
                sofa = Sofa_Score(factory)
            except:
                print('Could not calculate score for encounter %d in bed %s' %(row.eid,row.bed))
            if sofa is not None:
                try:
                    write_to_ubhnt175(sofa, row.eid, row.tnum, row.bed)
                except:
                    print('Could not write score to UHBNT175 for encounter %d in bed %s' %(row.eid,row.bed))
        else:
            print('Invalid LifeTimeNumber: %s' %row.tnum)
        
        
#            sofas = []
#            sofa = 0
#            for b,t in zip(beds,tnums):
#                sql = "SELECT B.encounterId FROM PtBedStay B INNER JOIN D_Encounter D ON B.encounterId=D.encounterId WHERE B.bedLabel='%s' and D.lifeTimeNumber='%s'" %(b,t)
#                _data = icca_query(sql)
#                if _data.empty:
#                    print('Warning: patient not found.')
#                    sofa = 0
#                else:
#                    eid = _data.iloc[0].encounterId
#                    try:
#                        factory = Intervention_Factory(dummy=False, encounterId=eid)     
#                        S = Sofa_Score(factory)
#                        sofa = S.score
#                    except:
#                        sofa = 0
#                sofas.append(sofa)
                

#    server = "ubhnt175.ubht.nhs.uk"
#    database = "CISReportingDB"
#    tc ="yes"  
#    
#    cnxn = pyodbc.connect('trusted_connection='+tc+';DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
#    cursor = cnxn.cursor()
#    
#    cursor.execute("""INSERT INTO UHB.SOFA_python 
#                   (chartTime, encounterId, sofa, nervous, cardio, respiratory, coagulation, liver, kidneys, bedLabel, lifeTimeNumber) VALUES (convert(datetime,'%s',20),%d,%d,%d,%d,%d,%d,%d,%d,'%s','%s')""" %('2000-04-24 12:04:32',3,3,3,3,3,3,3,3,'bed','tnum'))    
#    cnxn.commit()
#    cursor.close()
#    del cursor
#    cnxn.close()
            
 