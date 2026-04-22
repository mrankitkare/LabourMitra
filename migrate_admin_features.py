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
    CREATE TABLE IF NOT EXISTS disputes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        booking_id INT NOT NULL,
        raised_by INT NOT NULL,
        customer_or_labour VARCHAR(10),
        reason TEXT,
        status VARCHAR(20) DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Disputes table created")
except Exception as e:
    print(e)
    
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        setting_key VARCHAR(50) PRIMARY KEY,
        setting_value VARCHAR(255)
    )
    """)
    cursor.execute("INSERT IGNORE INTO settings (setting_key, setting_value) VALUES ('visiting_charge', '129')")
    cursor.execute("INSERT IGNORE INTO settings (setting_key, setting_value) VALUES ('commission_percent', '15')")
    print("Settings table created")
except Exception as e:
    print(e)

try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_blocked TINYINT(1) DEFAULT 0")
except Exception as e:
    pass

db.commit()
db.close()
print("Migration completed.")
