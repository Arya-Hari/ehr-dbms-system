from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify,send_from_directory
import mysql.connector
import bcrypt
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random
import pymysql
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
from gridfs import GridFS
import base64

# Creating an instance of a Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Creating a MySQL Connector object
mySqlConnect = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akshu123$",
    database="dbmslab"
)
sql_config = {
    "host": "localhost",
    "user": "root",
    "password": "Akshu123$",
    "database": "dbmsproject"
}
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["ehr_system"]
scan_collection = mongo_db["new"]
fs = GridFS(mongo_db)

# Folder to save uploaded files
UPLOAD_FOLDER = "uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def update_access_keys():
    cursor = mySqlConnect.cursor()
    try:
        # Generate and update a new access key for all users
        query = "UPDATE patientinfo SET accessKey = LPAD(FLOOR(RAND() * 1000000), 6, '0')"
        cursor.execute(query)
        mySqlConnect.commit()
    finally:
        cursor.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_access_keys, trigger="interval", minutes=3)
scheduler.start()

# First page to choose the role of the user
@app.route('/')
def choose_role():
    return render_template('choose_role.html')

# Function to select the appropriate table for login/register following role choice
@app.route('/select_table', methods=['POST'])
def select_table():
    # Store table name in session instance
    table_name = request.form['table']
    session['selected_table'] = table_name
    # Redirect to separate login if user role is pharmacy or laboratory
    if table_name == "pharmacy" or table_name == "laboratory":
        return redirect('pharmacy-laboratory-login')
    elif table_name=="doctorinfo":
        return redirect('doctor_login')
    return render_template('login-or-register.html')


# Register for patient/doctor
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        table_name = session.get('selected_table')
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        # Check if fields are empty
        if not username or not password:
            flash("All fields are required!", category="error")
            return redirect(url_for('register'))
        
        # Semantic checking on password
        if len(password) < 10:
            flash("Password must be at least 10 characters", category="error")
            return redirect(url_for('register'))
        
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        query = f"SELECT * FROM {table_name} WHERE username = %s"
        cursor.execute(query, (username,))
        # Check for unique username
        if cursor.fetchone():
            flash("Error: Username already in use", category="error")
            return redirect(url_for('register'))
        
        # Encrypt password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert data into the table
        try:
            query = f"INSERT INTO {table_name} (username, password) VALUES (%s, %s)"
            cursor.execute(query, (username, hashed_password))
            mySqlConnect.commit()
            print("complete")
            # Set session variable 'username' to the username
            session['username'] = username
            flash("Registration successful!", category="success")
        except Exception as e:
            mySqlConnect.rollback()
            flash("An error occurred during registration.", category="error")
            return redirect(url_for('register'))
        
        # Redirect to profile pages
        if table_name == "patientinfo":
            return redirect(url_for('new_patient_profile'))
        if table_name == "doctorinfo":
            return redirect(url_for('new_doctor_profile'))
    
    return render_template('register.html')

