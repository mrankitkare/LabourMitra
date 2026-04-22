from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymysql.err import IntegrityError
from datetime import datetime, timedelta
import os
import random
import requests
import razorpay
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

# ---------------- CONFIG ----------------
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "YOUR_API_KEY_HERE")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_YOUR_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "YOUR_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def send_otp_sms(mobile, otp):
    """
    Sends OTP via Fast2SMS API.
    In development, it also prints to console.
    """
    print(f"\n" + "="*40)
    print(f"OTP SENT TO: {mobile} | CODE: {otp}")
    print("="*40 + "\n")
    
    if FAST2SMS_API_KEY == "YOUR_API_KEY_HERE":
        return True
        
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = f"variables_values={otp}&route=otp&numbers={mobile}"
    headers = {
        'authorization': FAST2SMS_API_KEY,
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
    }
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        return response.json().get('return', False)
    except Exception as e:
        print(f"SMS API Error: {e}")
        return False

def generate_otp():
    return str(random.randint(100000, 999999))

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "labourmitra_secure_key"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB CONFIG ----------------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "Ankit@@123"),
    "database": os.environ.get("DB_NAME", "labourmitra"),
    "port": int(os.environ.get("DB_PORT", 3306)),
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
    "Helper / General Labour",
    "AC Repair / Installation",
    "Appliance Repair (Washing Machine / Fridge)"
]

VISITING_CHARGE_CATEGORIES = [
    "Electrician",
    "Plumber",
    "AC Repair / Installation",
    "Appliance Repair (Washing Machine / Fridge)"
]

HOURLY_PRICING = {
    "Painter": {"full_day": 850, "hourly": 150},
    "Mason (Raj Mistri)": {"full_day": 1200, "hourly": 200},
    "Helper / General Labour": {"full_day": 600, "hourly": 120}
}


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
        try:
            name = request.form.get("name")
            mobile = request.form.get("mobile")
            password = request.form.get("password")
            role = request.form.get("role", "").lower()

            if not name or not mobile or not password or not role:
                return render_template("register.html", error="Please fill all required fields", CATEGORIES=CATEGORIES)

            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE mobile=%s", (mobile,))
            if cursor.fetchone():
                cursor.close()
                return render_template("register.html", error="Mobile number already registered", CATEGORIES=CATEGORIES)
            cursor.close()

            # Handle extra fields for labour
            category = request.form.get("category") if role == "labour" else None
            city = request.form.get("city") if role == "labour" else None
            area = request.form.get("area") if role == "labour" else None
            aadhaar_number = request.form.get("aadhaar_number")
            id_proof_type = request.form.get("id_proof_type")

            profile_photo = None
            id_proof_image = None
            aadhaar_front = None
            aadhaar_back = None
            address_proof = None

            if role == "labour":
                def save_file(file, prefix):
                    if file and file.filename:
                        filename = secure_filename(f"{prefix}_{mobile}_{file.filename}")
                        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(path)
                        return filename
                    return None

                profile_photo = save_file(request.files.get("profile_photo"), "profile")
                id_proof_image = save_file(request.files.get("id_proof_image"), "id")
                aadhaar_front = save_file(request.files.get("aadhaar_front"), "front")
                aadhaar_back = save_file(request.files.get("aadhaar_back"), "back")
                address_proof = save_file(request.files.get("address_proof"), "addr")

            otp = generate_otp()
            expiry = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

            session['reg_data'] = {
                'name': name,
                'mobile': mobile,
                'password': generate_password_hash(password),
                'role': role,
                'category': category,
                'city': city,
                'area': area,
                'aadhaar_number': aadhaar_number,
                'id_proof_type': id_proof_type,
                'profile_photo': profile_photo,
                'id_proof_image': id_proof_image,
                'aadhaar_front': aadhaar_front,
                'aadhaar_back': aadhaar_back,
                'address_proof': address_proof,
                'otp': otp,
                'expiry': expiry
            }

            send_otp_sms(mobile, otp)
            return redirect(url_for("verify_register_otp"))

        except Exception as e:
            print("Registration Error:", e)
            return render_template("register.html", error=f"An error occurred: {str(e)}", CATEGORIES=CATEGORIES)

    return render_template("register.html", CATEGORIES=CATEGORIES)

