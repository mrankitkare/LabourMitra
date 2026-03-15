import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra",
    "cursorclass": pymysql.cursors.DictCursor
}

CATEGORY_PRICING = {
    "Electrician": {"base": 1000, "min": 900, "max": 1200, "hr_base": 150, "hr_min": 120, "hr_max": 200},
    "Plumber": {"base": 900, "min": 800, "max": 1100, "hr_base": 130, "hr_min": 100, "hr_max": 180},
    "Helper": {"base": 600, "min": 500, "max": 800, "hr_base": 80, "hr_min": 60, "hr_max": 120},
    "Carpenter": {"base": 950, "min": 850, "max": 1150, "hr_base": 140, "hr_min": 110, "hr_max": 190},
    "Painter": {"base": 850, "min": 750, "max": 1050, "hr_base": 120, "hr_min": 90, "hr_max": 160}
}

def backfill():
    db = pymysql.connect(**DB_CONFIG)
    cursor = db.cursor()
    
    try:
        # Fetch all labourers with 0.00 current_hourly_rate
        cursor.execute("SELECT id, skill FROM users WHERE role='labour' AND (current_hourly_rate = 0 OR per_hour_rate = 0)")
        labours = cursor.fetchall()
        
        for lb in labours:
            skill = lb['skill']
            if skill in CATEGORY_PRICING:
                p = CATEGORY_PRICING[skill]
                print(f"Backfilling hourly rates for {lb['id']} ({skill})")
                cursor.execute("""
                    UPDATE users 
                    SET per_hour_rate=%s, 
                        current_hourly_rate=%s, 
                        hour_min_rate=%s, 
                        hour_max_rate=%s
                    WHERE id=%s
                """, (p['hr_base'], p['hr_base'], p['hr_min'], p['hr_max'], lb['id']))
        
        db.commit()
        print("Backfill complete.")
    except Exception as e:
        db.rollback()
        print(f"Error during backfill: {e}")
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    backfill()
