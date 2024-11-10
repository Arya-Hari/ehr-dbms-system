from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"

mySqlConnect = mysql.connector.connect(
    host="localhost",
    user="aryahariharan",
    password="root",
    database="dbmsproject"
)
cursor = mySqlConnect.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def mainPage():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        if username == "" or password == "":
            flash("All fields are required!", category="error")
            return redirect(url_for('login'))
        
        sqlSelectQuery = "SELECT * FROM logininfo WHERE username = %s AND password = %s"
        cursor.execute(sqlSelectQuery, (username, password))
        
        user = cursor.fetchone()
        if user:
            return redirect(url_for('mainPage'))
        else:
            flash("Login Unsuccessful: Username/Password Incorrect",category="error")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['usernameInput']
        password = request.form['passwordInput']
        
        if username == "" or password == "":
            flash("All fields are required!",category="error")
            return redirect(url_for('register'))
        
        if len(password) <= 10:
            flash("Password must be atleast 10 characters")
            return redirect(url_for('register'))
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM logininfo WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Error: Username already in use")
            return redirect(url_for('register'))
        
        # Insert new user
        sql = "INSERT INTO logininfo (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, password))
        mySqlConnect.commit()
        
        return redirect(url_for('mainPage'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
