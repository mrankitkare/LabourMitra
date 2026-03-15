import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

def migrate():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()
    
    try:
        cursor.execute("DESCRIBE bookings")
        columns = [col[0] for col in cursor.fetchall()]
        
        if 'applied_hourly_rate' not in columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN applied_hourly_rate DECIMAL(10, 2) DEFAULT 0.00")
        if 'pricing_tier' not in columns:
            cursor.execute("ALTER TABLE bookings ADD COLUMN pricing_tier VARCHAR(20) DEFAULT NULL")
        
        # Rename user columns for consistency if requested (User mentioned specific names but current ones work)
        # I will keep the current user column names but ensure logic matches.
        
        db.commit()
        print("Migration successful: Added tier pricing columns to bookings table.")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
