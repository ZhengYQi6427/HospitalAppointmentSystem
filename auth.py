import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import init_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

days = ['Monday','Tuesday','Wednesday','Thursday',
            'Friday','Saturday','Sunday']

@bp.route('/register', methods=('GET', 'POST'))
def register_main():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']
        email = request.form['email']
        account_type = request.form['accountType']
        db = init_db()
        error = None

        if not user_ID:
            error = 'UserID is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif not account_type:
            error = 'Account type is required.'
        elif db.execute(
            'SELECT * FROM Login WHERE user_ID = (%s)', (user_ID,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(user_ID)

        if error is None:
            db.execute(
                'INSERT INTO Login (user_ID, password, email) VALUES (%s, %s, %s)',
                (user_ID, password, email)
            )
            if account_type == 'Doctor':
                return redirect(url_for('auth.register_doctor', user_ID=user_ID))
            else:
                return redirect(url_for('auth.register_patient', user_ID=user_ID))

        flash(error)

    types = ['Doctor', 'Patient']
    return render_template('auth/register.html', types=types)


@bp.route('/register_doctor/<user_ID>', methods=('GET', 'POST'))
def register_doctor(user_ID):
    if request.method == 'POST':
        doctor_ID = request.form['Doctor_ID']
        name = request.form['Name']
        title = request.form['Title']
        specialization = request.form['Specialization']
        availabletime = request.form['AvailableTime']
        db = init_db()
        error = None

        if not doctor_ID:
            error = 'Doctor ID is required.'
        elif not name:
            error = 'Name is required.'
        elif not specialization:
            error = 'Specialization is required.'
        elif not availabletime:
            error = 'Available Time is required.'
        elif db.execute(
            'SELECT doctor_id FROM Doctor WHERE doctor_id = (%s)', (doctor_ID,)
        ).fetchone() is not None:
            error = 'Doctor ID {} is already registered.'.format(doctor_ID)

        if error is None:
            db.execute(
                'INSERT INTO Doctor (doctor_id, name, title, specialization, availabletime, user_id) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (doctor_ID, name, title, specialization, availabletime, user_ID)
            )
            return render_template('auth/login.html')

        flash(error)

    return render_template('auth/register_doctor.html', user_ID=user_ID, days=days)


@bp.route('/register_patient/<user_ID>', methods=('GET', 'POST'))
def register_patient(user_ID):
    if request.method == 'POST':
        patient_ID = request.form['Patient_ID']
        name = request.form['Name']
        gender = request.form['Gender']
        height = request.form['Height']
        weight = request.form['Weight']
        age = request.form['Age']
        bloodtype = request.form['BloodType']
        db = init_db()
        error = None

        if not patient_ID:
            error = 'Patient ID is required.'
        elif not name:
            error = 'Name is required.'
        elif db.execute(
            'SELECT patient_id FROM Patient WHERE patient_id = (%s)', (patient_ID,)
        ).fetchone() is not None:
            error = 'Patient ID {} is already registered.'.format(patient_ID)

        if error is None:
            db.execute(
                'INSERT INTO Patient (patient_id, name, user_id) '
                'VALUES (%s, %s, %s)',
                (patient_ID, name, user_ID)
            )
            db.execute(
                'INSERT INTO Personal_information (name, gender, height, weight, age, bloodtype, patient_id) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (name, gender, height, weight, age, bloodtype, patient_ID)
            )
            return render_template('auth/login.html')

        flash(error)

    return render_template('auth/register_doctor.html', user_ID=user_ID)


@bp.route('/register_nurse/<user_ID>', methods=('GET', 'POST'))
def register_nurse(user_ID):
    if request.method == 'POST':
        nurse_ID = request.form['Nurse_ID']
        name = request.form['Name']
        specialization = request.form['Specialization']
        db = init_db()
        error = None

        if not nurse_ID:
            error = 'Doctor ID is required.'
        elif not name:
            error = 'Name is required.'
        elif not specialization:
            error = 'Specialization is required.'
        elif db.execute(
                'SELECT nurse_id FROM Nurse WHERE nurse_id = (%s)', (nurse_ID,)
        ).fetchone() is not None:
            error = 'Nurse ID {} is already registered.'.format(nurse_ID)

        if error is None:
            db.execute(
                'INSERT INTO Nurse (nurse_id, name, specialization, user_id) '
                'VALUES (%s, %s, %s, %s)',
                (nurse_ID, name, specialization, user_ID)
            )
            return render_template('auth/login.html')

        flash(error)

    return render_template('auth/register_nurse.html', user_ID=user_ID)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']
        db = init_db()
        error = None
        user = db.execute(
            'SELECT * FROM Login WHERE user_ID = (%s)', (user_ID,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif user['password'] != password:
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']

            if db.execute(
                    'SELECT * FROM Doctor WHERE user_id = (%s)', (user_ID,)
            ).fetchone() is not None:
                return redirect(url_for('index.doctor_index', user_ID=user_ID))

            elif db.execute(
                    'SELECT * FROM Nurse WHERE user_id = (%s)', (user_ID,)
            ).fetchone() is not None:
                return redirect(url_for('index.nurse_index', user_ID=user_ID))

            elif db.execute(
                    'SELECT * FROM Patient WHERE user_id = (%s)', (user_ID,)
            ).fetchone() is not None:
                return redirect(url_for('index.patient_index', user_ID=user_ID))
            else:
                error = "Invalid account. (Unknown account type)"

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_ID = session.get('user_id')

    if user_ID is None:
        g.user = None
    else:
        g.user = init_db().execute(
            'SELECT * FROM Login WHERE user_id = (%s)', (user_ID,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view