@app.route("/verify-register-otp", methods=["GET", "POST"])
def verify_register_otp():
    reg_data = session.get('reg_data')
    if not reg_data:
        return redirect(url_for("register"))

    if request.method == "POST":
        otp_entered = request.form.get("otp")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if now > reg_data['expiry']:
            return render_template("verify_otp.html", action="register", mobile=reg_data['mobile'], error="OTP Expired. Please register again.")

        if otp_entered == reg_data['otp']:
            try:
                db = get_db()
                cursor = db.cursor()
                
                sql = """
                    INSERT INTO users (name, mobile, password, role, category, city, area, 
                                     aadhaar_number, id_proof_type, profile_photo, id_proof_image, 
                                     aadhaar_front_image, aadhaar_back_image, address_proof_document,
                                     verification_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Labours start as pending, customers don't need verification usually (or start as verified)
                v_status = 'pending' if reg_data['role'] == 'labour' else 'approved'
                
                cursor.execute(sql, (
                    reg_data['name'], reg_data['mobile'], reg_data['password'], reg_data['role'], 
                    reg_data['category'], reg_data['city'], reg_data['area'],
                    reg_data['aadhaar_number'], reg_data['id_proof_type'], 
                    reg_data['profile_photo'], reg_data['id_proof_image'],
                    reg_data['aadhaar_front'], reg_data['aadhaar_back'], reg_data['address_proof'],
                    v_status
                ))
                
                db.commit()
                cursor.close()
                session.pop('reg_data', None)
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
                
            except IntegrityError:
                return render_template("verify_otp.html", action="register", mobile=reg_data['mobile'], error="Mobile number already registered.")
            except Exception as e:
                print("Verification Error:", e)
                return render_template("verify_otp.html", action="register", mobile=reg_data['mobile'], error=f"Database error: {str(e)}")
        else:
            return render_template("verify_otp.html", action="register", mobile=reg_data['mobile'], error="Invalid OTP.", demo_otp=reg_data['otp'])

    return render_template("verify_otp.html", action="register", mobile=reg_data['mobile'], demo_otp=reg_data['otp'])

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_type = request.form.get("login_type", "password")
        mobile = request.form["mobile"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE mobile=%s", (mobile,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            return render_template("login.html", error="❌ Mobile number not found")
        if user['is_blocked']:
            cursor.close()
            return render_template("login.html", error="❌ Account is blocked")

        if login_type == "password":
            password = request.form.get("password")
            if check_password_hash(user['password'], password):
                cursor.close()
                session["user_id"] = user['id']
                session["name"] = user['name']
                session["role"] = user['role']
                flash(f"Debug: Successfully logged in as {user['role'].upper()}", "success")
                if user['role'] == "admin": return redirect(url_for("admin_dashboard"))
                if user['role'] == "labour": return redirect(url_for("labour_dashboard"))
                return redirect(url_for("customer_dashboard"))
            cursor.close()
            return render_template("login.html", error="❌ Invalid password")
        
        elif login_type == "otp":
            otp = generate_otp()
            expiry = (datetime.now() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
            
            send_otp_sms(mobile, otp)
            
            cursor.execute("UPDATE users SET otp_code=%s, otp_expiry=%s, failed_otp_attempts=0 WHERE id=%s", (otp, expiry, user['id']))

    return render_template("login.html")

@app.route("/verify-login-otp", methods=["GET", "POST"])
def verify_login_otp():
    mobile = session.get('login_mobile')
    if not mobile: return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE mobile=%s", (mobile,))
    user = cursor.fetchone()

    if request.method == "POST":
        otp_entered = request.form.get("otp")
        now = datetime.now()
        
        if not user['otp_code'] or not user['otp_expiry'] or now > user['otp_expiry']:
            cursor.close()
            return render_template("verify_otp.html", action="login", error="OTP expired. Request a new one.", mobile=mobile)

        if user['failed_otp_attempts'] >= 3:
            cursor.execute("UPDATE users SET is_blocked=1 WHERE id=%s", (user['id'],))
            db.commit()
            cursor.close()
            session.pop('login_mobile', None)
            return render_template("login.html", error="Account blocked due to too many failed OTP attempts.")

        if otp_entered == user['otp_code']:
            cursor.execute("UPDATE users SET otp_code=NULL, otp_expiry=NULL, failed_otp_attempts=0 WHERE id=%s", (user['id'],))
            db.commit()
            cursor.close()
            session.pop('login_mobile', None)
            
            session["user_id"] = user['id']
            session["name"] = user['name']
            session["role"] = user['role']
            flash(f"Debug: Successfully logged in as {user['role'].upper()}", "success")
            if user['role'] == "admin": return redirect(url_for("admin_dashboard"))
            if user['role'] == "labour": return redirect(url_for("labour_dashboard"))
            return redirect(url_for("customer_dashboard"))
        
        cursor.execute("UPDATE users SET failed_otp_attempts = failed_otp_attempts + 1 WHERE id=%s", (user['id'],))
        db.commit()
        cursor.close()
        return render_template("verify_otp.html", action="login", error="Invalid OTP", mobile=mobile, demo_otp=user['otp_code'])
        
    cursor.close()
    return render_template("verify_otp.html", action="login", mobile=mobile, demo_otp=user['otp_code'])

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        mobile = request.form.get("mobile")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE mobile=%s AND role != 'admin'", (mobile,))
        user = cursor.fetchone()
        
        if not user:
             cursor.close()
             return render_template("forgot_password.html", error="Mobile number not found")
             
        otp = generate_otp()
        expiry = (datetime.now() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        
        send_otp_sms(mobile, otp)
        
        cursor.execute("UPDATE users SET otp_code=%s, otp_expiry=%s, failed_otp_attempts=0 WHERE id=%s", (otp, expiry, user['id']))
        db.commit()
        cursor.close()
        
        session['forgot_mobile'] = mobile
        return redirect(url_for("verify_forgot_otp"))
        
    return render_template("forgot_password.html")

@app.route("/verify-forgot-otp", methods=["GET", "POST"])
def verify_forgot_otp():
    mobile = session.get('forgot_mobile')
    if not mobile: return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE mobile=%s", (mobile,))
    user = cursor.fetchone()

    if request.method == "POST":
        otp_entered = request.form.get("otp")
        now = datetime.now()
        
        if not user['otp_code'] or not user['otp_expiry'] or now > user['otp_expiry']:
            cursor.close()
            return render_template("verify_otp.html", action="forgot", error="OTP expired. Request a new one.", mobile=mobile)

        if user['failed_otp_attempts'] >= 3:
            cursor.execute("UPDATE users SET is_blocked=1 WHERE id=%s", (user['id'],))
            db.commit()
            cursor.close()
            session.pop('forgot_mobile', None)
            return render_template("login.html", error="Account blocked due to too many failed OTP attempts.")

        if otp_entered == user['otp_code']:
            cursor.execute("UPDATE users SET otp_code=NULL, otp_expiry=NULL, failed_otp_attempts=0 WHERE id=%s", (user['id'],))
            db.commit()
            cursor.close()
            session['reset_mobile'] = mobile
            session.pop('forgot_mobile', None)
            return redirect(url_for("reset_password"))
            
        cursor.execute("UPDATE users SET failed_otp_attempts = failed_otp_attempts + 1 WHERE id=%s", (user['id'],))
        db.commit()
        cursor.close()
        return render_template("verify_otp.html", action="forgot", error="Invalid OTP", mobile=mobile, demo_otp=user['otp_code'])
        
    cursor.close()
    return render_template("verify_otp.html", action="forgot", mobile=mobile, demo_otp=user['otp_code'])

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    mobile = session.get('reset_mobile')
    if not mobile: return redirect(url_for("login"))
    
    if request.method == "POST":
        password = request.form.get("password")
        hashed = generate_password_hash(password)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET password=%s WHERE mobile=%s", (hashed, mobile))
        db.commit()
        cursor.close()
        session.pop('reset_mobile', None)
        return redirect(url_for("login"))
        
    return render_template("reset_password.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND role='admin'", (email,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin['password'], password):
            session["user_id"] = admin['id']
            session["name"] = admin['name']
            session["role"] = admin['role']
            flash(f"Debug: Successfully logged in as ADMIN", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", error="❌ Invalid admin credentials")

    return render_template("admin_login.html")

# ---------------- CUSTOMER DASHBOARD ----------------
@app.route("/customer/dashboard", methods=["GET", "POST"])
def customer_dashboard():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
    wallet_balance = float(cursor.fetchone()['wallet_balance'] or 0)
    cursor.close()

    return render_template("customer_dashboard.html", 
                           name=session["name"], 
                           wallet_balance=wallet_balance,
                           CATEGORIES=CATEGORIES,
                           ELECTRICIAN_SERVICES=ELECTRICIAN_SERVICES)

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
        SELECT id, name, latitude, longitude, category, IFNULL(average_rating, 0) as average_rating, total_jobs, IFNULL(total_reviews, 0) as total_reviews, available
        FROM users
        WHERE role='labour' AND verification_status='approved' AND latitude IS NOT NULL AND longitude IS NOT NULL
    """
    params = []
    if cat:
        query += " AND category=%s"
        params.append(cat)
        
    cursor.execute(query, tuple(params))
    labours = cursor.fetchall()
    for l in labours:
        l['latitude'] = float(l['latitude']) if l['latitude'] is not None else None
        l['longitude'] = float(l['longitude']) if l['longitude'] is not None else None
    
    return jsonify(labours)

