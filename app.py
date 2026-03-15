from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.err import IntegrityError
from datetime import datetime

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "labourmitra_secure_key"

# ---------------- DB CONFIG ----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ankit@@123",
    "database": "labourmitra",
    "cursorclass": pymysql.cursors.DictCursor
}

# ---------------- CONSTANTS ----------------
PLATFORM_FEE = 10
VISITING_CHARGE = 129

ELECTRICIAN_SERVICES = [
    "Fan Installation / Repair",
    "Switch Board Repair",
    "Light / Tube Light Installation",
    "House Wiring Work",
    "AC Power Connection",
    "Washing Machine Power Issue",
    "Inverter Connection",
    "Power Socket Repair",
    "MCB / Fuse Issue",
    "Other Electrical Problem"
]

CATEGORIES = [
    "Electrician",
    "Plumber",
    "Painter",
    "Mason (Raj Mistri)",
    "Helper / General Labour"
]

# ---------------- DB CONNECTION ----------------
def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        role = request.form["role"].lower()

        category = request.form.get("category") if role == "labour" else None
        city = request.form.get("city") if role == "labour" else None

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, mobile, password, role, category, city)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, mobile, hashed_password, role, category, city))
            db.commit()
            return redirect(url_for("login"))
        except IntegrityError:
            return render_template("register.html", error="⚠️ Mobile already registered", CATEGORIES=CATEGORIES)
        finally:
            cursor.close()

    return render_template("register.html", CATEGORIES=CATEGORIES)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE mobile=%s", (mobile,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['id']
            session["name"] = user['name']
            session["role"] = user['role']

            if user['role'] == "labour":
                return redirect(url_for("labour_dashboard"))
            elif user['role'] == "customer":
                return redirect(url_for("customer_dashboard"))
            else:
                return redirect(url_for("admin_dashboard"))

        return render_template("login.html", error="❌ Invalid mobile or password")

    return render_template("login.html")

# ---------------- CUSTOMER DASHBOARD ----------------
@app.route("/customer/dashboard", methods=["GET", "POST"])
def customer_dashboard():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    return render_template("customer_dashboard.html", 
                           name=session["name"], 
                           CATEGORIES=CATEGORIES,
                           ELECTRICIAN_SERVICES=ELECTRICIAN_SERVICES,
                           VISITING_CHARGE=VISITING_CHARGE)