# Register for patient/doctor
@app.route('/doctor_register', methods=['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        table_name = session.get('selected_table')
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        # Check if fields are empty
        if not username or not password:
            flash("All fields are required!", category="error")
            return redirect(url_for('doctor_register'))
        
        # Semantic checking on password
        if len(password) < 10:
            flash("Password must be at least 10 characters", category="error")
            return redirect(url_for('doctor_register'))
        
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        query = f"SELECT * FROM {table_name} WHERE username = %s"
        cursor.execute(query, (username,))
        # Check for unique username
        if cursor.fetchone():
            flash("Error: Username already in use", category="error")
            return redirect(url_for('doctor_register'))
        
        # Encrypt password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert data into the table
        try:
            query = f"INSERT INTO {table_name} (username, password) VALUES (%s, %s)"
            cursor.execute(query, (username, hashed_password))
            mySqlConnect.commit()
            print("complete")
            # Set session variable 'username' to the username
            session['username'] = username
            flash("Registration successful!", category="success")
        except Exception as e:
            mySqlConnect.rollback()
            flash("An error occurred during registration.", category="error")
            return redirect(url_for('doctor_register'))
        
        
        if table_name == "doctorinfo":
            return redirect(url_for('new_doctor_profile'))
    
    return render_template('doctor_register.html')


# Login for patient/doctor
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        table_name = session.get('selected_table')
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        # Check if fields are empty
        if username == "" or password == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('login'))
        
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        query = f"SELECT patientID, password FROM {table_name} WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        # Check if the user exists and verify the password
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['userID'] = user[0]
            session['username'] = username
            return redirect(url_for('patient_home'))
        else:
            flash("Login Unsuccessful : Username or Password Incorrect", category="error")
            return redirect(url_for('login'))
    return render_template('login.html')

# Login for patient/doctor
@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        table_name = session.get('selected_table')
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        # Check if fields are empty
        if username == "" or password == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('login'))
        
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        query = f"SELECT doctorID, password FROM {table_name} WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        # Check if the user exists and verify the password
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['doctorID'] = user[0]
            session['username'] = username
            return redirect(url_for('doctor_dashboard'))
        else:
            flash("Login Unsuccessful : Username or Password Incorrect", category="error")
            return redirect(url_for('doctor_login'))
    return render_template('doctor_login.html')


