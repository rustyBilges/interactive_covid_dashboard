from helper import icca_query
import pandas as pd
import json

if __name__=='__main__':
   
#    with open('patient_data_schema.json', 'r') as read_file:
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

    sql = "SELECT * FROM UHB.SOFA_python"
    icca_query_results['Sofa'] = icca_query(sql, db='CISReportingDB')
    
    sql = 'SELECT bedLabel, encounterId FROM PtBedStay WHERE outTime is null and clinicalUnitId in (5,8)'
    icca_query_results['Beds'] = icca_query(sql)
    
    # Should 'derived' have capital letter (in schema)
    # Refactor to use classes to avoid passing around vaiables between functions e.g. icca_query_results etc..
    # Need to combine FiO2 across PtAssessment and PtLabResults dataframes
    # Need to compute Ventilator parameters from Kieron/Stefan formulae
    # Need to work out what to do about 'No Bed' patients - some are valid, some are not?
    # Need to set time out when scheduling this on server...if timeout, revert to old josn?
    
    # need a clever way of defining stylings..
    
    ## Need two levels of script/task for the timeout scheduling? (otheriwse might timeout during write of new json and corrupt the file -> add if corrupt fn to front end?)
    # Should go through list of intervention and attibutes with a doctor (Kieron) to check prioities and definitions and units.
    
    def get_highest_priority_records_for_this_encounter(encounterId, icca_query_results, interventions_attributes, table):
        # There may be multiple intervention and attributes for the same parameter (e.g. heart rate encoded multiple way).
        # This function takes the most recent record and then, if there are multiple records at the same hour, 
        #  takes the value with the highest 'priorty' (in the excel table).
        #  Note: it may be better practice to discretise time?
        
        patient_results = icca_query_results[table].loc[icca_query_results[table].encounterId==encounter]
     
        patient_results = patient_results.merge(interventions_attributes[table], 
                                                on=['interventionId', 'attributeId'], how='inner')
    
        patient_results = patient_results.loc[patient_results.reset_index().sort_values(by=['chartTime', 'priority'], ascending=[False,True]).groupby('vname')['chartTime'].idxmax()]
        return patient_results
    
    
    def get_variable_value(patient_results, table, variable):
        value = patient_results[table].loc[patient_results[table].vname==variable]
        
        if len(value)>0:
            value = value.iloc[0]
            value = value[value.column]
        else:
            value = None
        return value
    
    def get_derived_value(parameter, patient_results):
        # Possibly this should use an abstract base class pattern?
        name = parameter['name']
        value = None
        
        if  name == 'FiO2':
            value = patient_results['PtAssessment'].loc[patient_results['PtAssessment'].vname==name]   # Refactor to make a function for this!!!!
            value = value.append(patient_results['PtLabResult'].loc[patient_results['PtLabResult'].vname==name], sort=False)
            value = value.loc[value.chartTime.idxmax()] if len(value)>0 else None
            value = value[value.column] if value is not None else None
            
        elif name == 'P/F Ratio':
            value = get_variable_value(patient_results, 'PtAssessment', name)
            if value is None:
                # If ratio not recorded, try to compute from individuals records...
                # CAREFUL WITH UNITS WHEN IMPLEMENTING THIS!
                value = None
        
        elif name == 'Ventilator ratio':
            
            etco2 = get_variable_value(patient_results, 'PtAssessment','EtCO2')
            paco2 = get_variable_value(patient_results, 'PtLabResult','PaCO2')
            if etco2 is not None and paco2 is not None:
                value = (paco2 - etco2)/float(paco2)
          
        else:
            value = None
        
        return value
    
#    How to make this nice and concise?!
    def get_style(value, parameter_name):
        
#        styles = ['normal', 'good', 'warning', 'bad', 'invalid', 'inactive']
        high_means_bad_parameters = ['VT/kg', 'etc...']
        lb = 6.0
        ub = 8.0
        
        if value is None:
            return 'inactive'
        
        elif parameter_name in high_means_bad_parameters:
            
            if value > ub:
                return 'bad'
            elif value > lb:
                return 'warning'
            else:
                return 'normal'
            
        else:
            return 'normal'
    
    
    def get_parameter_value_dict(parameter, bed_data_points, patient_results, interventions_attributes):
        
        param_type = parameter['type']
        
        if param_type in database_tables:
            value = get_variable_value(patient_results, param_type, parameter['name'])
            
        elif param_type == 'derived':
            value = get_derived_value(parameter, patient_results)
        
        else:
            value = None
            
        names = [point['name'] for point in bed_data_points] if bed_data_points is not None else []    
        previous = bed_data_points[names.index(parameter['name'])]['value'] if parameter['name'] in names else None
        
        return {'name': parameter['name'],
                   'value': value,
                   'style': get_style(value,  parameter['name']
                   ),
                   'previous': previous
                   }    
        
    
    def build_bed_value_dict(bedId, encounterId, schema):
        bvd = {'bedId': bedId, 'dataPoints': []}
    
        patient_results = dict()
        for table in database_tables:
            patient_results[table] = get_highest_priority_records_for_this_encounter(encounterId, icca_query_results, interventions_attributes, table)

        beds = [value['bedId'] for value in schema['values']]
        bed_data_points = schema['values'][beds.index(bedId)]['dataPoints'] if bedId in beds else None
        
        for parameter in schema['parameters']:
            bvd['dataPoints'].append(get_parameter_value_dict(parameter, bed_data_points, patient_results, interventions_attributes)) 
            
        return bvd
       
    
    for bed,encounter in zip(icca_query_results['Beds'].bedLabel,icca_query_results['Beds'].encounterId):
        data_dict['values'].append(build_bed_value_dict(bed, encounter, schema))
         

    data_dict['parameters'] = schema['parameters']
    with open('patient_data.json', 'w') as outfile:
        json.dump(data_dict, outfile)
    
            