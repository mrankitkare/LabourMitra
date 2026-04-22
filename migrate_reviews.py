import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

db = pymysql.connect(**DB_CONFIG)
cursor = db.cursor()

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INT AUTO_INCREMENT PRIMARY KEY,
        booking_id INT NOT NULL,
        customer_id INT NOT NULL,
        labour_id INT NOT NULL,
        rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY(booking_id)
    )
    """)
    print("reviews table created or already exists")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE users ADD COLUMN total_reviews INT DEFAULT 0")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE reviews ADD UNIQUE KEY(booking_id)")
except Exception as e:
    pass # maybe already exists

db.commit()
db.close()
