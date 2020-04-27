from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import init_db
import json
import requests
from datetime import datetime, timedelta, date

bp = Blueprint('appoint', __name__, url_prefix='/appoint')

weekdays = ['Monday','Tuesday','Wednesday','Thursday',
            'Friday','Saturday','Sunday']

def get_next_byday(dayname, start_date=None):
    if start_date is None:
        start_date = datetime.today()
    day_num = start_date.weekday()
    day_num_target = weekdays.index(dayname)
    days_after = (7 + day_num_target - day_num) % 7
    if days_after == 0:
        days_after = 7
    target_date = start_date + timedelta(days = days_after)
    return target_date.date()

@bp.route('/search', methods=('GET', 'POST'))
@login_required
def search():
    db = init_db()
    error = None

    if request.method == 'POST':
        doctor_name = request.form['Doctor_name']
        symptom1 = request.form['Symptom1']
        symptom2 = request.form['Symptom2']
        symptom3 = request.form['Symptom3']

        symptoms = symptom1+','+symptom2+','+symptom3

        if doctor_name:
            return redirect(url_for('appoint.result', doctor_name=doctor_name, symptoms=symptoms, user_ID=session.get('user_id')))
        elif symptoms!='None,None,None':
            return redirect(url_for('appoint.result', doctor_name='*', symptoms=symptoms, user_ID=session.get('user_id')))
        else:
            error = 'Please type in a doctor\'s name or your symptoms to search'

        flash(error)

    syms_name = db.execute('SELECT name FROM symptoms').fetchall()

    return render_template('appoint/search.html', syms_name=syms_name)


@bp.route('/result/<user_ID>/<doctor_name>+<symptoms>', methods=('GET', 'POST'))
@login_required
def result(doctor_name, symptoms, user_ID):
    db = init_db()
    issue = []

    if doctor_name!='*':
        selected_doctors = db.execute('select * from (select * from doctor where name=(%s)) as T1 '
                                 'join (select doctor_id as id, ROUND(AVG(rate),2) as avg, count(evaluation_record_id) from evaluation '
                                 'group by doctor_id) T2 on T1.doctor_id=T2.id '
                                 'order by avg desc, count desc', (doctor_name,)).fetchall()

    else:
        if symptoms:
            import re
            p = re.compile(r'[,]')
            syms = re.split(p, symptoms)
            sym_arr = []
            for sym in syms:
                sym_id = db.execute('SELECT id FROM symptoms WHERE name=(%s)', (sym,)).fetchone()['id']
                sym_arr.append(sym_id)

            symptoms = sym_arr
            url = "https://priaid-symptom-checker-v1.p.rapidapi.com/diagnosis"

            p_info = db.execute('SELECT personal_information.* '
                                'FROM personal_information, patient '
                                'WHERE personal_information.patient_id=patient.patient_id AND patient.user_id=(%s)',
                                (session.get('user_id'),)).fetchone()
            gender = p_info['gender']
            yob = str(date.today().year - p_info['age'])
            querystring = {"symptoms": json.dumps(symptoms), "gender": gender, "year_of_birth": yob,
                           "language": "en-gb"}

            headers = {
                'x-rapidapi-host': "priaid-symptom-checker-v1.p.rapidapi.com",
                'x-rapidapi-key': "6a93fdec92mshd41a9d80e2f185bp185f6bjsn726d7dd0f858"
            }

            # get first-step diagnosis result
            response = requests.request("GET", url, headers=headers, params=querystring)
            results = json.loads(response.text)
            specialisation = []
            for item in results:
                issue.append({'name': item['Issue']['Name'], 'profname': item['Issue']['ProfName']})
                for spec in item['Specialisation']:
                    if spec['Name'] not in specialisation:
                        specialisation.append({'speicalisation': item['Specialisation'][0]['Name']})

            # look up for the best doctors of every specialisation
            selected_doctors = []
            for spec in specialisation:
                if spec['speicalisation'] == 'General practice':
                    doctors = db.execute('select * from doctor as T1 '
                                         'join (select doctor_id as id, ROUND(AVG(rate),2) as avg, count(evaluation_record_id) from evaluation '
                                         'group by doctor_id) T2 on T1.doctor_id=T2.id '
                                         'order by avg desc, count desc').fetchall()

                else:
                    doctors = db.execute('select * from (select * from doctor where specialization=(%s)) as T1 '
                                         'join (select doctor_id as id, ROUND(AVG(rate),2) as avg, count(evaluation_record_id) from evaluation '
                                         'group by doctor_id) T2 on T1.doctor_id=T2.id '
                                         'order by avg desc, count desc', (spec['speicalisation'],)).fetchall()

                if doctors:
                    for doctor in doctors:
                        if doctor not in selected_doctors:
                            selected_doctors.append(doctor)

            if selected_doctors == []:
                selected_doctors = None
        else:
            selected_doctors = None

    if issue:
        return render_template('appoint/result.html', user_ID=session.get('user_id'), doctors=selected_doctors, issue=issue)
    else:
        return render_template('appoint/result.html', user_ID=session.get('user_id'), doctors=selected_doctors, issue=None)


@bp.route('/make/<user_ID>/<doctor_ID>', methods=('GET', 'POST'))
@login_required
def make(user_ID, doctor_ID):
    db = init_db()
    error = None
    if_made = 0

    day = db.execute('SELECT availabletime FROM doctor WHERE doctor_id = (%s)', (doctor_ID,)).fetchone()['availabletime']
    appointmenttime = get_next_byday(day)

    appointment_id = 'a' + str(db.execute('SELECT count(*) FROM appoint').fetchone()['count']+1)
    patient_ID = db.execute('SELECT patient_id FROM patient WHERE user_id=(%s)', (user_ID,)).fetchone()['patient_id']
    doctor_name = db.execute('SELECT name FROM doctor WHERE doctor_id=(%s)', (doctor_ID,)).fetchone()['name']

    if db.execute('SELECT appoint.* FROM appoint, appointment WHERE appointment.appointmenttime = (%s) AND appoint.patient_id = (%s) AND '
                  'appoint.doctor_id = (%s) AND appointment.appointment_id = appoint.appointment_id',
                  (appointmenttime, patient_ID, doctor_ID)).fetchone() is not None:
        error = 'You have already made an appointment with Dr.' + doctor_name + ' on ' + str(appointmenttime)
        print(error)
        if_made = 0
    else:
        if db.execute('INSERT INTO appointment (appointment_id, appointmenttime) VALUES (%s, %s)'
                , (appointment_id, appointmenttime)) and \
                db.execute('INSERT INTO appoint (appointment_id, doctor_id, patient_id) VALUES (%s, %s, %s)'
                    , (appointment_id, doctor_ID, patient_ID)):
            if_made = 1

    return render_template('appoint/make.html', user_ID=user_ID, doctor_name=doctor_name, time=appointmenttime, if_made=if_made)



@bp.route('/doctor_list', methods=('GET', 'POST'))
@login_required
def doctor_list():
    db = init_db()
    doctors = db.execute('select * from (select * from doctor) as T1 '
                         'join (select doctor_id as id, ROUND(AVG(rate),2) as avg, count(evaluation_record_id) from evaluation '
                         'group by doctor_id) T2 on T1.doctor_id=T2.id '
                         'order by avg desc, count desc').fetchall()

    return render_template('appoint/doctor_list.html', user_ID=session.get('user_id'), doctors=doctors)







