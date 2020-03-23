import pandas as pd
import json
import matplotlib.pyplot as plt
import io
import os
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


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
patient = None


@bp.route('/')
@login_required
def index():
    global df, nrfd
    if current_app.config['PATIENTDATA']=='dummy':
        patientData = DummyPatientData()
    elif current_app.config['PATIENTDATA']=='icca':
        patientData = IccaPatientData()

    df = patientData.returnPatientDf()
    nrfd = {bed:False for bed in df['Bed']}
    table_d = json.loads(df.to_json(orient='index'))
    columns = df.columns
                
    return render_template('tables/table1.html', columns=columns, 
                            table_data=table_d)

@bp.route('/patient_view')
@login_required
def patient_view():
    global df, patient
    #df_selected = df
    img = io.BytesIO()
    #fig = Figure()
    
    plt.plot([1,2,3,4,5,6,7,8,9,10,11,12], [24,22,22,23,19,20,17,15,17,13,10,10])
    plt.title("SOFA score during ICU admission")
    plt.xlabel("day of admission")
    plt.ylabel("SOFA score")
    plt.ylim([0,24])#
    plt.xlim([1,12])
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    #plot_url = base64.b64encode(img.getvalue())
    plot_url = base64.b64encode(img.getvalue()).decode()
    #pngImage = io.BytesIO()
    #plt.savefig(bytes_image, format='png')
    #bytes_image.seek(0)
    #FigureCanvas(fig).print_png(pngImage)
    
    # Encode PNG image to base64 string
    #pngImageB64String = "data:image/png;base64,"
    #pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    

    return render_template('tables/patient_view.html', image='static/images/new_plot.png', patient=patient, plot_url=plot_url)
    

@bp.route('/logout_msg')
def finish():
    logout()
    return render_template('tables/logout_msg.html')

@bp.route('/back_to_dashboard', methods=('GET', 'POST'))
def back_to_dashboard():
    return redirect(url_for('tables.index'))

@bp.route('/ward_view', methods=('GET', 'POST'))
def ward_view():
    return render_template('tables/ward_view.html')

@bp.route('/select_patient', methods=('GET', 'POST'))
@login_required
def select_patient():
    if request.method == 'POST':
        global df, patient
        #patient = request.form.get('selectedPatient')
        patient = request.form['selectedPatient']
        print(patient)
    return redirect(url_for('tables.patient_view'))

@bp.route('/submit_table2', methods=('GET', 'POST'))
@login_required
def submit_table2():
    if request.method == 'POST':
        global df, nrfd
        for bed in df['Bed']:    
            if not nrfd[bed]:
                rank = request.form[bed]
                print("%s : %s" %(bed,rank))
        
    return redirect(url_for('tables.finish'))
