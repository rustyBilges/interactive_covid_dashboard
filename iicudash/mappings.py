#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 18:12:34 2020

@author: rustybilges
"""

MAPPING = dict()

DUMMY_MAPPING = {'GCS': {'interventionIds' : [10], 
                         'attributeIds' : [2], 
                         'column' : [0.8]},
                 'MAP': {'interventionIds' : [70, 60, 80], 
                         'attributeIds' : [5, 3, 9], 
                         'column' : [0.5, 0.4, 0.6]},
                 'Adrenaline': {'interventionIds' : [0.1, 0.05], 
                         'attributeIds' : [0.1, 0.3], 
                         'column' : [0.5, 0.4]},
                 'Noradrenaline': {'interventionIds' : [0.1, 0.05], 
                         'attributeIds' : [0.1, 0.3], 
                         'column' : [0.5, 0.4]},                                
                 'Dobutamine': {'interventionIds' : [0.1], 
                         'attributeIds' : [0.1], 
                         'column' : [0.5]},           
                 'Dopamine': {'interventionIds' : [0.1, 0.05], 
                         'attributeIds' : [0.1, 0.3], 
                         'column' : [0.5, 0.4]},                                
                 'Bilirubin': {'interventionIds' : [6.1], 
                         'attributeIds' : [2.1], 
                         'column' : [0.1]},
                 'Platelets': {'interventionIds' : [60], 
                         'attributeIds' : [10.0], 
                         'column' : [0.1]},
                 'Creatinine': {'interventionIds' : [2.0], 
                         'attributeIds' : [1.0], 
                         'column' : [0.2]},
                 'PEEP': {'interventionIds' : [5.0], 
                         'attributeIds' : [1.0], 
                         'column' : [0.8]},                                
                 'FiO2': {'interventionIds' : [5.0], 
                         'attributeIds' : [1.0], 
                         'column' : [0.8]},
                 'PO2': {'interventionIds' : [5.0], 
                         'attributeIds' : [1.0], 
                         'column' : [0.8]}}