# ---------------- SEND BOOKING ----------------
@app.route("/prepare_booking", methods=["POST"])
def prepare_booking():
    if session.get("role") != "customer": return redirect(url_for("login"))
    
    session['pending_booking'] = {
        'category': request.form.get("category"),
        'service_type': request.form.get("service_type"),
        'booking_date': request.form.get("booking_date"),
        'lat': request.form.get("customer_latitude"),
        'lng': request.form.get("customer_longitude"),
        'booking_type': request.form.get("booking_type"),
        'selected_hours': request.form.get("selected_hours")
    }
    
    # Redirect to static Razorpay link
    return redirect("https://rzp.io/rzp/V9aelm0")

@app.route("/payment-success")
def payment_success():
    if 'pending_booking' in session:
        data = session.pop('pending_booking')
        
        db = get_db()
        cursor = db.cursor()
        
        visiting_charge_val = None
        if data['category'] in VISITING_CHARGE_CATEGORIES:
            visiting_charge_val = 129
            
        applied_rate = None
        estimate_val = None
        if data['category'] in HOURLY_PRICING:
            p = HOURLY_PRICING[data['category']]
            if data['booking_type'] == "full_day":
                applied_rate = p['full_day']
                estimate_val = p['full_day']
            else:
                applied_rate = p['hourly']
                estimate_val = float(data['selected_hours']) * p['hourly']

        cursor.execute("""
            INSERT INTO bookings 
            (customer_id, category, service_type, visiting_charge, platform_fee, booking_date, 
             customer_latitude, customer_longitude, booking_status, payment_status, booking_type, selected_hours, applied_rate, estimate_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed', 'Paid', %s, %s, %s, %s)
        """, (session["user_id"], data['category'], data['service_type'], visiting_charge_val, 10.0, data['booking_date'], 
              data['lat'], data['lng'], data['booking_type'], data['selected_hours'], applied_rate, estimate_val))
        
        db.commit()
        cursor.close()
        
        # Set a flag to prevent re-creation but allow showing success message
        session['last_payment_success'] = True
        return render_template("payment_result.html", status="success")
    
    elif session.get('last_payment_success'):
        return render_template("payment_result.html", status="already_done")
    
    return redirect(url_for('customer_dashboard'))

