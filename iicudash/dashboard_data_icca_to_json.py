from helper import icca_query
import pandas as pd

if __name__=='__main__':
#    
#    df_a = pd.read_excel('COVID_interventions_attributes.xlsx', sheet_name='PtAssessment')
#    #print(df)
#    
#    sql = """SELECT P.encounterId as encounterId, P.chartTime, DI.longLabel, DA.shortLabel, P.valueNumber, P.valueString, DI.interventionId as interventionId, DA.attributeId as attributeId FROM PtAssessment P
#    INNER JOIN D_Intervention DI
#    ON P.interventionId=DI.interventionId 
#    INNER JOIN D_Attribute DA
#    ON P.attributeId=DA.attributeId
#    WHERE P.encounterId in (SELECT encounterId from PtBedStay where outTime is null and clinicalUnitId in (5,8)) AND DI.interventionId in 
#    """ + str(tuple(df_a.interventionId)) + " AND DA.attributeId in " + str(tuple(df_a.attributeId))
#    
#    ptassessment_results = icca_query(sql)
    
    #if ptassessment_results is not None:
    #    print(ptassessment_results)

    df_l = pd.read_excel('COVID_interventions_attributes.xlsx', sheet_name='PtLabresult')
    sql = """SELECT P.encounterId as encounterId, P.chartTime, DI.longLabel, DA.shortLabel, P.valueNumber, P.valueString, DI.interventionId as interventionId, DA.attributeId as attributeId FROM PtLabResult P
    INNER JOIN D_Intervention DI
    ON P.interventionId=DI.interventionId 
    INNER JOIN D_Attribute DA
    ON P.attributeId=DA.attributeId
    WHERE P.encounterId in (SELECT encounterId from PtBedStay where outTime is null and clinicalUnitId in (5,8)) AND DI.interventionId in 
    """ + str(tuple(df_l.interventionId)) + " AND DA.attributeId in " + str(tuple(df_l.attributeId))
    
    ptlabresult_results = icca_query(sql)
    
#    
#    sql = "SELECT * FROM UHB.SOFA_python"
#    sofa = icca_query(sql, db='CISReportingDB')
#    #print(sofa)
    
    sql = 'SELECT bedLabel, encounterId FROM PtBedStay WHERE outTime is null and clinicalUnitId in (5,8)'
    beds = icca_query(sql)
    
    # Need to collapse columns based on priority
    # Need to combine FiO2 across PtAssessment and PtLabResults dataframes
    # Need to compute Ventilator parameters from Kieron/Stefan formulae
    # Need to work out what to do about 'No Bed' patients - some are valid, some are not?
    # Need to add valueNumber or valueString indicator to excel file. 
    
    # see @Select row by max value in group (link in jupyter notebook)@
    
    patient_data = dict()
    
    for bed,encounter in zip(beds.bedLabel,beds.encounterId):
        patient_data[bed] = dict()
        
        patient_labs = ptlabresult_results.loc[ptlabresult_results.encounterId==encounter]
        patient_labs = patient_labs.merge(df_l, on=['interventionId', 'attributeId'], how='inner')
        
        patient_labs = patient_labs.loc[patient_labs.reset_index().groupby('vname')['priority'].idxmax()]
        
        for v in df_l.vname:
            patient_data[bed][v] = patient_labs.loc[patient_labs.vname==v].valueNumber
           
            
    print(patient_data)
    
            