# ---------------- API: NEARBY LABOUR FOR MAP ----------------
@app.route("/api/nearby_labours")
def nearby_labours():
    cat = request.args.get("category")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    
    if not lat or not lng:
        return jsonify([])

    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT id, name, latitude, longitude, category, average_rating, total_jobs
        FROM users
        WHERE role='labour' AND available=1 AND latitude IS NOT NULL AND longitude IS NOT NULL
    """
    params = []
    if cat:
        query += " AND category=%s"
        params.append(cat)
        
    cursor.execute(query, tuple(params))
    labours = cursor.fetchall()
    
    # Filter by 10km manually or we let frontend show them
    # For now just return all online labours in that category
    return jsonify(labours)

# ---------------- SEND BOOKING ----------------
@app.route("/request", methods=["POST"])
def send_request():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    category = request.form.get("category")
    service_type = request.form.get("service_type")
    booking_date = request.form.get("booking_date")
    lat = request.form.get("customer_latitude")
    lng = request.form.get("customer_longitude")
    
    if not booking_date or not lat or not lng or not category:
        return "Missing Required Fields (Date, Location, Category)"
        
    if category == "Electrician" and not service_type:
        return "Service type is required for Electrician"

    cursor.execute("""
        INSERT INTO bookings 
        (customer_id, labour_id, category, service_type, visiting_charge, booking_status, amount, payment_status, booking_date, customer_latitude, customer_longitude)
        VALUES (%s, NULL, %s, %s, %s, 'Pending Platform Charge', %s, 'Pending', %s, %s, %s)
    """, (session["user_id"], category, service_type, VISITING_CHARGE, PLATFORM_FEE, booking_date, lat, lng))

    booking_id = cursor.lastrowid
    db.commit()
    cursor.close()
    
    return redirect(url_for("pay_platform_charge", booking_id=booking_id))

# ---------------- PAY PLATFORM CHARGE ----------------
@app.route("/pay_platform_charge/<int:booking_id>")
def pay_platform_charge(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    # Move to 'Searching for Labour'
    cursor.execute("""
        UPDATE bookings
        SET booking_status='Searching for Labour', commission=%s, payment_status='Paid'
        WHERE id=%s AND customer_id=%s AND booking_status='Pending Platform Charge'
    """, (PLATFORM_FEE, booking_id, session["user_id"]))

    db.commit()
    cursor.close()

    return redirect(url_for("booking_status_page", booking_id=booking_id))

# ---------------- BOOKING STATUS UI ----------------
@app.route("/booking_status/<int:booking_id>")
def booking_status_page(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))
    return render_template("booking_status.html", booking_id=booking_id)

# ---------------- API: BOOKING MATCHING ENGINE ----------------
@app.route("/api/matching/<int:booking_id>")
def booking_matching(booking_id):
    if session.get("role") != "customer":
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM bookings WHERE id=%s AND customer_id=%s", (booking_id, session['user_id']))
    booking = cursor.fetchone()
    
    if not booking:
        return jsonify({"error": "Not Found"}), 404

    status = booking['booking_status']
    
    if status in ['Accepted', 'Confirmed', 'Completed', 'Rejected & Refunded']:
        return jsonify({"status": status})

    if status == 'Request Sent':
        # Check if 30s passed
        assigned_at = booking['assigned_at']
        if assigned_at and (datetime.now() - assigned_at).total_seconds() >= 30:
            # Labour missed it
            cursor.execute("INSERT INTO booking_rejections (booking_id, labour_id) VALUES (%s, %s)", (booking_id, booking['labour_id']))
            cursor.execute("UPDATE bookings SET labour_id=NULL, booking_status='Searching for Labour', assigned_at=NULL WHERE id=%s", (booking_id,))
            db.commit()
            return jsonify({"status": "Searching for Labour"})
        else:
            return jsonify({"status": "Request Sent", "seconds_left": 30 - int((datetime.now() - assigned_at).total_seconds() if assigned_at else 0)})

    if status == 'Searching for Labour':
        # Auto Matching logic
        # 1. Same category
        # 2. available = 1
        # 3. Not rejected before
        # 4. Doesn't have an active booking
        # 5. Distance <= 10km
        
        c_lat = booking['customer_latitude']
        c_lng = booking['customer_longitude']
        
        if c_lat and c_lng:
            query = """
                SELECT id, 
                  (6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(latitude))
                  )) AS distance
                FROM users 
                WHERE role='labour' AND category=%s AND available=1
                  AND id NOT IN (SELECT labour_id FROM booking_rejections WHERE booking_id=%s)
                  AND id NOT IN (SELECT labour_id FROM bookings WHERE booking_status IN ('Request Sent', 'Confirmed') AND labour_id IS NOT NULL)
                HAVING distance <= 10
                ORDER BY distance ASC, average_rating DESC, total_jobs DESC
                LIMIT 1
            """
            cursor.execute(query, (c_lat, c_lng, c_lat, booking['category'], booking_id))
            candidate = cursor.fetchone()
            
            if candidate:
                cursor.execute("""
                    UPDATE bookings 
                    SET labour_id=%s, booking_status='Request Sent', assigned_at=NOW() 
                    WHERE id=%s
                """, (candidate['id'], booking_id))
                db.commit()
                return jsonify({"status": "Request Sent", "assigned_labour_id": candidate['id']})
                
        return jsonify({"status": "Searching for Labour"})

    return jsonify({"status": status})

# ---------------- CUSTOMER BOOKINGS ----------------
@app.route("/customer/bookings")
def customer_bookings():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.id, IFNULL(u.name, 'Searching...') as name, b.category, b.service_type, IFNULL(u.city, 'N/A') as city,
               'Support: +91 XXXXX XXXXX' as caller_info,
               b.booking_status, b.payment_status, b.amount, b.booking_date, b.visiting_charge
        FROM bookings b
        LEFT JOIN users u ON b.labour_id = u.id
        WHERE b.customer_id=%s AND b.booking_status != 'Pending Platform Charge'
        ORDER BY b.id DESC
    """, (session["user_id"],))

    bookings = cursor.fetchall()
    cursor.close()

    return render_template("customer_bookings.html", bookings=bookings, name=session["name"])


# ---------------- API: LABOUR UPDATE LOCATION ----------------
@app.route("/labour/update_location", methods=["POST"])
def update_location():
    if session.get("role") != "labour":
        return jsonify({"error": "Unauthorized"}), 401
        
    lat = request.json.get("lat")
    lng = request.json.get("lng")
    
    if lat and lng:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET latitude=%s, longitude=%s WHERE id=%s", (lat, lng, session["user_id"]))
        db.commit()
        return jsonify({"success": True})
        
    return jsonify({"error": "Bad Request"}), 400