@app.route('/pharmacy-laboratory-login', methods=['GET', 'POST'])
def pharmacy_laboratory_login():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput'].encode('utf-8')

        if not username or not password:
            flash("Username and password are required.", category="error")
            return redirect(url_for('pharmacy_laboratory_login'))

        cursor = mySqlConnect.cursor()

        # Fetch the hashed password for the given username
        cursor.execute("SELECT password FROM user_credentials WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            stored_hashed_password = user[0].encode('utf-8')
            # Verify the entered password with the stored hashed password
            if bcrypt.checkpw(password, stored_hashed_password):
                if username.startswith("laboratory"):
                    return redirect(url_for('laboratory_dashboard'))
                elif username.startswith("pharmacy"):
                    return redirect(url_for('pharmacy_dashboard'))
            else:
                flash("Incorrect password. Please try again.", category="error")
        else:
            flash("Invalid username. Please register first.", category="error")

        cursor.close()
        return redirect(url_for('pharmacy_laboratory_login'))

    return render_template("pharmacy-laboratory-login.html")


@app.route('/pharmacy-register', methods=['GET', 'POST'])
def pharmacy_register():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput'].encode('utf-8')

        if not username or not password:
            flash("Username and password are required.", category="error")
            return redirect(url_for('pharmacy_register'))

        cursor = mySqlConnect.cursor()

        # Check if username already exists
        cursor.execute("SELECT username FROM user_credentials WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already exists. Please choose a different one.", category="error")
        else:
            # Hash the password
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            try:
                cursor.execute("INSERT INTO user_credentials (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
                mySqlConnect.commit()
                flash("Registration successful! You can now log in.", category="success")
                return redirect(url_for('pharmacy_laboratory_login'))
            except Exception as e:
                flash(f"Registration failed: {e}", category="error")
        cursor.close()

    return render_template('pharmacy_register.html')


@app.route("/laboratory_dashboard", methods=["GET", "POST"])
def laboratory_dashboard():
    test_details = None
    access_granted = False
    cursor = mySqlConnect.cursor()

    try:
        if request.method == "POST":
            access_key = request.form.get("access_key")
            if access_key:
                print(f"Access key received: {access_key}")
                cursor.execute("SELECT patientID FROM patientinfo WHERE accessKey = %s", (access_key,))
                patient = cursor.fetchone()
                
                # Ensure all results are fetched
                cursor.fetchall()  

                if not patient:
                    flash("Invalid access key! Please try again.", "danger")
                    return redirect(url_for("laboratory_dashboard"))

                patient_id = patient[0]
                session["patientID"] = patient_id
                session["access_key"] = access_key
                access_granted = True

                cursor.execute("""
                    SELECT a.doctorID, p.test_name,p.prescription_id
                    FROM prescriptions p
                    JOIN appointments a ON a.appointmentID = p.appointment_id
                    WHERE a.userID = %s and p.test_required='yes'
                    ORDER BY a.date DESC
                """, (patient_id,))
                test_details = cursor.fetchone()

                # Fetch all remaining results to clear the buffer
                cursor.fetchall()
                print(f"test_details fetched: {test_details}")

        if request.method == "POST" and "upload_test" in request.form:
            print("Form submitted for upload_test")

            if not session.get("patientID"):
                flash("Session expired. Please enter access key again.", "warning")
                return redirect(url_for("laboratory_dashboard"))

            test_date = request.form.get("test_date")
            metadata = request.form.get("metadata")
            image = request.files.get("image")

            if not image:
                flash("Please upload a valid image.", "danger")
                return redirect(url_for("laboratory_dashboard"))

            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(filepath)

            patient_id = session["patientID"]
            doctor_id = test_details[0] if test_details else None

            cursor.execute(
                "INSERT INTO tests (patient_id, doctor_id, date,test_name,prescription_id) VALUES (%s, %s, %s,%s,%s)",
                (patient_id, doctor_id, test_date,test_details[1],test_details[2])
            )
            mySqlConnect.commit()
            test_id = cursor.lastrowid
            print("Data inserted into MySQL")

            image_id = fs.put(image.read(), filename=filename, content_type=image.content_type, metadata=metadata)

            scan_data = {
                "test_id": test_id,
                "metadata": metadata,
                "image_id": image_id,
                "file_path": filepath,
                "uploaded_at": datetime.now()
            }
            scan_collection.insert_one(scan_data)
            print("Data inserted into MongoDB")
            flash("Test details saved successfully!", "success")

            return redirect(url_for("laboratory_dashboard"))

    except Exception as e:
        flash(f"Error: {e}", "danger")
        print(f"Exception occurred: {e}")

    finally:
        try:
            cursor.close()  # Close cursor safely
        except:
            pass  

    return render_template("laboratory_dashboard.html", test_details=test_details, access_granted=access_granted)


@app.route("/laboratory_reset_access", methods=["GET"])
def laboratory_reset_access():
    session.pop("patientID", None)
    session.pop("access_key", None)
    return redirect(url_for("laboratory_dashboard"))


@app.route("/pharmacy_dashboard", methods=["GET", "POST"])
def pharmacy_dashboard():
    drug_details = None
    patient_id = None
    access_granted = False
    cursor = mySqlConnect.cursor()

    if request.method == "POST":
        access_key = request.form.get("access_key")
        if access_key:
            print(f"Access key received: {access_key}")

            try:
                # Step 1: Validate access key
                cursor.execute("SELECT patientID FROM patientinfo WHERE accessKey = %s", (access_key,))
                patient = cursor.fetchone()
                cursor.fetchall()

                if not patient:
                    flash("Invalid access key! Please try again.", "danger")
                    return redirect(url_for("pharmacy_dashboard"))

                patientID = patient[0]
                session["patientID"] = patientID  # Store in session
                session["access_key"] = access_key  # Store access key in session
                access_granted = True

                # Step 2: Fetch prescribed drug details

                cursor.execute("""
                    SELECT a.doctorID,d.drug_name, d.dosage, d.frequency,d.start_date,d.end_date
                    FROM drugs d
                    JOIN prescriptions p ON d.prescription_id = p.prescription_id
                    JOIN appointments a ON a.appointmentID = p.appointment_id
                    WHERE a.userID = %s
                """, (patientID,))

                drug_details = cursor.fetchall()
                print(drug_details)

            except Exception as e:
                flash(f"Error fetching drug details: {e}", "danger")
            finally:
                cursor.close()

    return render_template("pharmacy_dashboard.html", drug_details=drug_details, access_granted=access_granted)

@app.route("/pharmacy_reset_access", methods=["GET"])
def pharmacy_reset_access():
    session.pop("patientID", None)
    session.pop("access_key", None)
    return redirect(url_for("pharmacy_dashboard"))

# Creating new patient profile
@app.route('/new-patient-profile', methods=['GET', 'POST'])
def new_patient_profile():
    if request.method == "POST":
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        table_name = session.get('selected_table')
        username = session.get('username')
        
        # Get user details
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        middlename = request.form['middlename']
        dob = request.form['dob']
        weight = request.form['weight']
        height = request.form['height']
        bloodtype = request.form['bloodgroup']
        gender=request.form['gender']

        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        neww=float(weight)
        newh=float(height)/100
        print(neww,newh)
        bmi = round(neww / (newh*newh))
        
        # Validate that required fields are not empty
        if firstname == "" or lastname == "" or dob == "" or weight == "" or height == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('enter_details'))
        
        try:
            if middlename == "":  # If middle name is empty
                query = f"UPDATE {table_name} SET firstName = %s, lastName = %s, height = %s, weight = %s, dateOfBirth = %s,age=%s,bmi=%s, bloodType = %s, gender= %s WHERE username = %s"
                cursor.execute(query, (firstname, lastname, height, weight, dob,age,bmi, bloodtype,gender, username))
            else:  # If middle name is provided
                query = f"UPDATE {table_name} SET firstName = %s, middleName = %s, lastName = %s, height = %s, weight = %s,age=%s,bmi=%s, dateOfBirth = %s, bloodType = %s,gender=%s WHERE username = %s"
                cursor.execute(query, (firstname, middlename, lastname, height, weight,age,bmi, dob, bloodtype,gender, username))
            
            mySqlConnect.commit() 
            return redirect(url_for('patient_home'))
        except Exception as e:
            flash("An error occurred while updating the profile: " + str(e), category="error")
            return redirect(url_for('new_patient_profile'))

    return render_template('new-patient-profile.html')
@app.route('/new-doctor-profile', methods=['GET', 'POST'])
def new_doctor_profile():
    if request.method == "POST":
        cursor = mySqlConnect.cursor()
        table_name = session.get('selected_table')
        username = session.get('username')

        # Get user details from form
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        middlename = request.form.get('middlename', "")
        hospital = request.form['hospital']
        yoe = request.form['yoe']
        specialisation = request.form['specialisation']

        # Validate required fields
        if not all([firstname, lastname, hospital, yoe, specialisation]):
            flash("All fields are required!", category="error")
            return redirect(url_for('new_doctor_profile'))

        try:
            # Update the profile in the database
            if middlename == "":
                query = f"UPDATE {table_name} SET firstName = %s, lastName = %s, hospital = %s, yearsOfExperience = %s, specialisation = %s WHERE username = %s"
                cursor.execute(query, (firstname, lastname, hospital, yoe, specialisation, username))
            else:
                query = f"UPDATE {table_name} SET firstName = %s, middleName = %s, lastName = %s, hospital = %s, yearsOfExperience = %s, specialisation = %s WHERE username = %s"
                cursor.execute(query, (firstname, middlename, lastname, hospital, yoe, specialisation, username))
            
            mySqlConnect.commit()

            # Fetch doctorID and store it in session
            cursor.execute(f"SELECT doctorID FROM {table_name} WHERE username = %s", (username,))
            doctor = cursor.fetchone()
            if doctor:
                session['doctorID'] = doctor[0]

            flash("Profile updated successfully!", category="success")
            return redirect(url_for('doctor_dashboard'))

        except Exception as e:
            flash(f"An error occurred while updating the profile: {e}", category="error")
            return redirect(url_for('new_doctor_profile'))

    return render_template('new-doctor-profile.html')


@app.route("/doctor_dashboard")
def doctor_dashboard():
    
    doctor_id = session.get('doctorID')
    cursor = mySqlConnect.cursor()
    try:
        # Fetch Doctor Name and Details
        cursor.execute("SELECT * FROM doctorinfo WHERE doctorID = %s", (doctor_id,))
        doctor_details = cursor.fetchone()

        # Fetch Scheduled Appointments
        cursor.execute("""
            SELECT a.appointmentID, p.firstName AS patient_name, a.date, a.time, a.status
            FROM appointments a
            JOIN patientinfo p ON a.userID = p.patientID
            WHERE a.doctorID = %s
            ORDER BY a.date, a.time
        """, (doctor_id,))
        appointments = cursor.fetchall()
    
    finally:
        cursor.close()
    print(doctor_details)
    return render_template(
        "doctor_dashboard.html",
        doctor_name=doctor_details[3],
        doctor_details=doctor_details,
        appointments=appointments
    )

@app.route("/start_appointment/<int:appointment_id>", methods=["GET", "POST"])
def start_appointment(appointment_id):
    '''if "doctor_id" not in session:
        return redirect("/login")'''
    
    cursor = mySqlConnect.cursor()
    patient_details=None
    try:
        # Update Appointment Status to Ongoing
        cursor.execute("""
            UPDATE appointments
            SET status = 'Ongoing'
            WHERE appointmentID = %s
        """, (appointment_id,))
        mySqlConnect.commit()

        # Fetch Appointment and Patient Details
        cursor.execute("""
            SELECT a.appointmentID, p.firstName, a.date, a.time, a.status,a.userID
            FROM appointments a
            JOIN patientinfo p ON a.userID = p.patientID
            WHERE a.appointmentID = %s
        """, (appointment_id,))
        appointment = cursor.fetchone()

        if request.method == "POST":
            symptoms = request.form.get("symptoms")
            drugs_required = "drugs" in request.form
            tests_required = "tests" in request.form
            follow_on_required = request.form.get("follow_on_required")
            
            follow_on_time = "yes" if follow_on_required == "yes" else "no"
            print(follow_on_time)

            # Update Appointment follow-on
            cursor.execute("""
                UPDATE appointments
                SET follow_on = %s
                WHERE appointmentID = %s
            """, (follow_on_time, appointment_id))
            mySqlConnect.commit()

            if symptoms:
                cursor.execute("""
                    INSERT INTO symptoms (patient_id, appointment_id, symptom_description)
                    VALUES ((SELECT userID FROM appointments WHERE appointmentID = %s), %s, %s)
                """, (appointment_id, appointment_id, symptoms))
                mySqlConnect.commit()

            test_name = request.form.get("test_required")
            test_required = "yes" if test_name else "no"
            print(test_name)

            if drugs_required or tests_required:
                # Insert into prescription table
                cursor.execute("""
                    INSERT INTO prescriptions (appointment_id, test_required, test_name)
                    VALUES (%s, %s, %s)
                """, (appointment_id, test_required, test_name))
                mySqlConnect.commit()

                prescription_id = cursor.lastrowid  # Get the prescription_id of the inserted row
                drug_details = []
                for key in request.form:
                    if 'drug_name_' in key:
                        drug_index = key.split('_')[-1]
                        drug_details.append({
                            'name': request.form.get(f'drug_name_{drug_index}'),
                            'start_date': request.form.get(f'start_date_{drug_index}'),
                            'end_date': request.form.get(f'end_date_{drug_index}'),
                            'dosage': request.form.get(f'dosage_{drug_index}'),
                            'frequency': request.form.get(f'frequency_{drug_index}'),
                        })



                for drug_detail in drug_details:
                    try:
                        cursor.execute("""
                                INSERT INTO drugs (prescription_id, start_date, end_date, drug_name, dosage, frequency)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """, (prescription_id, drug_detail['start_date'], drug_detail['end_date'], drug_detail['name'], drug_detail['dosage'], drug_detail['frequency']))
                        mySqlConnect.commit()
                    except Exception as e:
                        print("Error inserting drug:", e)
       
        if request.method == "POST" and "finish_appointment" in request.form:
            # Change the appointment status to Finished
            cursor.execute("""
                UPDATE appointments
                SET status = 'Finished'
                WHERE appointmentID = %s
            """, (appointment_id,))
            mySqlConnect.commit()

            flash("Appointment marked as finished!", "success")
            return redirect("/doctor_dashboard")

    finally:
        cursor.close()

    return render_template(
        "start_appointment.html",
        appointment=appointment
    )

@app.route("/patient_details/<int:patient_id>")
def patient_details(patient_id):
    cursor = mySqlConnect.cursor()
    patient = None
    drugs=[]
    tests=[]
    try:
        cursor.execute("""
            SELECT p.firstName, p.lastName,p.gender, p.age, p.height, p.weight,p.bmi,p.bloodType, a.appointmentID
            FROM patientinfo p
            LEFT JOIN appointments a ON p.patientID = a.userID
            WHERE p.patientID = %s
        """, (patient_id,))
        
        # Fetch the result
        patient = cursor.fetchone()  # Or use fetchall() if expecting multiple rows
        print(patient)
        cursor.fetchall()
        cursor.execute("""
                    SELECT s.symptom_description, d.drug_name, d.dosage, d.frequency, d.start_date, d.end_date
                    FROM symptoms s
                    JOIN appointments ap ON ap.appointmentID = s.appointment_id
                    JOIN prescriptions p ON p.appointment_id = ap.appointmentID
                    JOIN drugs d ON d.prescription_id = p.prescription_id
                    WHERE ap.userID = %s
                """, (patient_id,))

        drugs = cursor.fetchall()
        print(drugs)


        cursor.execute("""
                    SELECT t.test_id,t.test_name,t.date
                    FROM tests t 
                    WHERE t.patient_id = %s
                """, (patient_id,))
        test_records = cursor.fetchall()
        print("Test Records:", test_records)

        for test in test_records:
            test_id, test_name,date = test
            test_data = scan_collection.find_one({"test_id": test_id})  # Find image for test_id in MongoDB
            print(test_data)
            if test_data and "file_path" in test_data:
                image_path = test_data["file_path"]  # File path from MongoDB
            else:
                image_path = None  # No image found
            print(f"Test ID: {test_id}, Image Path: {image_path}")


            tests.append({"test_name": test_name, "date":date,"image_path": image_path})


    except Exception as e:
        print("Error fetching patient details:", e)
        flash("Unable to fetch patient details.", "danger")
    finally:
        cursor.fetchall()  # Clear any remaining result set
        cursor.close()

    return render_template("patient_details.html", patient=patient,drugs=drugs,tests=tests)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)   


