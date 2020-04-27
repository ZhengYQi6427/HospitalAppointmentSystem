from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import init_db

bp = Blueprint('index', __name__, url_prefix='/main')

# ===========================================================================================
# For doctors
# ===========================================================================================
@bp.route('/doctor_index/<user_ID>', methods=('GET', 'POST'))
@login_required
def doctor_index(user_ID):
    db = init_db()
    doctor = db.execute(
        'SELECT name FROM Doctor WHERE user_id = (%s)', (user_ID,)
    ).fetchone()
    name = doctor['name']
    return render_template('index/doctor_index.html', user_ID=user_ID, name=name)


@bp.route('/doctor_appointment/<user_ID>', methods=('GET', 'POST'))
@login_required
def doctor_appointment(user_ID):
    db = init_db()
    doctor = db.execute(
        'SELECT doctor_id FROM Doctor WHERE user_id = (%s)', (user_ID,)
    ).fetchone()
    doctor_ID = doctor['doctor_id']

    appoint_info = db.execute(
        'SELECT * FROM '
        '(SELECT appoint.patient_id, doctor.user_id, patient.name, appointment.* '
        'FROM appoint, patient, appointment, doctor '
        'WHERE patient.patient_id = appoint.patient_id AND appointment.appointment_id = appoint.appointment_id AND '
        'doctor.doctor_id = (%s) AND appoint.doctor_id = (%s)) AS T1 '
        'LEFT JOIN (SELECT record.*, diagnose.doctor_id, diagnose.patient_id AS id FROM record, diagnose '
        'WHERE record.record_id = diagnose.record_id AND diagnose.doctor_id = (%s)) T2 ON T1.patient_id = T2.id '
        'AND T2.time = T1.appointmenttime'
        , (doctor_ID, doctor_ID, doctor_ID,)
    ).fetchall()

    return render_template('index/doctor_appointment.html', appoint_info=appoint_info)


@bp.route('/update/<user_ID>', methods=('GET', 'POST'))
@login_required
def update(user_ID):
    if request.method == 'POST':
        password = request.form['password']
        email = request.form['email']
        db = init_db()
        error = None

        if password:
            old_password = g.user['password']
            if old_password == password:
                error = 'New password cannot be the same as the old one.'
            else:
                db.execute('UPDATE Login SET password = (%s) WHERE user_id = (%s)', (password, user_ID))

        if email:
            old_email = g.user['email']
            if old_email == email:
                error = 'New email cannot be the same as the old one.'
            else:
                db.execute('UPDATE Login SET email = (%s) WHERE user_id = (%s)', (email, user_ID))

        if error is None or (email is None and password is None):
            if db.execute(
                    'SELECT * FROM Doctor WHERE user_id = (%s)', (user_ID,)
            ).fetchone() is not None:
                return redirect(url_for('index.doctor_index', user_ID=user_ID))
            else:
                return redirect(url_for('index.patient_index', user_ID=user_ID))

        flash(error)

    return render_template('index/update.html')


@bp.route('/diagnose/<appointment_id>', methods=('GET', 'POST'))
@login_required
def diagnose(appointment_id):
    if request.method == 'POST':
        import re
        record_id = 'r' + re.findall(r'([a-z]+)(\d+)', appointment_id)[0][1]
        disease_name = request.form['Disease_name']
        medicine_id = request.form['Medicine_id']
        medicine_quantity = request.form['Medicine_quantity']
        total_fee = request.form['Total_fee']
        db = init_db()
        error = None

        if not disease_name:
            error = 'Disease name is required.'
        elif not total_fee:
            error = 'Password is required.'
        elif db.execute(
            'SELECT * FROM Record WHERE record_ID = (%s)', (record_id,)
        ).fetchone() is not None:
            error = 'Diagnose record {} is already existed.'.format(record_id)

        if error is None:
            time = db.execute(
                'SELECT appointmenttime FROM appointment WHERE appointment_id = (%s)', (appointment_id, )
            ).fetchone()['appointmenttime']

            db.execute(
                'INSERT INTO Record (record_id, time, disease_name, medicine_id, medicine_quantity, total_fee) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (record_id, time, disease_name, medicine_id, medicine_quantity, total_fee)
            )

            doctor_id = db.execute(
                'SELECT * FROM appoint WHERE appoint.appointment_id = (%s)', (appointment_id, )
            ).fetchone()['doctor_id']
            patient_id = db.execute(
                'SELECT * FROM appoint WHERE appoint.appointment_id = (%s)', (appointment_id, )
            ).fetchone()['patient_id']
            db.execute(
                'INSERT INTO diagnose (record_id, doctor_id, patient_id) '
                'VALUES (%s, %s, %s)',
                (record_id, doctor_id, patient_id)
            )

            user_ID = session.get('user_id')
            return redirect(url_for('index.doctor_index', user_ID=user_ID))

        flash(error)

    return render_template('index/diagnose.html', appointment_id=appointment_id)


