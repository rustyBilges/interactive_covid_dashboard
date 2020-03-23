from interface import implements, Interface
import pandas as pd
import pyodbc
from flask import current_app

class I_PatientData(Interface):

    def returnPatientDf(self):
        pass

class DummyPatientData(implements(I_PatientData)):

    def __init__(self):

        self.df = pd.DataFrame()
        self.df['Bed'] = ['GICU 01','GICU 02','CICU 01','CICU 05','CICU 07','GICU 09','GICU 11','CICU 12','GICU 14','CICU 15']
        self.df['SOFA'] = [16, 5, 8, 17, 6, 18, 20, 5, 8, 7]
        self.df['VT_kg'] = ['6.0', '7.1', '8.0', '5.5', '6.2', '10.0', '11.0', '5.8', '7.2', '6.0']
        self.df['FiO2'] = ['0.5', '0.6', '0.4', '0.8', '0.7', '0.6', '0.7', '0.5', '0.8', '0.6' ]
        self.df['PEEP'] = ['5', '6', '10', '8', '7', '6', '7', '5', '8', '6' ]
        self.df['pH'] = ['0.5', '0.6', '0.4', '0.8', '0.7', '0.6', '0.7', '0.5', '0.8', '0.6' ]
        self.df['BE'] = ['0.5', '0.6', '0.4', '0.8', '0.7', '0.6', '0.7', '0.5', '0.8', '0.6' ]
        self.df['FB'] = ['500 (+1500)', '60 (+2000)', '400 (+500)', '500 (+1000)', '-70 (-1500)', '650 (+1000)', '-70 (-540)', '50 (+2000)', '-80 (+120)', '640 (+2300)' ]
        self.df['Pos'] = ['prone', 'supine', 'supine', 'prone', 'supine', 'prone', 'supine', 'supine', 'prone', 'supine']
        self.df['Norad'] = ['0', '0', '0.2', '0.3', '0', '0.1', '0.3', '0.1', '0', '0.4']
        self.df['COVID19'] = ['sent', 'pending', 'negative', 'positive', 'pending', 'sent', 'positive', 'positive', 'negative', 'pending']
        
    def returnPatientDf(self):
        return self.df

class IccaPatientData(implements(I_PatientData)):
## This class will get the current patients from ICCA using pyodbc:
    def __init__(self):

        self.df = pd.DataFrame()
        self.queryDatabase()

    def returnPatientDf(self):
        return self.df

    def queryDatabase(self):
        try:

            server = "ubhnt455.ubht.nhs.uk"
            database = "CISReportingDB"
            tc ="yes"  

            cnxn = pyodbc.connect('trusted_connection='+tc+';DRIVER={SQL Server};SERVER='+server+';DATABASE='+database)
            cursor = cnxn.cursor()

            cursor.execute("""SELECT TOP 23 D.firstName, D.lastName, D.lifeTimeNumber, DATEDIFF(hour, D.dateOfBirth, GETDATE())/8766 AS Age, B.bedLabel, CONVERT(date, P.inTime) 
               FROM PtCensus P
               INNER JOIN D_Encounter D
               ON P.encounterId=D.encounterId 
               INNER JOIN PtBedStay B
               ON P.encounterId=B.encounterId 
               WHERE P.clinicalUnitId=5 and P.outTime IS NULL and B.outTime IS NULL
               ORDER BY P.inTime desc;""")    

            names = []
            beds = []
            numbers = []
            ages = []
            admissions = []

            row = cursor.fetchone()
            while row:
                #print(row)
                names.append(row[0] + " " + row[1])
                beds.append(row[4])
                numbers.append(row[2])
                ages.append(row[3])
                admissions.append(row[5])

                row =cursor.fetchone()

            cursor.close()
            del cursor
            cnxn.close()

            self.df['Name'] = names
            self.df['Bed'] = beds
            self.df['T_number'] = numbers
            self.df['Age'] = ages
            self.df['Admission'] = admissions

        except:
            print("Error: Could not connect to database.")
