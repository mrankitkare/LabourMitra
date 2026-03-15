from flask import Flask, render_template, request, redirect, url_for, session, g
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.err import IntegrityError
import datetime

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

    labours = []
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        category = request.form.get("category", "")
        city = request.form.get("city", "")

        cursor.execute("""
            SELECT id, name, category, city, average_rating, total_jobs, visiting_charge
            FROM users
            WHERE role='labour'
            AND available=1
            AND (%s='' OR category=%s)
            AND (%s='' OR city=%s)
        """, (category, category, city, city))
        labours = cursor.fetchall()
        for l in labours:
            l['visiting_charge'] = float(l['visiting_charge'] or VISITING_CHARGE)

    cursor.close()
    return render_template("customer_dashboard.html", 
                           labours=labours, 
                           name=session["name"], 
                           CATEGORIES=CATEGORIES,
                           ELECTRICIAN_SERVICES=ELECTRICIAN_SERVICES,
                           VISITING_CHARGE=VISITING_CHARGE)

# ---------------- SEND BOOKING ----------------
@app.route("/request/<int:labour_id>", methods=["POST"])
def send_request(labour_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    service_type = request.form.get("service_type")
    booking_date = request.form.get("booking_date")
    
    if not booking_date:
        return "Booking date required"
        
    cursor.execute("SELECT category FROM users WHERE id=%s", (labour_id,))
    labour_data = cursor.fetchone()
    category = labour_data['category'] if labour_data else None

    # Electrician requires service_type
    if category == "Electrician" and not service_type:
        return "Service type is required for Electrician"

    cursor.execute("""
        INSERT INTO bookings 
        (customer_id, labour_id, category, service_type, visiting_charge, booking_status, amount, payment_status, booking_date)
        VALUES (%s, %s, %s, %s, %s, 'Pending Platform Charge', %s, 'Pending', %s)
    """, (session["user_id"], labour_id, category, service_type, VISITING_CHARGE, PLATFORM_FEE, booking_date))

    booking_id = cursor.lastrowid
    db.commit()
    cursor.close()
    
    # Automatically redirect to payment (in real life this would go to a payment gateway)
    return redirect(url_for("pay_platform_charge", booking_id=booking_id))

# ---------------- PAY PLATFORM CHARGE ----------------
@app.route("/pay_platform_charge/<int:booking_id>")
def pay_platform_charge(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    # Move to 'Awaiting Labour Response'
    cursor.execute("""
        UPDATE bookings
        SET booking_status='Awaiting Labour Response', commission=%s, payment_status='Paid'
        WHERE id=%s AND customer_id=%s AND booking_status='Pending Platform Charge'
    """, (PLATFORM_FEE, booking_id, session["user_id"]))

    db.commit()
    cursor.close()

    return redirect(url_for("customer_bookings"))

# ---------------- CUSTOMER BOOKINGS ----------------
@app.route("/customer/bookings")
def customer_bookings():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.id, u.name, b.category, b.service_type, u.city,
               'Support: +91 XXXXX XXXXX' as caller_info,
               b.booking_status, b.payment_status, b.amount, b.booking_date, b.visiting_charge
        FROM bookings b
        JOIN users u ON b.labour_id = u.id
        WHERE b.customer_id=%s
        ORDER BY b.id DESC
    """, (session["user_id"],))

    bookings = cursor.fetchall()
    cursor.close()

    return render_template("customer_bookings.html", bookings=bookings, name=session["name"])

# ---------------- LABOUR DASHBOARD ----------------
@app.route("/labour/dashboard")
def labour_dashboard():
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.id, 
               CASE WHEN b.booking_status IN ('Confirmed', 'Completed') THEN u.name ELSE 'Customer' END as name,
               'Support: +91 XXXXX XXXXX' as caller_info,
               b.booking_status, b.booking_date, b.category, b.service_type, b.visiting_charge
        FROM bookings b
        JOIN users u ON b.customer_id = u.id
        WHERE b.labour_id=%s AND b.booking_status NOT IN ('Pending Platform Charge')
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
        WHERE id=%s AND labour_id=%s
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

    # If rejected, Mark status as 'Rejected & Refunded' and payment_status as Refunded
    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Rejected & Refunded', payment_status='Refunded'
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

    if booking:
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