@app.route("/payment-failed")
def payment_failed():
    session.pop('pending_booking', None)
    return render_template("payment_result.html", status="failed")

# ---------------- PAY PLATFORM CHARGE ----------------
@app.route("/pay_platform_charge/<int:booking_id>")
def pay_platform_charge(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    # Check balance
    cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
    balance = float(cursor.fetchone()['wallet_balance'] or 0)
    
    if balance < PLATFORM_FEE:
        flash(f"Insufficient wallet balance. You need ₹{PLATFORM_FEE}. Please add money.", "warning")
        return redirect(url_for("wallet_history"))

    # Deduct
    cursor.execute("UPDATE users SET wallet_balance = wallet_balance - %s WHERE id=%s", (PLATFORM_FEE, session["user_id"]))
    cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'debit', %s, %s)", 
                   (session["user_id"], PLATFORM_FEE, f"Platform fee for Booking #{booking_id}"))

    cursor.execute("""
        UPDATE bookings
        SET booking_status='Searching for Labour', commission=%s, payment_status='Paid'
        WHERE id=%s AND customer_id=%s AND booking_status='Pending Payment'
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
    
    cursor.execute("""
        SELECT b.*, u.area as customer_area 
        FROM bookings b 
        JOIN users u ON b.customer_id = u.id 
        WHERE b.id=%s AND b.customer_id=%s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()
    
    if not booking:
        return jsonify({"error": "Not Found"}), 404

    status = booking['booking_status']
    
    if status not in ['Request Sent', 'Searching for Labour']:
        return jsonify({"status": status})

    if status == 'Request Sent':
        assigned_at = booking['assigned_at']
        if assigned_at and (datetime.now() - assigned_at).total_seconds() >= 30:
            cursor.execute("INSERT INTO booking_rejections (booking_id, labour_id) VALUES (%s, %s)", (booking_id, booking['labour_id']))
            cursor.execute("UPDATE bookings SET labour_id=NULL, booking_status='Searching for Labour', assigned_at=NULL WHERE id=%s", (booking_id,))
            db.commit()
            return jsonify({"status": "Searching for Labour"})
        else:
            return jsonify({"status": "Request Sent", "seconds_left": 30 - int((datetime.now() - assigned_at).total_seconds() if assigned_at else 0)})

    if status == 'Searching for Labour':
        c_lat = booking['customer_latitude']
        c_lng = booking['customer_longitude']
        
        if c_lat and c_lng:
            query = """
                SELECT id, 
                  (6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) * 
                    cos(radians(longitude) - radians(%s)) + 
                    sin(radians(%s)) * sin(radians(latitude))
                  )) AS distance,
                  (CASE WHEN area = %s THEN 1 ELSE 0 END) as same_area
                FROM users 
                WHERE role='labour' AND category=%s AND available=1 AND verification_status='approved'
                  AND id NOT IN (SELECT labour_id FROM booking_rejections WHERE booking_id=%s)
                  AND id NOT IN (SELECT labour_id FROM bookings WHERE booking_status IN ('Request Sent', 'Confirmed', 'Accepted', 'Inspection Started', 'Estimate Sent', 'Work Approved', 'Work In Progress') AND labour_id IS NOT NULL)
                HAVING distance <= 15
                ORDER BY same_area DESC, average_rating DESC, total_jobs DESC, distance ASC
                LIMIT 1
            """
            cursor.execute(query, (c_lat, c_lng, c_lat, booking['customer_area'], booking['category'], booking_id))
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

# ---------------- WORKFLOW ROUTES ----------------

@app.route("/pay_visiting_charge/<int:booking_id>")
def pay_visiting_charge(booking_id):
    if session.get("role") != "customer": return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM bookings WHERE id=%s AND customer_id=%s", (booking_id, session["user_id"]))
    b = cursor.fetchone()
    if not b:
        cursor.close()
        return redirect(url_for("customer_bookings"))
        
    vc = float(b['visiting_charge'] or 0)
    
    if vc > 0:
        cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
        balance = float(cursor.fetchone()['wallet_balance'] or 0)
        if balance < vc:
            flash(f"Insufficient wallet balance. You need ₹{vc}. Please add money.", "warning")
            return redirect(url_for("wallet_history"))
        
        # Deduct from customer
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance - %s WHERE id=%s", (vc, session["user_id"]))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'debit', %s, %s)", 
                       (session["user_id"], vc, f"Visiting charge for Booking #{booking_id}"))
        
        # Calculate breakdown for VC
        plat_vc = vc * 0.15
        lab_vc = vc * 0.85
        
        # Update booking earnings
        cursor.execute("""
            UPDATE bookings 
            SET visiting_charge_paid=1, platform_commission = platform_commission + %s, labour_earnings = labour_earnings + %s
            WHERE id=%s
        """, (plat_vc, lab_vc, booking_id))
        
        # Credit labour wallet
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance + %s WHERE id=%s", (lab_vc, b['labour_id']))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'credit', %s, %s)", 
                       (b['labour_id'], lab_vc, f"Visiting earnings for Booking #{booking_id}"))

    cursor.execute("UPDATE bookings SET booking_status='Inspection Started', visiting_charge_paid=1 WHERE id=%s AND customer_id=%s AND booking_status='Accepted'", (booking_id, session["user_id"]))
    db.commit()
    cursor.close()
    return redirect(url_for("customer_bookings"))

