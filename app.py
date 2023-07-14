# from crypt import methods
from asyncio.windows_events import NULL
from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import sqlite3
import yaml

app = Flask(__name__)
app.secret_key = '1893'

cred = yaml.load(open('cred.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST'] = cred['mysql_host']
app.config['MYSQL_USER'] = cred['mysql_user']
app.config['MYSQL_PASSWORD'] = cred['mysql_password']
app.config['MYSQL_DB'] = cred['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


conn = sqlite3.connect('models/dormWEB.db')
con = conn.cursor()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/guest")
def guest():
    return render_template("guest.html")


@app.route("/auth_guest", methods=["POST"])
def auth_guest():
    guest_name = request.form["name"]
    guest_password = request.form["password"]
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT * FROM guests WHERE name=? AND password=?", (guest_name, guest_password))
        guest = con.fetchone()
        print(guest)
    if guest:
        session['user_id'] = guest[0]  # Set the user_id session variable to the guest's ID
        return redirect(url_for("guestdashboard"))
    else:
        return redirect(url_for("guestlogin"))


@app.route("/guestdashboard", methods=['GET', 'POST'])
def guestdashboard():
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, itemname, itemprice FROM menu")
        menu_items = con.fetchall()
        # Fetch room and guest details
        con.execute(
            "SELECT room.id, room.price, guests.id, guests.balance, guests.bill FROM room JOIN guests ON room.guestid = guests.id WHERE guests.id=?",
            (session["user_id"],))
        rows = con.fetchall()

    return render_template("guestdashboard.html", menu_items=menu_items, rows=rows)


@app.route("/order_item", methods=['POST'])
def order_item():
    item_id = request.form['item_id']
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT itemprice FROM menu WHERE id=?", (item_id,))
        item_price = con.fetchone()[0]
        con.execute("UPDATE guests SET bill = bill + ? WHERE id=?", (item_price, session["user_id"]))
        conn.commit()
        flash("Item ordered successfully", "item-order-success")

    return redirect(url_for("guestdashboard"))


@app.route("/pay_bill", methods=['POST'])
def pay_bill():
    amount_paid = float(request.form['amount'])
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT balance, bill FROM guests WHERE id=?", (session["user_id"],))
        guest_info = con.fetchone()
        balance = guest_info[0]
        current_bill = guest_info[1]
        if amount_paid > current_bill:
            flash("Amount paid cannot be greater than the current bill", "amt-danger")
        elif amount_paid > balance:
            flash("Amount paid cannot be greater than the available balance", "danger")
        else:
            new_balance = balance - amount_paid
            new_bill = current_bill - amount_paid
            con.execute("UPDATE guests SET balance = ?, bill=? WHERE id=?", (new_balance, new_bill, session["user_id"]))
            conn.commit()
            flash("Bill updated successfully", "amt-success")

    return redirect(url_for("guestdashboard"))


@app.route("/roomtable", methods=["GET", "POST"])
def roomtable():
    # Get the list of available rooms
    # conn = sqlite3.connect('models/dormWEB.db')
    # con = conn.cursor()
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, price FROM room WHERE availability = 0")
        rooms = con.fetchall()
        print(rooms)

    available_rooms = rooms
    room_list = []
    for room in available_rooms:
        room_dict = {}
        room_dict["id"] = room[0]
        room_dict["price"] = room[1]
        room_list.append(room_dict)

    # Render the booking form
    return render_template("bookroom.html", rooms=room_list)


@app.route("/bookroom", methods=["GET", "POST"])
def bookroom():
    # Get the list of available rooms
    # conn = sqlite3.connect('models/dormWEB.db')
    # con = conn.cursor()
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, price FROM room WHERE availability = 0")
        rooms = con.fetchall()
        print(rooms)

    available_rooms = rooms
    room_list = []
    for room in available_rooms:
        room_dict = {}
        room_dict["id"] = room[0]
        room_dict["price"] = room[1]
        room_list.append(room_dict)

    if request.method == "POST":
        # Handle form submission
        room_ids = request.form.getlist("room_id[]")
        # print("printing room ids",room_ids)
        name = request.form["name"]
        # print(name)
        password = request.form["password"]
        # print(password)
        checkout = request.form["checkout"]
        # print(checkout)

        # Create a new bookingrequest in the database
        # conn = sqlite3.connect('models/dormWEB.db')
        # co = conn.cursor()

        with sqlite3.connect('models/dormWEB.db') as conn:
            con = conn.cursor()
            for rid in room_ids:
                con.execute("INSERT INTO roomrequests (roomid, guestname, checkoutdate, gpassword) VALUES (?, ?, ?, ?)",
                            (rid, name, checkout, password))

            con.execute("SELECT * FROM roomrequests")
            result = con.fetchall()
            print(result)

        # Display a confirmation message to the user
        flash("Your booking has been submitted!", "booking-success")
        return redirect(url_for("bookroom"))
    # Render the bookroom template with the room information
    return render_template("bookroom.html", rooms=room_list)


@app.route("/admindashboard", methods=['GET', 'POST'])
def admindashboard():
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("SELECT roomid, guestname, checkoutdate FROM roomrequests")
        room_requests = con.fetchall()
        print("here", room_requests)

        # Fetch current guests
        con.execute(
            "SELECT guests.name, room.id, guests.id FROM guests JOIN room ON guests.id = room.guestid WHERE room.availability = 1")
        current_guests = con.fetchall()
        print(current_guests)

        # Fetch current menu items
        con.execute("SELECT id, itemname, itemprice FROM menu")
        current_menu = con.fetchall()
        # new
        if request.method == 'POST':
            room_id = request.form['room_id']
            guest_name = request.form['guest_name']
            checkout_date = request.form['checkout_date']

            con.execute("SELECT roomid, guestname, checkoutdate, gpassword FROM roomrequests WHERE roomid = ?",
                        (room_id))
            roomreqs = con.fetchone()
            print(roomreqs)
            con.execute("SELECT price FROM room WHERE id = ?", (room_id))
            roomprice = con.fetchone()
            print(roomprice)

            con.execute("INSERT INTO guests (name, password) VALUES (?, ?)", (roomreqs[1], roomreqs[3]))

            con.execute("SELECT id, bill, balance FROM guests WHERE (name = ?) AND (password = ?)",
                        (roomreqs[1], roomreqs[3]))
            gid = con.fetchone()
            print(gid)

            con.execute("UPDATE guests SET bill = ?, balance = ? WHERE id = ?",
                        (gid[1] + roomprice[0], gid[2] - roomprice[0], gid[0]))

            con.execute("UPDATE room SET availability = ?, guestid = ? WHERE id = ?", (1, gid[0], room_id))
            con.execute("DELETE FROM roomrequests WHERE roomid = ?", (room_id,))
            conn.commit()

            flash('Room request accepted!', 'room-success')
            return redirect(url_for('admindashboard'))
        # end new

    return render_template("admindashboard.html", room_requests=room_requests, current_guests=current_guests,
                           current_menu=current_menu)


@app.route("/remove_guest", methods=['POST'])
def remove_guest():
    guest_id = request.form['guest_id']
    print(guest_id)

    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        guest_id = request.form['guest_id']
        con.execute("UPDATE room SET availability = ?, guestid = NULL WHERE guestid = ?", (0, guest_id))
        con.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
        conn.commit()

        flash('Guest removed!', 'guest-rmv-success')
        return redirect(url_for('admindashboard'))


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
        return redirect('/')
    return render_template('write-review.html')


@app.route("/remove_menu_item", methods=['POST'])
def remove_menu_item():
    item_id = request.form['item_id']
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("DELETE FROM menu WHERE id = ?", (item_id,))
        conn.commit()
        flash('Menu item removed!', 'item-success')
    return redirect(url_for('admindashboard'))


@app.route("/add_menu_item", methods=['POST'])
def add_menu_item():
    item_name = request.form['itemname']
    print(item_name)
    item_price = request.form['itemprice']
    print(item_price)
    with sqlite3.connect('models/dormWEB.db') as conn:
        con = conn.cursor()
        con.execute("INSERT INTO menu (itemname, itemprice) VALUES (?, ?)", (item_name, item_price))
        conn.commit()
        flash('New menu item added!', 'item-success')
    return redirect(url_for('admindashboard'))


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

    if (user[0]['username'] == session['username']):
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
    queryStatement = f"SELECT * FROM rooms"
    print(queryStatement)
    result_value = cur.execute(queryStatement)
    if result_value > 0:
        rooms = cur.fetchall()
        return render_template('admin.html', rooms=rooms)
    else:
        return render_template('admin.html', rooms=None)

if __name__ == "__main__":
    app.run(debug=True)
