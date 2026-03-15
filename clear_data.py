import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

def clear_users():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete all users (cascades will handle bookings/reviews if defined correctly)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE reviews;")
        cursor.execute("TRUNCATE TABLE bookings;")
        cursor.execute("TRUNCATE TABLE users;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        conn.commit()
        print("✅ All registered users and their data have been deleted.")
    except Exception as e:
        print(f"❌ Error deleting users: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    clear_users()
