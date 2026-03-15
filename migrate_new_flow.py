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

    # Drop old pricing columns from users to clean it up (optional but good)
    cols_to_drop = ['full_day_rate', 'min_rate', 'max_rate', 'current_full_day_rate', 
                    'per_hour_rate', 'current_hourly_rate', 'hour_min_rate', 'hour_max_rate',
                    'pending_rate_approval', 'proposed_rate', 'proposed_hourly_rate']
    
    for col in cols_to_drop:
        try:
            cursor.execute(f"ALTER TABLE users DROP COLUMN {col}")
        except Exception as e: pass

    # rename skill to category
    try:
        cursor.execute("ALTER TABLE users CHANGE skill category VARCHAR(50) DEFAULT NULL")
    except Exception as e: print(e)
    
    # add visiting_charge to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN visiting_charge DECIMAL(10,2) DEFAULT 129.00")
    except Exception as e: print(e)

    # alter bookings table
    try:
        cursor.execute("ALTER TABLE bookings DROP COLUMN booking_type")
        cursor.execute("ALTER TABLE bookings DROP COLUMN selected_hours")
        cursor.execute("ALTER TABLE bookings DROP COLUMN start_time")
        cursor.execute("ALTER TABLE bookings DROP COLUMN end_time")
        cursor.execute("ALTER TABLE bookings DROP COLUMN applied_hourly_rate")
        cursor.execute("ALTER TABLE bookings DROP COLUMN pricing_tier")
        cursor.execute("ALTER TABLE bookings DROP COLUMN advance_amount")
    except Exception as e: print(e)

    try:
        cursor.execute("ALTER TABLE bookings CHANGE status booking_status VARCHAR(50) DEFAULT 'Pending Platform Charge'")
    except Exception as e: print(e)

    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN category VARCHAR(50) DEFAULT NULL")
    except Exception as e: print(e)

    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN service_type VARCHAR(100) DEFAULT NULL")
    except Exception as e: print(e)

    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN visiting_charge DECIMAL(10,2) DEFAULT 129.00")
    except Exception as e: print(e)
    
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN booking_date DATE DEFAULT NULL")
    except Exception as e: print(e)
    
    # Change payment_status enum
    try:
        cursor.execute("ALTER TABLE bookings MODIFY COLUMN payment_status VARCHAR(50) DEFAULT 'Pending'")
    except Exception as e: print(e)
    
    # Reset existing to Mason / etc if needed
    cursor.execute("UPDATE users SET category='Mason' WHERE category='Mason (Raj Mistri)'")

    db.commit()
    db.close()
    print("Migration successful")
except Exception as e:
    print(f"Error connecting or running: {e}")
