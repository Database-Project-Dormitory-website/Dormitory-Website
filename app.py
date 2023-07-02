from flask import Flask, render_template, request, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)
app.config['SECRET_KEY'] = "Never push this line to github public repo"

cred = yaml.load(open('cred.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST'] = cred['mysql_host']
app.config['MYSQL_USER'] = cred['mysql_user']
app.config['MYSQL_PASSWORD'] = cred['mysql_password']
app.config['MYSQL_DB'] = cred['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        userDetails = request.form

        # Check the password and confirm password
        if userDetails['password'] != userDetails['confirm_password']:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        p1 = userDetails['first_name']
        p2 = userDetails['last_name']
        p3 = userDetails['username']
        p4 = userDetails['email']
        p5 = userDetails['password']

        hashed_pw = generate_password_hash(p5)
        print(p1 + "," + p2 + "," + p3 + "," + p4 + "," + p5 + "," + hashed_pw)

        queryStatement = (
            f"INSERT INTO "
            f"user(first_name,last_name, username, email, password, role_id) "
            f"VALUES('{p1}', '{p2}', '{p3}', '{p4}','{hashed_pw}', 1)"
        )
        print(check_password_hash(hashed_pw, p5))
        print(queryStatement)
        cur = mysql.connection.cursor()
        cur.execute(queryStatement)
        mysql.connection.commit()
        cur.close()

        flash("Form Submitted Successfully.", "success")
        return redirect('/')
    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)