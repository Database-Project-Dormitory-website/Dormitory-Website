from asyncio.windows_events import NULL
from datetime import datetime
from datetime import date

from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import sqlite3
import yaml
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = '1893'

cred = yaml.load(open('cred.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST'] = cred['mysql_host']
app.config['MYSQL_USER'] = cred['mysql_user']
app.config['MYSQL_PASSWORD'] = cred['mysql_password']
app.config['MYSQL_DB'] = cred['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")



@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        loginForm = request.form
        username = loginForm['username']
        cur = mysql.connection.cursor()
        queryStatement = f"SELECT * FROM user WHERE username = '{username}'"
        numRow = cur.execute(queryStatement)
        if numRow > 0:
            user = cur.fetchone()
            if check_password_hash(user['password'], loginForm['password']):
                # Record session information
                session['login'] = True
                session['username'] = user['username']
                session['firstName'] = user['first_name']
                session['lastName'] = user['last_name']

                if user['role_id'] == 1:
                    return redirect('/admin')
                
                print(session['username'])
                flash('Welcome ' + session['firstName'], 'success')
                # flash("Log In successful",'success')
                return redirect('/')
            else:
                cur.close()
                flash("Password is incorrect", 'danger')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return render_template('login.html')
    return render_template('login.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        userDetails = request.form

        queryStatement = f"SELECT * FROM user"
        cur = mysql.connection.cursor()
        numRow = cur.execute(queryStatement)
        if numRow > 0:
            user = cur.fetchone()
            if userDetails['username'] in user['username']:
                flash('This username isn\'t available. Please try another.', 'danger')
                return render_template('register.html')
        # Check the password and confirm password
        if userDetails['password'] != userDetails['confirm_password']:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        p1 = userDetails['first_name']
        p2 = userDetails['last_name']
        p3 = userDetails['username']
        p4 = userDetails['email']
        p5 = userDetails['password']
        p6 = userDetails['phone_number']

        hashed_pw = generate_password_hash(p5)
        print(p1 + "," + p2 + "," + p3 + "," + p4 + "," + p5 + "," + p6 + "," + hashed_pw)

        queryStatement = (
            f"INSERT INTO "
            f"user(first_name, last_name, username, email, phone_number, password, role_id) "
            f"VALUES('{p1}', '{p2}', '{p3}', '{p4}', '{p6}', '{hashed_pw}', {2})"
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


@app.route('/roomlists')
def roomlists():
    return render_template('roomlists.html')


@app.route('/reviews/')
def reviews():
    cur = mysql.connection.cursor()
    queryStatement = f"SELECT * FROM reviews"
    print(queryStatement)
    result_value = cur.execute(queryStatement)
    if result_value > 0:
        reviews = cur.fetchall()
        return render_template('reviews.html', reviews=reviews)
    else:
        return render_template('reviews.html', reviews=None)


@app.route('/write-review/', methods=['GET', 'POST'])
def write_review():
    try:
        username = session['username']
    except:
        flash('Please sign in first.', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        review = request.form
        body = review['body']
        cur = mysql.connection.cursor()
        queryStatement = (
            f"INSERT INTO reviews(username, body) "
            f"VALUES('{username}', '{body}')"
        )
        print(queryStatement)
        cur.execute(queryStatement)
        mysql.connection.commit()
        cur.close()
        flash("Successfully posted", 'success')
        return redirect('/reviews')
    return render_template('write-review.html')



@app.route('/logout')
def logout():
    try:
        session['username']
        session.clear()
        flash("You have been logged out", 'info')
        return redirect('/')

    except:
        flash('Please sign in first.', 'danger')
        return redirect('/')


@app.route('/delete-review/<int:id>/')
def delete_review(id):
    try:
        username = session['username']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')

    cur = mysql.connection.cursor()
    review_user = f"SELECT username FROM reviews WHERE review_id = {id}"
    cur.execute(review_user)
    user = cur.fetchall()

    if (user[0]['username'] == username):
        queryStatement = f"DELETE FROM reviews WHERE review_id = {id}"
        print(queryStatement)
        cur.execute(queryStatement)
        mysql.connection.commit()
        flash("Your review is deleted", "success")
        return redirect('/reviews')
    else:
        flash("This is not your review", "danger")
        return redirect('/reviews')


@app.route('/report-problem', methods=['GET', 'POST'])
def report_problem():
    try:
        username = session['username']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        room_number = request.form.get('room_number')
        problem_description = request.form.get('problem_description')

    # Validate form inputs
        if not room_number or not problem_description:
            return render_template('report_problem.html', error="Please fill in all fields.")
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("INSERT INTO Problems (user_id, room_id, problem_details, status) VALUES (?, ?, ?, ?)",
                (username, room_number, problem_description, 'pending'))
        conn.commit()
    return render_template('report_problem.html')


@app.route('/problems', methods=['GET','POST'])
def problem():
    username = session.get('username')
    if username != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        problem_id = request.form.get('problem_id')
        new_status = request.form.get('new_status')
        with sqlite3.connect('models/dormWEB.db') as conn:
            con = conn.cursor()
            con.execute("UPDATE Problem SET status = ? WHERE problem_id = ?", (new_status, problem_id))
            con.execute("SELECT * FROM Problem")
            problems = con.fetchall()
    return render_template('problems.html', problems=problems)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    cur = mysql.connection.cursor()
    curr = mysql.connection.cursor()
    queryStatement = (
        f"SELECT u.first_name, u.last_name, u.email, u.phone_number, "
        f"c.start, c.end, r.room_number, rt.room_type "
        f"FROM user AS u "
        f"JOIN contracts AS c on u.user_id = c.user_id "
        f"JOIN rooms AS r on c.contract_id = r.contract_id "
        f"JOIN roomtype AS rt on r.room_type_id = rt.room_type_id"
    )
    queryStatement1 = (
        f"SELECT room_number, "
        f"(SELECT room_type FROM roomtype WHERE room_type_id = rooms.room_type_id) AS room_type "
        f"FROM rooms WHERE contract_id IS NULL"
    )
    print(queryStatement)
    print(queryStatement1)
    result_value = cur.execute(queryStatement)
    result_value1 = curr.execute(queryStatement1)
    if result_value > 0 and result_value1 > 0:
        rooms = cur.fetchall()
        empty_rooms = curr.fetchall()
        return render_template('admin.html', rooms=rooms, empty_rooms=empty_rooms)
    elif result_value <= 0:
        return render_template('admin.html', rooms=None)
    elif result_value1 <= 0:
        return render_template('admin.html', empty_rooms=None)
    
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    try:
        username = session['username']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')

    if request.method == 'POST':
        booking = request.form
        date_ = booking['datepicker']
        bedtype = booking['bedTypeSelect']
        contract = booking['contractDurationSelect']
        currr = mysql.connection.cursor()
        que = f"SELECT user_id FROM user WHERE username = '{username}'"
        currr.execute(que)
        user = currr.fetchone()
        if not date_:
            flash('Please select move-in date', 'danger')
            return redirect('/booking')
       
        session['booking_date'] = date_

        cur = mysql.connection.cursor()
        curr = mysql.connection.cursor()
        ccur = mysql.connection.cursor()
        queryStatement = f"""SELECT * FROM rooms WHERE room_type_id = '{bedtype}'"""
        booking_list = cur.execute(queryStatement)
        print(booking_list)
        queryStatement2 = (
            f"SELECT contract_type_id, price FROM contracttype "
            f"WHERE contract_length_id = '{contract}' AND room_type_id = '{bedtype}'"
        )
        ccur.execute(queryStatement2)
        contract_type = ccur.fetchone()
        if booking_list > 0:
            booking = cur.fetchall()
            bookings = []
            for bk in booking:
                if bk['contract_id'] is None:
                    bk['contract_type'] = contract
                    bk['selected_date'] = date_
                    bk['user_id'] = user['user_id']
                    bk['contract_type_id'] = contract_type['contract_type_id']
                    bk['price'] = contract_type['price']
                    bookings.append(bk)
                else:
                    queryStatement1 = (
                        f"SELECT c.end FROM contracts AS c "
                        f"JOIN rooms AS r ON c.contract_id = r.contract_id AND r.room_number = {bk['room_number']}"
                    )
                    checks = curr.execute(queryStatement1)
                    if checks > 0:
                        check = curr.fetchone()
                        if (check['end'] + relativedelta(months=1)) < datetime.strptime(date_, '%Y-%m-%d').date():
                            bk['contract_type'] = contract
                            bk['selected_date'] = date_
                            bk['user_id'] = user['user_id']
                            bk['contract_type_id'] = contract_type['contract_type_id']
                            bk['price'] = contract_type['price']
                            bookings.append(bk)
            print(bookings)
            flash('Successful.', 'success')
            return render_template('booking.html', bookings=bookings, selected_date=date_)

    return render_template('booking.html')

@app.route('/reserve/<booking>/<booking_date>', methods=['GET', 'POST'])
def reserve(booking, booking_date):
    cur = mysql.connection.cursor()
    curr = mysql.connection.cursor()
    booking = eval(booking)
    print(booking)

    if booking['contract_type'] == 's1':
        queryStatement = (
            f"INSERT INTO contracts (user_id, start, end, contract_type_id) "
            f"VALUES ({booking['user_id']}, '{booking['selected_date']}', "
            f"DATE_ADD('{booking['selected_date']}', INTERVAL 6 MONTH), "
            f"'{booking['contract_type_id']}')"
        )
        cur.execute(queryStatement)
        mysql.connection.commit()
        cur.close()

    else:
        queryStatement1 = (
            f"INSERT INTO contracts (user_id, start, end, contract_type_id) "
            f"VALUES ({booking['user_id']}, '{booking['selected_date']}', "
            f"DATE_ADD('{booking['selected_date']}', INTERVAL 1 YEAR), "
            f"'{booking['contract_type_id']}')"
        )

        curr.execute(queryStatement1)
        mysql.connection.commit()
        curr.close()
    ccur = mysql.connection.cursor()
    queryStatement2 = f"SELECT contract_id FROM contracts WHERE user_id = {booking['user_id']}"
    ccur.execute(queryStatement2)
    contract_id = ccur.fetchone()

    ccurr = mysql.connection.cursor()
    queryStatement3 = f"UPDATE rooms SET contract_id = {contract_id['contract_id']} WHERE room_number = {booking['room_number']}"
    ccurr.execute(queryStatement3)
    mysql.connection.commit()
    ccurr.close()

    flash('Successfully booked the room', 'success')
    return render_template('booking.html', bookings=booking, selected_date=booking_date)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    try:
        username = session['username']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')

    cur = mysql.connection.cursor()
    queryStatement = f"""SELECT * FROM user WHERE username = '{username}'"""
    user_profile = cur.execute(queryStatement)
    
    if user_profile > 0:
        user = cur.fetchall()

        queryStatement2 = f"""SELECT * FROM rooms WHERE contract_id IN (SELECT contract_id FROM contracts WHERE user_id = {user[0]['user_id']})"""
        room_result = cur.execute(queryStatement2)
        
        if room_result > 0:
            rooms = cur.fetchall()
        else:
            rooms = None
        
        selected_date = request.form.get('booking_date')
        
        return render_template('profile.html', user=user, rooms=rooms, selected_date=selected_date)
    
    return render_template('profile.html')

    
if __name__ == "__main__":
    app.run(debug=True)