@app.route("/submit_estimate/<int:booking_id>", methods=["POST"])
def submit_estimate(booking_id):
    if session.get("role") != "labour": return redirect(url_for("login"))
    est = request.form.get("estimate_amount")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE bookings SET booking_status='Estimate Sent', estimate_amount=%s WHERE id=%s AND labour_id=%s AND booking_status='Inspection Started'", (est, booking_id, session["user_id"]))
    db.commit()
    cursor.close()
    return redirect(url_for("labour_dashboard"))

@app.route("/approve_estimate/<int:booking_id>/<action>")
def approve_estimate(booking_id, action):
    if session.get("role") != "customer": return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    if action == 'accept':
        cursor.execute("UPDATE bookings SET booking_status='Work Approved' WHERE id=%s AND customer_id=%s AND booking_status='Estimate Sent'", (booking_id, session["user_id"]))
    else:
        cursor.execute("UPDATE bookings SET booking_status='Rejected by Customer' WHERE id=%s AND customer_id=%s AND booking_status='Estimate Sent'", (booking_id, session["user_id"]))
        cursor.execute("UPDATE users SET available=1 WHERE id=(SELECT labour_id FROM bookings WHERE id=%s)", (booking_id,))
    db.commit()
    cursor.close()
    return redirect(url_for("customer_bookings"))

@app.route("/begin_work/<int:booking_id>")
def begin_work(booking_id):
    if session.get("role") != "labour": return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE bookings SET booking_status='Work In Progress' WHERE id=%s AND labour_id=%s AND booking_status='Work Approved'", (booking_id, session["user_id"]))
    db.commit()
    cursor.close()
    return redirect(url_for("labour_dashboard"))

@app.route("/checkout/<int:booking_id>")
def checkout(booking_id):
    if session.get("role") != "customer": return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=%s AND customer_id=%s", (booking_id, session["user_id"]))
    b = cursor.fetchone()
    
    if not b or b['booking_status'] != 'Work In Progress':
        return redirect(url_for("customer_bookings"))
    
    vc = float(b['visiting_charge'] or 0)
    wc = float(b['estimate_amount'] or 0)
    total = vc + wc
    
    plat_fee = total * 0.15
    labour_earnings = total * 0.85
    
    # Check if customer has enough balance for WC (assuming VC was already paid)
    cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
    wallet_balance = float(cursor.fetchone()['wallet_balance'] or 0)
    
    cursor.close()
    return render_template("payment.html", booking=b, vc=vc, wc=wc, total=total, plat_fee=plat_fee, labour_earnings=labour_earnings, wallet_balance=wallet_balance)

