import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra",
    "cursorclass": pymysql.cursors.DictCursor
}

CATEGORY_PRICING = {
    "Electrician": {"base": 1000, "min": 900, "max": 1200},
    "Plumber": {"base": 900, "min": 800, "max": 1100},
    "Helper": {"base": 600, "min": 500, "max": 800},
    "Carpenter": {"base": 950, "min": 850, "max": 1150},
    "Painter": {"base": 850, "min": 750, "max": 1050}
}

def update_existing_labours():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()
    
    try:
        # Fetch all labours that have 0 base_rate
        cursor.execute("SELECT id, skill FROM users WHERE role='labour' AND base_rate=0.00")
        labours = cursor.fetchall()
        
        for labour in labours:
            skill = labour['skill']
            if skill in CATEGORY_PRICING:
                p = CATEGORY_PRICING[skill]
                cursor.execute("""
                    UPDATE users 
                    SET base_rate=%s, min_rate=%s, max_rate=%s, current_rate=%s
                    WHERE id=%s
                """, (p['base'], p['min'], p['max'], p['base'], labour['id']))
        
        db.commit()
        print(f"Updated {len(labours)} existing labourers with default pricing.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    update_existing_labours()
