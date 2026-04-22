import pymysql
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

db = pymysql.connect(**DB_CONFIG)
cursor = db.cursor()

try: 
    cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100) UNIQUE DEFAULT NULL")
except Exception as e: 
    pass

cursor.execute("SELECT id FROM users WHERE role='admin' AND email='ankitkare21@gmail.com'")
admin = cursor.fetchone()

if not admin:
    try:
        cursor.execute("""
            INSERT INTO users (name, email, mobile, password, role, verification_status)
            VALUES ('Admin', 'ankitkare21@gmail.com', 'N/A_ADMIN', %s, 'admin', 'verified')
        """, (generate_password_hash('Ankit@123'),))
        print("Admin seeded successfully.")
    except Exception as e:
        print("Error seeding admin:", e)
else:
    print("Admin already exists.")

db.commit()
db.close()