#View patient home
@app.route('/patient_home')
def patient_home():
    user_id = session.get('userID')
    cursor = mySqlConnect.cursor()
    try:
        # Fetch the access key for the logged-in user
        query = "SELECT accessKey FROM patientinfo WHERE patientID = %s"
        cursor.execute(query, (user_id,))
        #access_key = cursor.fetchone()[0]
        result = cursor.fetchone()
        access_key = result[0] if result else None

    finally:
        cursor.close()
            
    return render_template('patient_home.html', access_key=access_key)


# View profile for patient
@app.route('/view-patient-profile', methods = ['GET', 'POST'])
def view_patient_profile():
    # MySQL cursor instance
    cursor = mySqlConnect.cursor()
    table_name = session.get('selected_table')
    username = session.get('username')  # Retrieve username from session

    # If not logged in
    if not username:
        flash("You need to be logged in to view your profile.", category="error")
        return redirect(url_for('login'))

    # Query to fetch user details from the database
    query = f"SELECT firstName, middleName, lastName, dateOfBirth, weight, height, bloodType, gender ,bmi FROM {table_name} WHERE username = %s"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    if user_data:
        # Unpack the data into variables
        firstname, middlename, lastname, dob, weight, height, bloodtype,gender,bmi = user_data
        return render_template('view-patient-profile.html', firstname=firstname, middlename=middlename,
                               lastname=lastname, dob=dob, weight=weight, height=height, bloodtype=bloodtype,gender=gender,bmi=bmi)
    else:
        flash("User not found.", category="error")
        return redirect(url_for('choose_role'))


