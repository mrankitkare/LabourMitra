import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123"
}

def init_db():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Read SQL file
        with open('database.sql', 'r') as f:
            sql_script = f.read()

        # Split script into individual commands
        # Simple split by ; (might not handle complex cases but should work for this schema)
        commands = sql_script.split(';')
        
        for command in commands:
            if command.strip():
                cursor.execute(command)
        
        conn.commit()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()
