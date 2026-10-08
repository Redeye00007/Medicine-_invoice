import sqlite3


def connect():
    return sqlite3.connect("rms.db")



def create_db():

    con = connect()
    cur = con.cursor()


    # Admin User Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)


    # Default Admin
    cur.execute("""
    INSERT OR IGNORE INTO users
    (id,username,password)
    VALUES
    (1,'admin','1234')
    """)



    # Medicine Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        company TEXT,

        batch TEXT,

        expiry TEXT,

        buy REAL,

        sell REAL,

        stock INTEGER

    )
    """)



    # Invoice Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        supplier TEXT,

        date TEXT,

        total REAL

    )
    """)



    # Invoice Items Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        invoice_id INTEGER,

        product TEXT,

        qty INTEGER,

        price REAL,

        total REAL

    )
    """)



    con.commit()
    con.close()