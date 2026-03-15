import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra",
    "cursorclass": pymysql.cursors.DictCursor
}

def update_schema():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()
    try:
        print("Updating status enum to include 'In Progress' and 'Cancelled'...")
        cursor.execute("""
            ALTER TABLE bookings 
            MODIFY COLUMN status ENUM(
                'Pending Platform Charge', 
                'Awaiting Labour Response', 
                'Confirmed', 
                'In Progress',
                'Completed', 
                'Rejected & Refunded', 
                'Cancelled'
            ) 
            DEFAULT 'Pending Platform Charge'
        """)
        db.commit()
        print("Schema update complete.")
    except Exception as e:
        print(f"Error during update: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    update_schema()
