from helper import icca_query
import pandas as pd
import json

if __name__=='__main__':
#   
    #with open('patient_data_schema.json', 'r') as read_file:
    with open('patient_data.json', 'r') as read_file:
        schema = json.load(read_file) 
    
    # This is to store the data that will be saved in the new json file for display on the summary table view of the dashboard
    data_dict = {'parameters': [], 'values': []}

    # Loop through and get the interventions and attributes that will be selected from each database table, then query the table:
    #   Note: when this script is scheduled a timeout setting will be added. If the script times out the old json data will be used.
    database_tables = ['PtAssessment', 'PtLabResult', 'PtDemographic']
    interventions_attributes = dict()
    icca_query_results = dict()
    
    for table in database_tables:
        interventions_attributes[table] = pd.read_excel('COVID_interventions_attributes.xlsx', sheet_name=table)
        sql = """SELECT P.encounterId as encounterId, P.chartTime as chartTime, DI.longLabel, DA.shortLabel, P.valueNumber, P.valueString, DI.interventionId as interventionId, DA.attributeId as attributeId 
        FROM
        """ + table +  """ P
        INNER JOIN D_Intervention DI
        ON P.interventionId=DI.interventionId 
        INNER JOIN D_Attribute DA
        ON P.attributeId=DA.attributeId
        WHERE P.encounterId in (SELECT encounterId from PtBedStay where outTime is null and clinicalUnitId in (5,8)) AND DI.interventionId in 
        """ + str(tuple(interventions_attributes[table].interventionId)) + " AND DA.attributeId in " + str(tuple(interventions_attributes[table].attributeId))
        
        icca_query_results[table] = icca_query(sql)
#    
#
#    df_l = pd.read_excel('COVID_interventions_attributes.xlsx', sheet_name='PtLabresult')
#    sql = """SELECT P.encounterId as encounterId, P.chartTime, DI.longLabel, DA.shortLabel, P.valueNumber, P.valueString, DI.interventionId as interventionId, DA.attributeId as attributeId FROM PtLabResult P
#    INNER JOIN D_Intervention DI
#    ON P.interventionId=DI.interventionId 
#    INNER JOIN D_Attribute DA
#    ON P.attributeId=DA.attributeId
#    WHERE P.encounterId in (SELECT encounterId from PtBedStay where outTime is null and clinicalUnitId in (5,8)) AND DI.interventionId in 
#    """ + str(tuple(df_l.interventionId)) + " AND DA.attributeId in " + str(tuple(df_l.attributeId))
#    
#    ptlabresult_results = icca_query(sql)
    
    
    sql = "SELECT * FROM UHB.SOFA_python"
    icca_query_results['Sofa'] = icca_query(sql, db='CISReportingDB')
    
    sql = 'SELECT bedLabel, encounterId FROM PtBedStay WHERE outTime is null and clinicalUnitId in (5,8)'
    icca_query_results['Beds'] = icca_query(sql)
    
    # Should 'derived' have capital letter (in schema)
    # Refactor to use classes to avoid passing around vaiables between functions e.g. icca_query_results etc..
    # Need to combine FiO2 across PtAssessment and PtLabResults dataframes
    # Need to compute Ventilator parameters from Kieron/Stefan formulae
    # Need to work out what to do about 'No Bed' patients - some are valid, some are not?
    # Need to add valueNumber or valueString indicator to excel file. 
    # Need to set time out when scheduling this on server...if timeout, revert to old josn?
    
    # need a clever way of looping over variables that are in the schema, working out whether to extract them from PtAssessment etc, or compute them,and if they are stored in valueString or valueNumber, and how to apply condition formatting, and get previous value 
    
    # need a celever way of defining stylings..
    ## Need two levels of script/task for the timeout scheduling? (otheriwse might timeout during write of new json and corrupt the file -> add if corrupt fn to front end?)
    
    def get_derived_value(parameter):
        return None
    
    def get_parameter_value_dict(parameter, bed_data_points, patient_labs, patient_assess):
        
        if parameter['type'] == 'PtLabResult':
            
            value = patient_labs.loc[patient_labs.vname==parameter['name']].valueNumber
            value = value.iloc[0] if len(value)>0 else None
                
        elif parameter['type'] == 'PtAssessment':
            
            value = patient_assess.loc[patient_assess.vname==parameter['name']].valueNumber
            value = value.iloc[0] if len(value)>0 else None
        
        elif parameter['type'] == 'derived':
            value = get_derived_value(parameter)
        else:
            value = None
            
        # This doesn't work - need to get the list of data points corresponding to this bed...
        names = [point['name'] for point in bed_data_points] if bed_data_points is not None else []    
        previous = bed_data_points[names.index(parameter['name'])]['value'] if parameter['name'] in names else None
            
        
        return {'name': parameter['name'],
                   'value': value,
                   'style': 'normal', # NEED TO DEFINE STYLING (IN EXCEL?)
                   'previous': previous
                   }
        
        
    def get_highest_priority_records_for_this_encounter(encounterId, icca_query_results, interventions_attributes, table):
        # There may be multiple intervention and attributes for the same parameter (e.g. heart rate encoded multiple way).
        # This function takes the most recent record and then, if there are multiple records at the same hour, 
        #  takes the value with the highest 'priorty' (in the excel table)
        
        patient_results = icca_query_results[table].loc[icca_query_results[table].encounterId==encounter]
     
        patient_results = patient_results.merge(interventions_attributes[table], 
                                                on=['interventionId', 'attributeId'], how='inner')
    
        patient_results = patient_results.loc[patient_results.reset_index().sort_values(by=['chartTime', 'priority'], ascending=[False,True]).groupby('vname')['chartTime'].idxmax()]
        
        return patient_results
    
    
    def build_bed_value_dict(bedId, encounterId, schema):
        bvd = {'bedId': bedId, 'dataPoints': []}
    
        patient_labs = get_highest_priority_records_for_this_encounter(encounterId, icca_query_results, interventions_attributes, 'PtLabResult')
        patient_assess = get_highest_priority_records_for_this_encounter(encounterId, icca_query_results, interventions_attributes, 'PtAssessment')
#        patient_labs = ptlabresult_results.loc[ptlabresult_results.encounterId==encounter]
#        patient_labs = patient_labs.merge(df_l, on=['interventionId', 'attributeId'], how='inner')
#        patient_labs = patient_labs.loc[patient_labs.reset_index().groupby('vname')['priority'].idxmax()]
#        
#        patient_assess = ptassessment_results.loc[ptassessment_results.encounterId==encounter]
#        patient_assess = patient_assess.merge(df_a, on=['interventionId', 'attributeId'], how='inner')
#        patient_assess = patient_assess.loc[patient_assess.reset_index().groupby('vname')['priority'].idxmax()]
        
        beds = [value['bedId'] for value in schema['values']]
        bed_data_points = schema['values'][beds.index(bedId)]['dataPoints'] if bedId in beds else None
        
        for parameter in schema['parameters']:
            
            bvd['dataPoints'].append(get_parameter_value_dict(parameter, bed_data_points, patient_labs, patient_assess)) 
            
        return bvd
       
    
    for bed,encounter in zip(icca_query_results['Beds'].bedLabel,icca_query_results['Beds'].encounterId):
        data_dict['values'].append(build_bed_value_dict(bed, encounter, schema))
         

    data_dict['parameters'] = schema['parameters']
    with open('patient_data.json', 'w') as outfile:
        json.dump(data_dict, outfile)
    
            