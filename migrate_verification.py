import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

db = pymysql.connect(**DB_CONFIG)
cursor = db.cursor()

try: cursor.execute("ALTER TABLE users ADD COLUMN aadhaar_number VARCHAR(20) DEFAULT NULL")
except: pass

try: cursor.execute("ALTER TABLE users ADD COLUMN profile_photo VARCHAR(255) DEFAULT NULL")
except: pass

try: cursor.execute("ALTER TABLE users ADD COLUMN id_proof_type VARCHAR(50) DEFAULT NULL")
except: pass

try: cursor.execute("ALTER TABLE users ADD COLUMN id_proof_image VARCHAR(255) DEFAULT NULL")
except: pass

try: cursor.execute("ALTER TABLE users ADD COLUMN verification_status VARCHAR(20) DEFAULT 'verified'") # Default verified for existing/customers
except: pass

# Set existing labours to verified so we don't break existing demo data
try: cursor.execute("UPDATE users SET verification_status='verified' WHERE role='labour' AND verification_status IS NULL")
except: pass

db.commit()
db.close()
print("Migration done")
