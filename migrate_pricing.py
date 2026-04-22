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

    try: cursor.execute("ALTER TABLE bookings ADD COLUMN booking_type VARCHAR(20) DEFAULT 'visit'")
    except Exception as e: print(e)
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN selected_hours INT DEFAULT NULL")
    except Exception as e: print(e)
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN applied_rate DECIMAL(10,2) DEFAULT NULL")
    except Exception as e: print(e)

    db.commit()
    db.close()
    print("Migration successful")
except Exception as e:
    print(e)
