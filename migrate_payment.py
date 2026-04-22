import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

try:
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()

    try: cursor.execute("ALTER TABLE bookings ADD COLUMN estimate_amount DECIMAL(10,2) DEFAULT NULL")
    except: pass
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN final_work_cost DECIMAL(10,2) DEFAULT NULL")
    except: pass
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN visiting_charge_paid TINYINT(1) DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN work_cost_paid TINYINT(1) DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN platform_commission DECIMAL(10,2) DEFAULT 0.00")
    except: pass
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN labour_earnings DECIMAL(10,2) DEFAULT 0.00")
    except: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN wallet_balance DECIMAL(10,2) DEFAULT 0.00")
    except: pass

    # rename status if it exists
    try: cursor.execute("UPDATE bookings SET booking_status='Pending Payment' WHERE booking_status='Pending Platform Charge'")
    except: pass
    
    db.commit()
    db.close()
    print("Migration successful")
except Exception as e:
    print(e)