# Update patient profile details
@app.route('/update-patient-profile', methods=['GET', 'POST'])
def update_patient_profile():
    # MySQL cursor instance
    cursor = mySqlConnect.cursor()
    table_name = session.get('selected_table')
    username = session.get('username')

    # Check if user logged in
    if not username:
        flash("You need to be logged in to update your profile.", category="error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Collect updated details from the form
        firstname = request.form['firstname']
        middlename = request.form['middlename']
        lastname = request.form['lastname']
        dob = request.form['dob']
        weight = request.form['weight']
        height = request.form['height']
        bloodtype = request.form['bloodgroup']
        

        # Validate required fields
        if not firstname or not lastname or not dob or not weight or not height or not bloodtype:
            flash("All fields are required!", category="error")
            return redirect(url_for('update_patient_profile'))

        # Update the database
        try:
            if middlename:
                query = f"""
                UPDATE {table_name} 
                SET firstName = %s, middleName = %s, lastName = %s, dateOfBirth = %s, weight = %s, height = %s, bloodType = %s 
                WHERE username = %s
                """
                cursor.execute(query, (firstname, middlename, lastname, dob, weight, height, bloodtype, username))
            else:
                query = f"""
                UPDATE {table_name} 
                SET firstName = %s, lastName = %s, dateOfBirth = %s, weight = %s, height = %s, bloodType = %s 
                WHERE username = %s
                """
                cursor.execute(query, (firstname, lastname, dob, weight, height, bloodtype, username))

            mySqlConnect.commit()
            flash("Profile updated successfully!", category="success")
            return redirect(url_for('view_patient_profile'))
        except Exception as e:
            mySqlConnect.rollback()
            flash("An error occurred while updating the profile: " + str(e), category="error")
            return redirect(url_for('update_patient_profile'))

    # Pre-fill the form with current details
    query = f"SELECT firstName, middleName, lastName, dateOfBirth, weight, height, bloodType FROM {table_name} WHERE username = %s"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    if user_data:
        return render_template('update-patient-profile.html', user=user_data)
    else:
        flash("User not found.", category="error")
        return redirect(url_for('view_patient_profile'))


# API route for getting doctors available for booking
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    try:
        # MySQL cursor instance
        newcursor = mySqlConnect.cursor()
        query = "SELECT doctorID, firstName, lastName, hospital, specialisation FROM doctorinfo"
        newcursor.execute(query)
        doctors = newcursor.fetchall()
        
        # Formatting retrieved tuples
        doctor_list = [
            {
                "id": doctor[0],
                "name": f"{doctor[1]} {doctor[2]}",
                "hospital": doctor[3],
                "specialisation": doctor[4]
            }
            for doctor in doctors
        ]
        return {"doctors": doctor_list}
    except Exception as e:
        return {"error": str(e)}, 500


# API route to book doctor and enter information into appointments table
@app.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
def book_doctor(doctor_id):
    # MySQL cursor instance
    cursor = mySqlConnect.cursor()
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        userID = session.get('userID')
        
        # Inserting appointment details into appointment table
        try:
            query = """
                INSERT INTO appointments (userID, doctorID, date, time, status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (userID, doctor_id, date, time, "Scheduled"))
            mySqlConnect.commit()
            return redirect(url_for('patient_home'))
        except Exception as e:
            flash("An error occurred: " + str(e), category="error")
            mySqlConnect.rollback()
            return redirect(url_for('book_doctor', doctor_id=doctor_id))

    
    # Form information for booking appointment
    query = "SELECT firstName, lastName, hospital, specialisation FROM doctorinfo WHERE doctorID = %s"
    cursor.execute(query, (doctor_id,))
    doctor = cursor.fetchone()

    date = request.args.get('date')
    if date:
        query = """
            SELECT time FROM appointments 
            WHERE doctorID = %s AND date = %s
        """
        cursor.execute(query, (doctor_id, date))
        
        # Checking if any time slots have already been booked
        booked_slots = cursor.fetchall()
        booked_times = {slot['time'] for slot in booked_slots}
    else:
        booked_times = set()

    # Available slots are those not present in booked slots
    start_time = datetime.strptime("09:30", "%H:%M")
    end_time = datetime.strptime("19:30", "%H:%M")
    delta = timedelta(minutes=30)
    available_slots = []
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime("%H:%M")
        if time_str not in booked_times:
            available_slots.append(time_str)
        current_time += delta

    return render_template('book-form.html', doctor=doctor, available_slots = available_slots, selected_date=date, doctor_id=doctor_id)


# API route for displaying the available slots
@app.route('/api/available_slots', methods=['GET'])
def get_available_slots():
    cursor = mySqlConnect.cursor()
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')

    query = """
        SELECT time FROM appointments 
        WHERE doctorID = %s AND date = %s
    """
    cursor.execute(query, (doctor_id, date))
    booked_slots = cursor.fetchall()

    # Slots start at 9:30, end at 19:30 and are at 30-minute intervals
    booked_times = set()
    for slot in booked_slots:
        if isinstance(slot[0], timedelta):
            total_seconds = slot[0].total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            booked_times.add(f"{hours:02}:{minutes:02}")
        else:
            booked_times.add(slot[0].strftime("%H:%M"))

    start_time = datetime.strptime("09:30", "%H:%M")
    end_time = datetime.strptime("19:30", "%H:%M")
    delta = timedelta(minutes=30)

    available_slots = []
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime("%H:%M")
        if time_str not in booked_times:
            available_slots.append(time_str)
        current_time += delta

    return {"available_slots": available_slots}


# API route for previously booked appointments
@app.route('/api/previous_appointments', methods=['GET'])
def get_previous_appointments():
    cursor = mySqlConnect.cursor()
    userID = session.get('userID')
    if not userID:
        return {"error": "User not logged in"}, 401

    try:
        query = """
            SELECT 
                CONCAT(d.firstName, ' ', d.lastName) AS doctor, 
                d.hospital, 
                a.date,
                a.time, 
                a.status,
                a.follow_on,
                a.appointmentID
            FROM appointments a
            JOIN doctorinfo d ON a.doctorID = d.doctorID
            WHERE a.userID = %s
            ORDER BY a.date DESC, a.time DESC
        """
        cursor.execute(query, (userID,))
        appointments = cursor.fetchall()
        print(appointments)
        # Formatting appointment information
        appointment_list = [
            {
                "doctor": appointment[0],
                "hospital": appointment[1],
                "date": appointment[2].strftime('%Y-%m-%d'),  # Convert date to string
                "time": str(appointment[3]),  # Convert time or timedelta to string
                "status": appointment[4],
                "follow":appointment[5],
                "id":appointment[6]
            }
            for appointment in appointments
        ]
        return {"appointments": appointment_list}
       
    except Exception as e:
        return {"error": str(e)}, 500
    print(appointment_list)


@app.route('/view_prescription/<int:appointment_id>')
def view_prescription(appointment_id):
    try:
        cursor = mySqlConnect.cursor()

        # Fetch symptoms based on appointment_id
        cursor.execute("""
            SELECT s.symptom_description
            FROM symptoms s  
            WHERE s.appointment_id = %s
        """, (appointment_id,))
        symptoms = [row[0] for row in cursor.fetchall()]
        print("Symptoms:", symptoms)

        # Fetch drug and test details
        cursor.execute("""
            SELECT d.drug_name, d.dosage, d.frequency, d.start_date, d.end_date, 
                   t.test_id, t.test_name, t.date
            FROM prescriptions p 
            LEFT JOIN drugs d ON d.prescription_id = p.prescription_id
            LEFT JOIN tests t ON t.prescription_id = p.prescription_id
            WHERE p.appointment_id = %s
        """, (appointment_id,))
        drugs = cursor.fetchall()  # Can be empty

        test_images = {}
        for drug in drugs:
            test_id = drug[5]  # Index 5 is test_id
            if test_id:  # Ensure test_id is valid
                test = scan_collection.find_one({"test_id": test_id})
                if test and "file_path" in test:
                    test_images[test_id] = test["file_path"]

        cursor.close()

        print("Test Images:", test_images)

        return render_template('view_prescription.html', 
                               appointment_id=appointment_id, 
                               symptoms=symptoms, 
                               drugs=drugs, 
                               test_images=test_images)
    
    except Exception as e:
        print(f"Error fetching prescription details: {e}")
        return "Failed to load prescription details.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)
    
import atexit
atexit.register(lambda: scheduler.shutdown())
