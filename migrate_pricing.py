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
        # Add new columns to users table
        cursor.execute("ALTER TABLE users ADD COLUMN base_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN min_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN max_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN current_rate DECIMAL(10, 2) DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN average_rating FLOAT DEFAULT 0.00")
        cursor.execute("ALTER TABLE users ADD COLUMN total_jobs INT DEFAULT 0")
        cursor.execute("ALTER TABLE users ADD COLUMN pending_rate_approval BOOLEAN DEFAULT 0")
        cursor.execute("ALTER TABLE users ADD COLUMN proposed_rate DECIMAL(10, 2) DEFAULT 0.00")
        
        db.commit()
        print("Migration successful: Added pricing and rating columns to users table.")
    except Exception as e:
        print(f"Migration error: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    migrate()
