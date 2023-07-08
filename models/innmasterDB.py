import sqlite3

conn = sqlite3.connect('innmaster.db')
c = conn.cursor()

#creating admin table

c.execute('''CREATE TABLE IF NOT EXISTS admin
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              password TEXT NOT NULL)''')

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
table_exists = c.fetchone()

if table_exists:
    print("admin table created successfully")
else:
    print("failed to create admin table")    
#c.execute("INSERT INTO admin (name, password) VALUES (?, ?)", ('ahmed', '0000'))

c.execute("SELECT * FROM admin")
rows = c.fetchall()
print(rows)

#creating room table

c.execute('''CREATE TABLE IF NOT EXISTS room
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              price INTEGER NOT NULL DEFAULT 0,
              availability BOOLEAN NOT NULL DEFAULT 0,
              guestid INTEGER)''')

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='room'")
table_exists = c.fetchone()

if table_exists:
    print("room table created successfully")
else:
    print("failed to create room table")

#c.execute("INSERT INTO room (price, availability, guestid) VALUES (?, ?, ?)", (5000, 0, 0))
#c.execute("INSERT INTO room (price, availability, guestid) VALUES (?, ?, ?)", (3000, 0, 0))
#c.execute("INSERT INTO room (price, availability, guestid) VALUES (?, ?, ?)", (4000, 0, 0))

c.execute("SELECT * FROM room")
ro = c.fetchall()
print(ro)

#creating roomrequests table

c.execute('''CREATE TABLE IF NOT EXISTS roomrequests
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              roomid INTEGER,
              guestname TEXT,
              checkoutdate DATE,
              gpassword TEXT)''')

#c.execute("DROP TABLE roomrequests;")

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roomrequests'")
table_exists = c.fetchone()

if table_exists:
    print("roomrequests table created successfully")
else:
    print("failed to create roomrequests table")
    
c.execute("SELECT * FROM roomrequests")
rrs = c.fetchall()
print(rrs)

#creating guests table

c.execute('''CREATE TABLE IF NOT EXISTS guests
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              password TEXT NOT NULL, bill INTEGER DEFAULT 0, balance INTEGER DEFAULT 100000)''')

#c.execute("DROP TABLE guests;")

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='guests'")
table_exists = c.fetchone()

if table_exists:
    print("guests table created successfully")
else:
    print("failed to create guests table")
    
c.execute("SELECT * FROM guests")
g = c.fetchall()
print(g)

#creating menu table

c.execute('''CREATE TABLE IF NOT EXISTS menu
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              itemname TEXT NOT NULL,
              itemprice INTEGER NOT NULL)''')

#c.execute("DROP TABLE menu;")

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu'")
table_exists = c.fetchone()

if table_exists:
    print("menu table created successfully")
else:
    print("failed to create menu table")
    
c.execute("SELECT * FROM guests")
m = c.fetchall()
print(m)

conn.commit()
conn.close()