@app.route("/pay_final_work/<int:booking_id>")
def pay_final_work(booking_id):
    if session.get("role") != "customer": return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id=%s AND customer_id=%s", (booking_id, session["user_id"]))
    b = cursor.fetchone()
    
    if b and b['booking_status'] == 'Work In Progress':
        wc = float(b['estimate_amount'] or 0)
        
        # Check wallet balance
        cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
        balance = float(cursor.fetchone()['wallet_balance'] or 0)
        
        if balance < wc:
            flash(f"Insufficient wallet balance. You need ₹{wc}. Please add money.", "warning")
            return redirect(url_for("wallet_history"))

        # Deduct from customer
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance - %s WHERE id=%s", (wc, session["user_id"]))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'debit', %s, %s)", 
                       (session["user_id"], wc, f"Final payment for Booking #{booking_id}"))

        # Calculate breakdown
        plat_wc = wc * 0.15
        lab_wc = wc * 0.85
        
        cursor.execute("""
            UPDATE bookings 
            SET booking_status='Completed', work_cost_paid=1, final_work_cost=%s, 
                platform_commission = platform_commission + %s, labour_earnings = labour_earnings + %s 
            WHERE id=%s
        """, (wc, plat_wc, lab_wc, booking_id))
        
        # Credit to labour
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance + %s, available=1, total_jobs = total_jobs + 1 WHERE id=%s", (lab_wc, b['labour_id']))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'credit', %s, %s)", 
                       (b['labour_id'], lab_wc, f"Work earnings for Booking #{booking_id}"))

        db.commit()
        cursor.close()
        return render_template("payment_success.html", amount=wc, booking_id=booking_id)
        
    cursor.close()
    return redirect(url_for("customer_bookings"))

# ---------------- WALLET SYSTEM ----------------
@app.route("/wallet")
def wallet_history():
    if not session.get("user_id"): return redirect(url_for("login"))
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT wallet_balance FROM users WHERE id=%s", (session["user_id"],))
    balance = float(cursor.fetchone()['wallet_balance'] or 0)
    
    cursor.execute("SELECT * FROM transactions WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
    transactions = cursor.fetchall()
    for t in transactions:
        t['amount'] = float(t['amount'])
    
    cursor.close()
    return render_template("wallet.html", balance=balance, transactions=transactions, config_key=RAZORPAY_KEY_ID)

@app.route("/wallet/add", methods=["POST"])
def add_money():
    if not session.get("user_id"): return redirect(url_for("login"))
    try:
        amount = float(request.form.get("amount", 0))
        if amount <= 0:
            flash("Invalid amount. Please enter a positive value.", "danger")
            return redirect(url_for("wallet_history"))
        
        # In a real app, you'd create a Razorpay order here
        # For now, we'll keep the direct add but structure it for Razorpay transition
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance + %s WHERE id=%s", (amount, session["user_id"]))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'credit', %s, 'Added to wallet (Razorpay Simulated)')", (session["user_id"], amount))
        db.commit()
        cursor.close()
        flash(f"₹{amount} successfully added to your wallet!", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        
    return redirect(url_for("wallet_history"))

@app.route("/api/razorpay/create_order", methods=["POST"])
def create_razorpay_order():
    if not session.get("user_id"): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    amount = int(float(data.get('amount')) * 100) # Amount in paise
    
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    }
    try:
        order = client.order.create(data=order_data)
        return jsonify(order)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/razorpay/verify", methods=["POST"])
def verify_payment():
    if not session.get("user_id"): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    
    try:
        # Verify signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        
        # Payment is successful, update wallet
        amount = float(data['amount'])
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance + %s WHERE id=%s", (amount, session["user_id"]))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (%s, 'credit', %s, 'Added via Razorpay')", (session["user_id"], amount))
        db.commit()
        cursor.close()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "failure", "error": str(e)}), 400

