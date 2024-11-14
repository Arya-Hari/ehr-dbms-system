from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

mySqlConnect = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akshu123$",
    database="dbmsproject"
)
cursor = mySqlConnect.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def mainPage():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve the user's details
    cursor.execute("SELECT * FROM logininfo WHERE username = %s", (session['username'],))
    user_details = cursor.fetchone()
    
    return render_template('main.html', user_details=user_details)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        if username == "" or password == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('register'))
        
        if len(password) <= 10:
            flash("Password must be at least 10 characters")
            return redirect(url_for('register'))
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM logininfo WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Error: Username already in use")
            return redirect(url_for('register'))
        
        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert new user with hashed password into logininfo
        sql = "INSERT INTO logininfo (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, hashed_password))
        mySqlConnect.commit()
        
        # Insert the username into user_details with default values for other fields
        cursor.execute("INSERT INTO user_details (username) VALUES (%s)", (username,))
        mySqlConnect.commit()
        
        flash("Registration successful! Please log in.", category="success")
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        if username == "" or password == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('login'))
        
        # Fetch the user's hashed password from the database
        sqlSelectQuery = "SELECT password FROM logininfo WHERE username = %s"
        cursor.execute(sqlSelectQuery, (username,))
        user = cursor.fetchone()
        
        # Check if user exists and verify password
        if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
            session['username'] = username  # Store username in session
            return redirect(url_for('mainPage'))
        else:
            flash("Login Unsuccessful: Username or Password Incorrect", category="error")
            return redirect(url_for('login'))
    return render_template('login.html')



@app.route('/home')
def home():
    return render_template('home.html')  # Make sure home.html is the page where you want to navigate

@app.route('/enter_details', methods=['GET', 'POST'])
def enter_details():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        weight = request.form['weight']
        height = request.form['height']
        
        if name == "" or dob == "" or weight == "" or height == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('enter_details'))
        
        # Retrieve username from the session
        username = session.get('username')
        if not username:
            flash("User not logged in. Please log in first.", category="error")
            return redirect(url_for('login'))  # Redirect to login if username is missing
        
        # Calculate BMI
        bmi = round(float(weight) / (float(height) / 100) ** 2, 2)

        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

# Ensure bmi is a float and age is an int
        bmi = float(bmi)
        age = int(age)

# Check if the user already has details in the 'user_details' table
        cursor.execute("SELECT * FROM user_details WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
    # Update existing record
            sql_update = """
    UPDATE user_details
    SET name = %s, dob = %s, weight = %s, height = %s, bmi = %s, age = %s
    WHERE username = %s
    """
            cursor.execute(sql_update, (name, dob, weight, height, bmi, age, username))
        else:
    # Insert new record if not found
            sql_insert = """
    INSERT INTO user_details (username, name, dob, weight, height, bmi, age)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
            cursor.execute(sql_insert, (username, name, dob, weight, height, bmi, age))

        mySqlConnect.commit()
        
        # Display a success message and show the "Go to Home" option
        #flash("Details accepted successfully!", category="success")
        return render_template('enter_details.html', success=True)  # Passing success to trigger the message display
    
    return render_template('enter_details.html')





@app.route('/view_details')
def view_details():
    if 'username' not in session:
        flash("You need to log in first!", category="error")
        return redirect(url_for('login'))

    # Get the username from the session
    username = session['username']

    # Query the database for the user's details
    cursor.execute("SELECT name, dob,age, weight, height, bmi FROM user_details WHERE username = %s", (username,))
    user_details = cursor.fetchone()

    if user_details:
        # Pass the user details to the template
        return render_template('view_details.html', user_details=user_details)
    else:
        flash("No details found for this user.", category="error")
        return redirect(url_for('mainPage'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
