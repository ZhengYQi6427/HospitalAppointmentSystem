
# Hospital Appointment Application

Hospital Appointment Application is a Flask app to arrange appoinments with doctors in a given system. Users can register as either doctor or patient. 

## Description
For every user, he can register with user_id, password, email and he needs to choose account type: doctor or patient. Different account type will redirect to different webpages and have different functions.  

1. For doctors
They use user_id and password to login the system and they can modify their account information: password and email. 
They have access to view their appointments information including appointment time, locations and patients’ names, and they can make a diagnosis by typing in the disease name, medicine_id, medicine_quantity and total_fee for every appointment that does not have a diagnose yet.
They can view all the comments and corresponding rates from patients. 

2. For patients
They use user_id and password to login the system and they can modify their account information: password and email. The app ask for patients' information when they register and store in database.
They can make appointments by searching the doctor’s name or symptoms to get the suitable doctor. Searching according to symptoms would query informations using API from Symptom Checker based on the symptoms selected and the patients' information in the database. A rough diagnosis shows on the result page and the app would select doctor according to this diagnosis ordering by doctor's rate and number of comments. Patients can have a view of information about the selected doctors including doctor’s name, his/her rating, specialization and available time on the same page and then make an appointment by clicking "select". In addition, if no doctor is recommended, patients can also get redirected to the doctor list page to have a view of all doctors and make appointments there. If appointment is made successfully, patient can see notice on the "make" page, otherwise there will be a trouble shooting message.
[Attention: a patient is not allowed to make an appointment with the same doctor multiple times at the same day]
They can view their appointment records including appointment time, doctor, location, diagnose result and total fee. They can also comment and rate on the doctor if the appointment has diagnosis result. 

We do not implement the function for administrators and nurses because the system can work fine with current functions. The role nurse doesn't have many iteration with other roles in the system. Administrators can be added in further development. 

## ER Diagram
![](images/ER%20new.png)

## Database Operation Examples
1. Select the most suitable doctor:

(select * from (select * from doctor where specialization= (%s) ) as T1 
join (select doctor_id as id, ROUND(AVG(rate),2) as avg, count(evaluation_record_id) from evaluation 
group by doctor_id) T2 on T1.doctor_id=T2.id 
order by avg desc, count desc, (spec['speicalisation'],))

We use RapidAPI to help us to match the symptoms with the department the patient need to go. For example, after the first step of searching, we get the specialization of doctor like “Ear, Nose, and Throat” that the patient needs to seek. And run the query above to select the doctor whose specialization is “Ear, Nose, and Throat” and display the information of the doctors in descending order of their rates. 


2. Get the appointment information for doctor

SELECT * FROM 
(SELECT appoint.patient_id, doctor.user_id, patient.name, appointment.* 
FROM appoint, patient, appointment, doctor 
WHERE patient.patient_id = appoint.patient_id AND appointment.appointment_id = appoint.appointment_id AND 
doctor.doctor_id = (%s) AND appoint.doctor_id = (%s)) AS T1 
LEFT JOIN (SELECT record.*, diagnose.doctor_id, diagnose.patient_id AS id FROM record, diagnose 
WHERE record.record_id = diagnose.record_id AND diagnose.doctor_id = (%s)) T2 ON T1.patient_id = T2.id 
AND T2.time = T1.appointmenttime
, (doctor_ID, doctor_ID, doctor_ID,)

The appointment information involves of six tables appoint, patient, appointment, doctor, record and diagnose. Some appointments do not have record, so we need to use left join to list all the appointments no matter whether they have records. 

## Techonologies Used
PostgreSQL, Flask (deployed on GCE)
