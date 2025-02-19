# Imports
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import bcrypt
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import random
from apscheduler.schedulers.background import BackgroundScheduler

# Creating an instance of a Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Creating a MySQL Connector object
mySqlConnect = mysql.connector.connect(
    host="localhost",
    user="aryahariharan",
    password="root",
    database="dbmslab"
)

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


# Login for pharmacy/laboratory
@app.route('/pharmacy-laboratory-login', methods=['GET', 'POST'])
def pharmacy_laboratory_login():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        # Hardcoded pharmacy/laboratory usernames and passwords
        allowed_usernames = ["pharmacy1", "laboratory1"]
        allowed_passwords = ["12345","67890"]
        
        # Check if entered username and password match
        if username in allowed_usernames and password in allowed_passwords:
            ind = allowed_usernames.index(username)
            req_password = allowed_passwords[ind]
            if req_password != password:
                flash("Incorrect password", category="error")
                return redirect(url_for('pharmacy-laboratory-login'))
            else:
                return redirect(url_for('choose_role'))
        else:
            flash("Incorrect username or password", category="error")
            return redirect(url_for('pharmacy-laboratory-login'))
    
    return render_template("pharmacy-laboratory-login.html")


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
        
        # Validate that required fields are not empty
        if firstname == "" or lastname == "" or dob == "" or weight == "" or height == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('enter_details'))
        
        try:
            if middlename == "":  # If middle name is empty
                query = f"UPDATE {table_name} SET firstName = %s, lastName = %s, height = %s, weight = %s, dateOfBirth = %s, bloodType = %s WHERE username = %s"
                cursor.execute(query, (firstname, lastname, height, weight, dob, bloodtype, username))
            else:  # If middle name is provided
                query = f"UPDATE {table_name} SET firstName = %s, middleName = %s, lastName = %s, height = %s, weight = %s, dateOfBirth = %s, bloodType = %s WHERE username = %s"
                cursor.execute(query, (firstname, middlename, lastname, height, weight, dob, bloodtype, username))
            
            mySqlConnect.commit() 
            return redirect(url_for('choose_role'))
        except Exception as e:
            flash("An error occurred while updating the profile: " + str(e), category="error")
            return redirect(url_for('new-patient-profile'))

    return render_template('new-patient-profile.html')

# Creating a new doctor profile
@app.route('/new-doctor-profile', methods=['GET', 'POST'])
def new_doctor_profile():
    if request.method == "POST":
        # MySQL cursor instance
        cursor = mySqlConnect.cursor()
        table_name = session.get('selected_table')
        username = session.get('username')
        
        # Get user details
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        middlename = request.form['middlename']
        hospital = request.form['hospital']
        yoe = request.form['yoe']
        specialisation = request.form['specialisation']
        
        # Validate that required fields are not empty
        if firstname == "" or lastname == "" or hospital == "" or yoe == "" or specialisation == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('enter_details'))
        
        try:
            if middlename == "":  # If middle name is empty
                query = f"UPDATE {table_name} SET firstName = %s, lastName = %s, hospital = %s, yearsOfExperience = %s, specialisation = %s WHERE username = %s"
                cursor.execute(query, (firstname, lastname, hospital, yoe, specialisation, username))
            else:  # If middle name is provided
                query = f"UPDATE {table_name} SET firstName = %s, middleName = %s, lastName = %s, hospital = %s, yearsOfExperience = %s, specialisation = %s WHERE username = %s"
                cursor.execute(query, (firstname, middlename, lastname, hospital, yoe, specialisation, username))
            
            mySqlConnect.commit() 
            return redirect(url_for('choose_role'))
        except Exception as e:
            flash("An error occurred while updating the profile: " + str(e), category="error")
            return redirect(url_for('new_doctor_profile'))

    return render_template('new-doctor-profile.html')


#View patient home
@app.route('/patient_home')
def patient_home():
    user_id = session.get('userID')
    cursor = mySqlConnect.cursor()
    try:
        # Fetch the access key for the logged-in user
        query = "SELECT accessKey FROM patientinfo WHERE patientID = %s"
        cursor.execute(query, (user_id,))
        access_key = cursor.fetchone()[0]

    finally:
        cursor.close()
            
    return render_template('patient-home.html', access_key=access_key)


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
    query = f"SELECT firstName, middleName, lastName, dateOfBirth, weight, height, bloodType FROM {table_name} WHERE username = %s"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    if user_data:
        # Unpack the data into variables
        firstname, middlename, lastname, dob, weight, height, bloodtype = user_data
        return render_template('view-patient-profile.html', firstname=firstname, middlename=middlename,
                               lastname=lastname, dob=dob, weight=weight, height=height, bloodtype=bloodtype)
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
            cursor.execute(query, (userID, doctor_id, date, time, "Not Started"))
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
                a.status 
            FROM appointments a
            JOIN doctorinfo d ON a.doctorID = d.doctorID
            WHERE a.userID = %s
            ORDER BY a.date DESC, a.time DESC
        """
        cursor.execute(query, (userID,))
        appointments = cursor.fetchall()
        
        # Formatting appointment information
        appointment_list = [
            {
                "doctor": appointment[0],
                "hospital": appointment[1],
                "date": appointment[2].strftime('%Y-%m-%d'),  # Convert date to string
                "time": str(appointment[3]),  # Convert time or timedelta to string
                "status": appointment[4]
            }
            for appointment in appointments
        ]
        return {"appointments": appointment_list}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run()
    
import atexit
atexit.register(lambda: scheduler.shutdown())