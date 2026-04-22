import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra"
}

def migrate():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # Add new columns
            alter_queries = [
                "ALTER TABLE users ADD COLUMN aadhaar_front_image VARCHAR(255) DEFAULT NULL;",
                "ALTER TABLE users ADD COLUMN aadhaar_back_image VARCHAR(255) DEFAULT NULL;",
                "ALTER TABLE users ADD COLUMN address_proof_document VARCHAR(255) DEFAULT NULL;",
                "ALTER TABLE users ADD COLUMN area VARCHAR(100) DEFAULT NULL;"
            ]
            
            for query in alter_queries:
                try:
                    cursor.execute(query)
                    print(f"Executed: {query}")
                except Exception as e:
                    print(f"Error or already exists: {e}")
            
        connection.commit()
        print("Migration for zone and verification completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    migrate()