# ---------------- LABOUR DASHBOARD ----------------
@app.route("/labour/dashboard")
def labour_dashboard():
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    
    # We first sync any timed out requests sent to this labour
    # To ensure they don't see it if it's past 30s
    cursor.execute("""
        SELECT id, assigned_at FROM bookings 
        WHERE labour_id=%s AND booking_status='Request Sent'
    """, (session['user_id'],))
    active_requests = cursor.fetchall()
    
    for req in active_requests:
        assigned_at = req['assigned_at']
        if assigned_at and (datetime.now() - assigned_at).total_seconds() >= 30:
            cursor.execute("INSERT INTO booking_rejections (booking_id, labour_id) VALUES (%s, %s)", (req['id'], session['user_id']))
            cursor.execute("UPDATE bookings SET labour_id=NULL, booking_status='Searching for Labour', assigned_at=NULL WHERE id=%s", (req['id'],))
            db.commit()

    cursor.execute("""
        SELECT b.id, 
               CASE WHEN b.booking_status IN ('Confirmed', 'Completed') THEN u.name ELSE 'Customer' END as name,
               'Support: +91 XXXXX XXXXX' as caller_info,
               b.booking_status, b.booking_date, b.category, b.service_type, b.visiting_charge, b.customer_latitude, b.customer_longitude
        FROM bookings b
        JOIN users u ON b.customer_id = u.id
        WHERE b.labour_id=%s AND b.booking_status IN ('Request Sent', 'Confirmed', 'Completed')
        ORDER BY b.id DESC
    """, (session["user_id"],))

    requests = cursor.fetchall()
    
    cursor.execute("""
        SELECT category, average_rating, total_jobs, visiting_charge
        FROM users WHERE id=%s
    """, (session["user_id"],))
    labour_profile = cursor.fetchone()

    cursor.close()

    return render_template("labour_dashboard.html", 
                           requests=requests, 
                           name=session["name"], 
                           profile=labour_profile)

# ---------------- ACCEPT ----------------
@app.route("/accept/<int:booking_id>")
def accept_booking(booking_id):
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Confirmed'
        WHERE id=%s AND labour_id=%s AND booking_status='Request Sent'
    """, (booking_id, session["user_id"]))

    db.commit()
    cursor.close()

    return redirect(url_for("labour_dashboard"))

# ---------------- REJECT ----------------
@app.route("/reject/<int:booking_id>")
def reject_booking(booking_id):
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    # If rejected, it should go back to pool, not 'Rejected & Refunded' 
    # unless we decide to refund completely after max retries.
    # Currently it just goes back to Searching for Labour
    cursor.execute("INSERT INTO booking_rejections (booking_id, labour_id) VALUES (%s, %s)", (booking_id, session['user_id']))
    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Searching for Labour', labour_id=NULL, assigned_at=NULL
        WHERE id=%s AND labour_id=%s
    """, (booking_id, session["user_id"]))

    db.commit()
    cursor.close()

    return redirect(url_for("labour_dashboard"))

# ---------------- COMPLETE ----------------
@app.route("/complete/<int:booking_id>")
def complete_booking(booking_id):
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Completed'
        WHERE id=%s AND labour_id=%s
    """, (booking_id, session["user_id"]))

    cursor.execute("UPDATE users SET available=1 WHERE id=%s", (session["user_id"],))
    cursor.execute("UPDATE users SET total_jobs = total_jobs + 1 WHERE id=%s", (session["user_id"],))

    db.commit()
    cursor.close()

    return redirect(url_for("labour_dashboard"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return "Access Denied"

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM bookings")
    total_bookings = cursor.fetchone()['count']

    cursor.execute("SELECT SUM(commission) as total FROM bookings WHERE payment_status='Paid'")
    total_earnings = cursor.fetchone()['total'] or 0

    cursor.close()

    return render_template("admin.html",
                           total_users=total_users,
                           total_bookings=total_bookings,
                           total_earnings=total_earnings)

# ---------------- ADD REVIEW ----------------
@app.route("/review/<int:booking_id>", methods=["POST"])
def add_review(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    rating = request.form.get("rating")
    comment = request.form.get("comment")

    db = get_db()
    cursor = db.cursor()

    # Get labour_id
    cursor.execute("SELECT labour_id FROM bookings WHERE id=%s", (booking_id,))
    booking = cursor.fetchone()

    if booking and booking['labour_id']:
        cursor.execute("""
            INSERT INTO reviews (booking_id, customer_id, labour_id, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, session["user_id"], booking['labour_id'], rating, comment))
        
        cursor.execute("""
            UPDATE users SET average_rating = (
                SELECT AVG(rating) FROM reviews WHERE labour_id = %s
            ) WHERE id = %s
        """, (booking['labour_id'], booking['labour_id']))
        
        db.commit()

    cursor.close()
    return redirect(url_for("customer_bookings"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