# ---------------- CUSTOMER BOOKINGS ----------------
@app.route("/customer/bookings")
def customer_bookings():
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.*, IFNULL(u.name, 'Searching...') as name, IFNULL(u.city, 'N/A') as city,
               'Support: +91 XXXXX XXXXX' as caller_info,
               (SELECT rating FROM reviews r WHERE r.booking_id = b.id LIMIT 1) as rating
        FROM bookings b
        LEFT JOIN users u ON b.labour_id = u.id
        WHERE b.customer_id=%s
        ORDER BY b.id DESC
    """, (session["user_id"],))

    bookings = cursor.fetchall()
    for b in bookings:
        b['visiting_charge'] = float(b['visiting_charge'] or 0)
        b['amount'] = float(b['amount'] or 0)
        b['estimate_amount'] = float(b['estimate_amount'] or 0)
        b['applied_rate'] = float(b['applied_rate'] or 0)
        b['final_work_cost'] = float(b['final_work_cost'] or 0)
        b['platform_commission'] = float(b['platform_commission'] or 0)
        b['labour_earnings'] = float(b['labour_earnings'] or 0)
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
    
    # Sync timeouts
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
        SELECT b.*, 
               CASE WHEN b.booking_status IN ('Accepted', 'Inspection Started', 'Estimate Sent', 'Work Approved', 'Work In Progress', 'Completed') THEN u.name ELSE 'Customer' END as name,
               'Support: +91 XXXXX XXXXX' as caller_info
        FROM bookings b
        JOIN users u ON b.customer_id = u.id
        WHERE b.labour_id=%s AND b.booking_status NOT IN ('Pending Payment', 'Searching for Labour')
        ORDER BY b.id DESC
    """, (session["user_id"],))

    requests = cursor.fetchall()
    
    cursor.execute("""
        SELECT category, average_rating, total_jobs, visiting_charge, wallet_balance, total_reviews
        FROM users WHERE id=%s
    """, (session["user_id"],))
    labour_profile = cursor.fetchone()
    if labour_profile:
        labour_profile['visiting_charge'] = float(labour_profile['visiting_charge'] or 0)
        labour_profile['wallet_balance'] = float(labour_profile['wallet_balance'] or 0)

    # Earnings stats
    cursor.execute("SELECT SUM(labour_earnings) as total FROM bookings WHERE labour_id=%s AND booking_status='Completed'", (session["user_id"],))
    total_earnings = float(cursor.fetchone()['total'] or 0)
    
    cursor.execute("SELECT SUM(labour_earnings) as total FROM bookings WHERE labour_id=%s AND booking_status='Completed' AND DATE(created_at) = CURDATE()", (session["user_id"],))
    today_earnings = float(cursor.fetchone()['total'] or 0)

    cursor.close()

    return render_template("labour_dashboard.html", 
                           requests=requests, 
                           name=session["name"], 
                           profile=labour_profile,
                           total_earnings=total_earnings,
                           today_earnings=today_earnings)

