import pandas as pd
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from rankapp.auth import login_required, logout
from rankapp.db import get_db
from rankapp.patient_db import *

bp = Blueprint('tables', __name__)

## using global variables for table data
##   A class would be more elegant but requires url endpoint rules
##   rather than decorators as currently used here.
df = pd.DataFrame()
nrfd = dict()


@bp.route('/')
@login_required
def index():
    global df
    if current_app.config['PATIENTDATA']=='dummy':
        patientData = DummyPatientData()
    elif current_app.config['PATIENTDATA']=='icca':
        patientData = IccaPatientData()

    df = patientData.returnPatientDf()
    nrfd = {name:False for name in df['Name']}
    table_d = json.loads(df.to_json(orient='index'))
    columns = df.columns
                
    return render_template('tables/table1.html', columns=columns, 
                            table_data=table_d)

@bp.route('/table2')
@login_required
def table2():
    global df
    drop_rows = [i for i,name in enumerate(df['Name']) if nrfd[name]] 
    df_selected = df.drop(drop_rows, axis=0)
    df_selected['Rank'] = [i for i in range(len(df_selected))]
    df_selected = df_selected[['Rank', 'Name', 'Bed', 'T_number', 'Age', 'Admission']]
    table_d = json.loads(df_selected.to_json(orient='index'))
    columns = df_selected.columns
            
    return render_template('tables/table2.html', columns=columns, 
                            table_data=table_d)

@bp.route('/logout_msg')
def finish():
    logout()
    return render_template('tables/logout_msg.html')

@bp.route('/submit_table1', methods=('GET', 'POST'))
@login_required
def submit_table1():
    if request.method == 'POST':
        global df, nrfd
        for name in df['Name']:    
            selected = request.form[name]
            if selected=="selected":
                nrfd[name] = True
            elif selected=="unselected":
                nrfd[name] = False
       
        print(nrfd)
    return redirect(url_for('tables.table2'))

@bp.route('/submit_table2', methods=('GET', 'POST'))
@login_required
def submit_table2():
    if request.method == 'POST':
        global df, nrfd
        for name in df['Name']:    
            if not nrfd[name]:
                rank = request.form[name]
                print("%s : %s" %(name,rank))
        
    return redirect(url_for('tables.finish'))
