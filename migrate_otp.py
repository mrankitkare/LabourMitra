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
    cursor.execute("ALTER TABLE users ADD COLUMN otp_code VARCHAR(10) DEFAULT NULL")
except Exception as e:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry DATETIME DEFAULT NULL")
except Exception as e:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN failed_otp_attempts INT DEFAULT 0")
except Exception as e:
    pass

db.commit()
db.close()
print("OTP columns added successfully.")
