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

    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('credit', 'debit') NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Ensure wallet_balance exists in users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN wallet_balance DECIMAL(10, 2) DEFAULT 0.00")
    except:
        pass

    db.commit()
    db.close()
    print("Wallet migration successful")
except Exception as e:
    print(f"Error: {e}")
