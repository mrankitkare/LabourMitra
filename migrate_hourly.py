import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra",
    "cursorclass": pymysql.cursors.DictCursor
}

def migrate():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()
    
    try:
        # Update users table
        cursor.execute("ALTER TABLE users CHANGE COLUMN base_rate full_day_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN per_hour_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users CHANGE COLUMN current_rate current_full_day_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN current_hourly_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN hour_min_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN hour_max_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN proposed_hourly_rate DECIMAL(10, 2) DEFAULT 0.00")

        # Update bookings table
        cursor.execute("ALTER TABLE bookings ADD COLUMN booking_type ENUM('full_day', 'hourly') DEFAULT 'full_day'")
        cursor.execute("ALTER TABLE bookings ADD COLUMN selected_hours INT DEFAULT 0")
        cursor.execute("ALTER TABLE bookings ADD COLUMN start_time TIME NULL")
        cursor.execute("ALTER TABLE bookings ADD COLUMN end_time TIME NULL")
        
        db.commit()
        print("Migration successful: Added hourly booking support to users and bookings tables.")
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