# ---------------- ACCEPT ----------------
@app.route("/accept/<int:booking_id>")
def accept_booking(booking_id):
    if session.get("role") != "labour":
        return redirect(url_for("login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Accepted'
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

    cursor.execute("INSERT INTO booking_rejections (booking_id, labour_id) VALUES (%s, %s)", (booking_id, session['user_id']))
    cursor.execute("""
        UPDATE bookings 
        SET booking_status='Searching for Labour', labour_id=NULL, assigned_at=NULL
        WHERE id=%s AND labour_id=%s
    """, (booking_id, session["user_id"]))

    db.commit()
    cursor.close()

    return redirect(url_for("labour_dashboard"))

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='customer'")
    total_customers = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='labour'")
    total_labours = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM bookings")
    total_bookings = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE booking_status='Completed'")
    completed_jobs = cursor.fetchone()['count']

    cursor.execute("SELECT SUM(platform_commission + amount) as total FROM bookings WHERE booking_status='Completed'")
    total_earnings = float(cursor.fetchone()['total'] or 0)
    
    cursor.execute("""
        SELECT id, name, mobile, category, city, aadhaar_number, id_proof_type, profile_photo, id_proof_image, verification_status, is_blocked 
        FROM users WHERE role='labour' AND verification_status='pending' ORDER BY id DESC
    """)
    labours = cursor.fetchall()
    
    cursor.close()

    return render_template("admin.html",
                           active_tab="dashboard",
                           total_customers=total_customers,
                           total_labours=total_labours,
                           total_bookings=total_bookings,
                           completed_jobs=completed_jobs,
                           total_earnings=total_earnings,
                           labours=labours)

@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin": return redirect(url_for("admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, mobile, role, is_blocked FROM users WHERE role='customer' ORDER BY id DESC")
    customers = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", active_tab="users", customers=customers)

@app.route("/admin/labours")
def admin_labours():
    if session.get("role") != "admin": return redirect(url_for("admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, name, mobile, category, city, aadhaar_number, id_proof_type, profile_photo, id_proof_image, verification_status, is_blocked 
        FROM users WHERE role='labour' ORDER BY CASE WHEN verification_status='pending' THEN 1 ELSE 2 END, id DESC
    """)
    labours = cursor.fetchall()
    for l in labours:
        if 'base_rate' in l: l['base_rate'] = float(l['base_rate'] or 0)
        if 'current_rate' in l: l['current_rate'] = float(l['current_rate'] or 0)
        if 'wallet_balance' in l: l['wallet_balance'] = float(l['wallet_balance'] or 0)
    cursor.close()
    return render_template("admin.html", active_tab="labour", labours=labours)

@app.route("/admin/bookings")
def admin_bookings():
    if session.get("role") != "admin": return redirect(url_for("admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT b.*, u1.name as customer_name, u2.name as labour_name 
        FROM bookings b
        LEFT JOIN users u1 ON b.customer_id = u1.id
        LEFT JOIN users u2 ON b.labour_id = u2.id
        ORDER BY b.id DESC
    """)
    bookings_data = cursor.fetchall()
    for b in bookings_data:
        b['amount'] = float(b['amount'] or 0)
        b['commission'] = float(b['commission'] or 0)
        if 'platform_commission' in b: b['platform_commission'] = float(b['platform_commission'] or 0)
        if 'labour_earnings' in b: b['labour_earnings'] = float(b['labour_earnings'] or 0)
        if 'visiting_charge' in b: b['visiting_charge'] = float(b['visiting_charge'] or 0)
    cursor.close()
    return render_template("admin.html", active_tab="bookings", bookings=bookings_data)

@app.route("/admin/reviews")
def admin_reviews():
    if session.get("role") != "admin": return redirect(url_for("admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT r.*, u1.name as customer_name, u2.name as labour_name FROM reviews r JOIN users u1 ON r.customer_id = u1.id JOIN users u2 ON r.labour_id = u2.id ORDER BY r.created_at DESC")
    reviews_data = cursor.fetchall()
    cursor.close()
    return render_template("admin.html", active_tab="reviews", reviews=reviews_data)

@app.route("/admin/settings")
def admin_settings():
    if session.get("role") != "admin": return redirect(url_for("admin_login"))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM settings")
    settings = cursor.fetchall()
    settings_dict = {s['setting_key']: s['setting_value'] for s in settings}
    cursor.close()
    return render_template("admin.html", active_tab="settings", settings=settings_dict)



# ---------------- ADMIN UPDATE VERIFICATION ----------------
@app.route("/admin/verify/<int:labour_id>/<status>")
def update_verification(labour_id, status):
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    
    if status not in ['approved', 'rejected']:
        return "Invalid status", 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET verification_status=%s WHERE id=%s", (status, labour_id))
    db.commit()
    cursor.close()
    return redirect(request.referrer or url_for("admin_dashboard"))

# ---------------- ADMIN TOGGLE BLOCK ----------------
@app.route("/admin/toggle_block/<int:user_id>")
def toggle_block(user_id):
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_blocked = NOT is_blocked WHERE id=%s", (user_id,))
    db.commit()
    cursor.close()
    return redirect(request.referrer or url_for("admin_users"))

# ---------------- ADMIN SETTINGS ----------------
@app.route("/admin/settings", methods=["POST"])
def update_settings():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))

    vc = request.form.get("visiting_charge")
    cp = request.form.get("commission_percent")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("REPLACE INTO settings (setting_key, setting_value) VALUES ('visiting_charge', %s)", (vc,))
    cursor.execute("REPLACE INTO settings (setting_key, setting_value) VALUES ('commission_percent', %s)", (cp,))
    db.commit()
    cursor.close()
    
    return redirect(url_for("admin_settings"))



# ---------------- ADD REVIEW ----------------
@app.route("/review/<int:booking_id>", methods=["POST"])
def add_review(booking_id):
    if session.get("role") != "customer":
        return redirect(url_for("login"))

    rating = request.form.get("rating")
    comment = request.form.get("comment")

    db = get_db()
    cursor = db.cursor()    # Get labour_id and check if review exists
    cursor.execute("SELECT labour_id FROM bookings WHERE id=%s", (booking_id,))
    booking = cursor.fetchone()

    cursor.execute("SELECT id FROM reviews WHERE booking_id=%s", (booking_id,))
    existing = cursor.fetchone()

    if booking and booking['labour_id'] and not existing:
        cursor.execute("""
            INSERT INTO reviews (booking_id, customer_id, labour_id, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, session["user_id"], booking['labour_id'], rating, comment))
        
        cursor.execute("""
            UPDATE users SET 
                average_rating = (SELECT AVG(rating) FROM reviews WHERE labour_id = %s),
                total_reviews = (SELECT COUNT(*) FROM reviews WHERE labour_id = %s)
            WHERE id = %s
        """, (booking['labour_id'], booking['labour_id'], booking['labour_id']))
        
        db.commit()

    cursor.close()
    return redirect(url_for("customer_bookings"))

# ---------------- API: LABOUR REVIEWS ----------------
@app.route("/api/labour_reviews/<int:labour_id>")
def labour_reviews(labour_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT r.rating, r.comment, u.name as customer_name, DATE_FORMAT(r.created_at, '%Y-%m-%d') as date
        FROM reviews r
        JOIN users u ON r.customer_id = u.id
        WHERE r.labour_id = %s
        ORDER BY r.created_at DESC
        LIMIT 10
    """, (labour_id,))
    reviews = cursor.fetchall()
    return jsonify(reviews)

if __name__ == "__main__":
    app.run(debug=True)