@bp.route('/comment_view/<user_ID>', methods=('GET', 'POST'))
@login_required
def comment_view(user_ID):
    db = init_db()
    evaluation = db.execute(
        'SELECT * FROM evaluation, doctor WHERE evaluation.doctor_id = doctor.doctor_id '
        'AND doctor.user_id = (%s)', (user_ID,)
    ).fetchall()

    return render_template('index/comment_view.html', evaluation=evaluation)


# ===========================================================================================
# For patients
# ===========================================================================================
@bp.route('/patient_index/<user_ID>', methods=('GET', 'POST'))
@login_required
def patient_index(user_ID):
    return render_template('index/patient_index.html', user_ID=user_ID)

@bp.route('/record_view/<user_ID>', methods=('GET', 'POST'))
@login_required
def record_view(user_ID):
    db = init_db()
    patient = db.execute(
        'SELECT patient_id FROM Patient WHERE user_id = (%s)', (user_ID,)
    ).fetchone()
    patient_ID = patient['patient_id']

    info = db.execute(
        'SELECT * FROM (SELECT appointment.*, doctor.name, doctor.doctor_id FROM appointment, appoint, doctor '
        'WHERE appointment.appointment_id = appoint.appointment_id '
        'AND appoint.doctor_id = doctor.doctor_id '
        'AND appoint.patient_id = (%s)) AS T1 '
        'LEFT JOIN (SELECT record.*, appoint.appointment_id AS id FROM record, appoint, diagnose, appointment '
        'WHERE diagnose.record_id = record.record_id AND diagnose.patient_id = appoint.patient_id AND diagnose.doctor_id = appoint.doctor_id'
        'AND appointment.appointment_id = appoint.appointment_id AND appointment.appointmenttime = record.time '
        'AND appoint.patient_id = (%s)) T2 '
        'ON T1.appointment_id = T2.id',
        (patient_ID, patient_ID)
    ).fetchall()

    eval = db.execute(
        'SELECT appoint.appointment_id FROM appoint, appointment, evaluate, evaluation '
        'WHERE appoint.patient_id = (%s) AND appointment.appointment_id = appoint.appointment_id '
        'AND appointment.appointmenttime = evaluate.time '
        'AND appoint.patient_id = evaluate.patient_id AND appoint.doctor_id = evaluate.doctor_id '
        'AND evaluate.evaluation_record_id = evaluation.evaluation_record_id',
        (patient_ID,)
    ).fetchall()

    flag = {}

    for item in info:
        flag[item['appointment_id']] = 0
        for e in eval:
            if e['appointment_id'] == item['appointment_id']:
                flag[item['appointment_id']] = 1

    return render_template('index/record_view.html', user_ID=user_ID, info=info, flag=flag)


@bp.route('/comment/<user_ID>/<appointment_id>', methods=('GET', 'POST'))
@login_required
def comment(user_ID, appointment_id):
    if request.method == 'POST':
        db = init_db()
        error = None
        import re
        evaluation_record_id = 'e' + re.findall(r'([A-Z]+)(\d+)', appointment_id)[0][1]
        doctor_ID = db.execute('SELECT doctor_id from appoint where appointment_id = (%s)', (appointment_id,)).fetchone()['doctor_id']
        patient_ID = db.execute('SELECT patient_id from patient where user_id = (%s)', (user_ID,)).fetchone()['patient_id']
        rate = request.form['Rate']
        comment = request.form['Comment']

        if not rate:
            error = 'Please give your score'
        if error is None:
            db.execute('INSERT INTO evaluation (evaluation_record_id, doctor_id, rate, comment) '
                       'VALUES (%s, %s, %s, %s)', (evaluation_record_id, doctor_ID, rate, comment))

            time = db.execute('SELECT appointmenttime FROM appointment WHERE appointment_id=(%s)',
                              (appointment_id,)).fetchone()['appointmenttime']
            db.execute('INSERT INTO evaluate (evaluation_record_id, doctor_id, patient_id, time) '
                       'VALUES (%s, %s, %s, %s)', (evaluation_record_id, doctor_ID, patient_ID, time))
            return redirect(url_for('index.record_view', user_ID=user_ID))

    return render_template('index/comment.html', appointment_id=appointment_id)










