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

    try: cursor.execute("ALTER TABLE users ADD COLUMN latitude DECIMAL(10,8) DEFAULT NULL")
    except Exception as e: print("latitude:", e)

    try: cursor.execute("ALTER TABLE users ADD COLUMN longitude DECIMAL(11,8) DEFAULT NULL")
    except Exception as e: print("longitude:", e)

    # Drop existing foreign key before modifying the column to avoid errors in strict mode
    try:
        cursor.execute("""
            SELECT CONSTRAINT_NAME 
            FROM information_schema.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'bookings' AND COLUMN_NAME = 'labour_id' AND TABLE_SCHEMA = 'labourmitra' 
              AND CONSTRAINT_NAME != 'PRIMARY' AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        fk = cursor.fetchone()
        if fk:
            cursor.execute(f"ALTER TABLE bookings DROP FOREIGN KEY {fk[0]}")
    except Exception as e: print("drop fk:", e)

    try: cursor.execute("ALTER TABLE bookings MODIFY COLUMN labour_id INT NULL")
    except Exception as e: print("labour_id:", e)

    try: cursor.execute("ALTER TABLE bookings ADD CONSTRAINT fk_labour FOREIGN KEY (labour_id) REFERENCES users(id) ON DELETE CASCADE")
    except Exception as e: print("add fk:", e)

    try: cursor.execute("ALTER TABLE bookings ADD COLUMN customer_latitude DECIMAL(10,8) DEFAULT NULL")
    except Exception as e: print("c_lat:", e)

    try: cursor.execute("ALTER TABLE bookings ADD COLUMN customer_longitude DECIMAL(11,8) DEFAULT NULL")
    except Exception as e: print("c_lng:", e)
    
    try: cursor.execute("ALTER TABLE bookings ADD COLUMN assigned_at DATETIME DEFAULT NULL")
    except Exception as e: print("assigned_at:", e)
    
    # We might need a table to track which labour rejected or timed out
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_rejections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                labour_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY (labour_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
    except Exception as e: print("rejections table:", e)

    db.commit()
    db.close()
    print("Migration successful")
except Exception as e:
    print(e)
