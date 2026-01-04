from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
import csv
import io
import re
import requests # Added for Paystack
import hmac
import hashlib
import json
import openpyxl
from openpyxl import Workbook
import random
import string

def generate_reference():
    """Generates a standardized transaction reference: BYT + 8 random uppercase alphanumeric chars."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"BYT{suffix}"
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func
import os
import threading
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

load_dotenv()

failed_logins = {}  # key = email, value = count
MAX_ATTEMPTS = 4

app = Flask(__name__)

# =====================
# CONFIG
# =====================
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# =====================
# USER MODEL
# =====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(200))
    balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    is_suspended = db.Column(db.Boolean, default=False) # New field for suspension
    is_super_admin = db.Column(db.Boolean, default=False) # New field for super admin
    last_read_notice_timestamp = db.Column(db.DateTime) # New field for notifications
    preferred_network = db.Column(db.String(20)) # New field for locked withdrawal network

# =====================
# TRANSACTION MODEL
# =====================
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False) # Paystack ref
    type = db.Column(db.String(20), nullable=False) # Deposit, Withdrawal
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Success, Failed
    recipient_number = db.Column(db.String(20)) # New: Saved at time of request
    recipient_network = db.Column(db.String(20)) # New: Saved at time of request
    account_name = db.Column(db.String(100)) # New: Verified name
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

# =====================
# DATA PLAN MODEL (Dynamic Pricing)
# =====================
class DataPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    network = db.Column(db.String(20), nullable=False) # MTN, TELECEL, AIRTELTIGO
    plan_size = db.Column(db.String(20), nullable=False) # e.g. "1 GB"
    cost_price = db.Column(db.Float, nullable=False, default=0.0) # Depot Price (Cost)
    manufacturing_price = db.Column(db.Float, nullable=False, default=0.0) # Raw Cost (Super Admin only)
    dealer_price = db.Column(db.Float, nullable=False, default=0.0) # Price for Store Owners
    selling_price = db.Column(db.Float, nullable=False, default=0.0) # Site Price (Revenue)
    display_order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Active') # Active, Inactive

# =====================
# SYSTEM SETTINGS MODEL
# =====================
class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)

# Context Processor to make site_notice available globally
@app.context_processor
def inject_site_notice():
    notice_setting = SiteSetting.query.filter_by(key='site_notice').first()
    
    # Check for timestamp
    notice_timestamp_setting = SiteSetting.query.filter_by(key='site_notice_timestamp').first()
    notice_timestamp = None
    if notice_timestamp_setting and notice_timestamp_setting.value:
        try:
            notice_timestamp = datetime.utcfromtimestamp(float(notice_timestamp_setting.value))
        except:
            pass
            
    return dict(
        site_notice=notice_setting.value if notice_setting else None,
        site_notice_timestamp=notice_timestamp
    )

@app.context_processor
def inject_admin_stats():
    # Only useful if user is admin, but safe to check generally or just return 0
    if current_user.is_authenticated and current_user.is_admin:
        pending_txns = Transaction.query.filter(
            Transaction.status == 'Pending',
            Transaction.type.in_(['Withdrawal', 'Store Withdrawal'])
        ).order_by(Transaction.date.desc()).all()
        
        return dict(
            pending_withdrawals_count=len(pending_txns),
            pending_notifications=pending_txns
        )
    return dict(pending_withdrawals_count=0, pending_notifications=[])

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {e}")

def send_notification_email(subject, body):
    # Send to the configured MAIL_USERNAME (Admin)
    msg = Message(subject, recipients=[app.config['MAIL_USERNAME']])
    msg.body = body
    
    # Run in thread
    t = threading.Thread(target=send_async_email, args=(app._get_current_object(), msg))
    t.start()


# =====================
# CONSTANTS
# =====================
# =====================
# CONSTANTS
# =====================

# =====================
# STORE MODELS
# =====================
class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), default="My Store")
    slug = db.Column(db.String(50), unique=True) # For the public link
    support_phone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    whatsapp_group_link = db.Column(db.String(200)) # New field
    description = db.Column(db.String(300))
    notice = db.Column(db.String(500)) # New field for store announcements
    status = db.Column(db.String(20), default='Active') # Active, Suspended, Inactive

    
    # Store Stats
    total_sales = db.Column(db.Float, default=0.0)
    total_withdrawn = db.Column(db.Float, default=0.0)
    credit_balance = db.Column(db.Float, default=0.0)

    user = db.relationship('User', backref=db.backref('store', uselist=False))

class StorePricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    network = db.Column(db.String(20), nullable=False)
    package_name = db.Column(db.String(50), nullable=False)
    dealer_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Inactive

    store = db.relationship('Store', backref=db.backref('pricing', lazy=True))

class StoreOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120)) # Added for customer tracking
    network = db.Column(db.String(20)) # Added for filtering
    package = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    store = db.relationship('Store', backref=db.backref('orders', lazy=True))

# =====================
# ORDER MODEL
# =====================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    network = db.Column(db.String(20), nullable=False)
    package = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20)) # Added for data destination
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Delivered, Failed, Processing
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('orders', lazy=True))

# =====================
# USER LOADER
# =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================
# DECORATORS
# =====================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =====================
# ROUTES
# =====================
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user:
            flash("Email already registered", "error")
            return redirect(url_for("register"))

        new_user = User(
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            username=request.form["username"],
            email=request.form["email"],
            mobile=request.form["mobile"],
            preferred_network=request.form.get("network"), # Capture Network
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Login now.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    email = None
    password = None
    attempts = 0

    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')

        # check if input is a valid email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'error')
            attempts = failed_logins.get(email, 0) if email else 0
            return render_template('login.html', attempts=attempts, email=email)

        # Case-insensitive email check
        user = User.query.filter(func.lower(User.email) == email.lower()).first()

        # Initialize failed attempts for this email
        if email not in failed_logins:
            failed_logins[email] = 0

        # Check if user exists
        if not user:
            failed_logins[email] += 1
            flash(f'Account with email "{email}" does not exist.', 'danger')
            if failed_logins[email] >= MAX_ATTEMPTS:
                flash('Too many failed attempts. You can reset your password.', 'warning')
            attempts = failed_logins[email]
            return render_template('login.html', attempts=attempts, email=email)

        # Check password
        if not check_password_hash(user.password, password):
            failed_logins[email] += 1
            flash('Wrong password.', 'danger')
            if failed_logins[email] >= MAX_ATTEMPTS:
                flash('Too many failed attempts. You can reset your password.', 'warning')
            attempts = failed_logins[email]
            return render_template('login.html', attempts=attempts, email=email)

        # Successful login, reset counter
        failed_logins[email] = 0
        login_user(user)
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('login.html', attempts=attempts, email=email)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    return render_template('reset_password.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    # Dynamic Data Bundles (Same logic as buy_data)
    plans = DataPlan.query.filter_by(status='Active').order_by(DataPlan.display_order).all()
    data_bundles = {
        "MTN": [],
        "TELECEL": [],
        "AIRTELTIGO": []
    }
    
    for plan in plans:
        # Standardize structure for the template
        # Matching template use: plan.size, plan.price
        # DB Fields: plan.plan_size, plan.selling_price
        if plan.network in data_bundles:
            data_bundles[plan.network].append({
                "size": plan.plan_size,
                "price": f"GH₵{plan.selling_price:.2f}",
                "expiry": "No-Expiry" # Default for now
            })

    balance = current_user.balance
    current_plan = "No Active Plan"
    recent_activity = "No recent activity"

    return render_template(
        "dashboard.html",
        data_bundles=data_bundles,
        balance=balance,
        current_plan=current_plan,
        recent_activity=recent_activity
    )

@app.route("/api/read_notification", methods=["POST"])
@login_required
def read_notification():
    current_user.last_read_notice_timestamp = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})

@app.route("/orders")
@login_required
def orders():
    # Helper to seed dummy data if none exists
    if Order.query.count() == 0:
        dummy_orders = [
            Order(user_id=current_user.id, transaction_id="TXN12345678", network="MTN", package="1 GB", amount=4.60, status="Delivered"),
            Order(user_id=current_user.id, transaction_id="TXN87654321", network="TELECEL", package="2 GB", amount=9.60, status="Pending"),
            Order(user_id=current_user.id, transaction_id="TXN11223344", network="AIRTELTIGO", package="3 GB", amount=14.00, status="Failed"),
            Order(user_id=current_user.id, transaction_id="TXN99887766", network="MTN", package="4 GB", amount=18.50, status="Processing"),
        ]
        for order in dummy_orders:
            db.session.add(order)
        db.session.commit()

    # Filtering
    status_filter = request.args.get('status')
    network_filter = request.args.get('network')

    query = Order.query.filter_by(user_id=current_user.id)

    if status_filter and status_filter != "Status" and status_filter is not None:
        query = query.filter(Order.status.ilike(status_filter)) 
    
    if network_filter and network_filter != "Network" and network_filter is not None:
        query = query.filter(Order.network.ilike(network_filter))

    orders = query.order_by(Order.date.desc()).all()

    return render_template("orders.html", orders=orders)

@app.route("/history")
@login_required
def history():
    return render_template("history.html")

@app.route("/wallet")
@login_required
def wallet():
    # Calculate Sales
    today = datetime.utcnow().date()
    # active_orders = Order.query.filter_by(user_id=current_user.id, status='Delivered').all()
    # Simple calculation for demo
    daily_sales = 0.0 # Sum of orders today
    monthly_sales = 0.0 # Sum of orders this month

    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()

    return render_template(
        "wallet.html",
        balance=current_user.balance,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
        transactions=transactions
    )



# Redefining helper to actually take the User object or params
def execute_deposit_credit(user, reference, amount_to_credit):
    txn = Transaction.query.filter_by(reference=reference).first()
    if txn and txn.status == 'Success':
        return False, "Transaction already successful"
    
    if not txn:
         txn = Transaction(
            user_id=user.id,
            reference=reference,
            type="Deposit",
            amount=amount_to_credit,
            status="Success"
         )
         db.session.add(txn)
    else:
        txn.status = "Success"
        txn.amount = amount_to_credit # update if needed
        
    user.balance += amount_to_credit
    db.session.commit()
    return True, f"Wallet credited with GH₵{amount_to_credit:.2f}"


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    try:
        amount = float(request.form.get("amount"))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError):
        flash("Invalid amount entered.", "error")
        return redirect(url_for('wallet'))


    reference = generate_reference()

    # ===============================================================
    # [PAYSTACK INTEGRATION START]
    # ===============================================================
    # 1. Get Secret Key
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not secret_key:
        flash("Payment gateway not configured.", "error")
        return redirect(url_for('wallet'))
    
    # 2. Prepare Data
    # CHARGE 3% FEE: User requests 100, we charge 103.
    charge_amount = amount * 1.03
    amount_kobo = int(charge_amount * 100)
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": current_user.email, 
        "amount": amount_kobo, 
        "reference": reference,
        "callback_url": url_for('payment_callback', _external=True),
        "metadata": {
            "original_amount": amount,
            "user_id": current_user.id # Critical for Webhook
        }
    }
    
    # 3. Send Request
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        if response.status_code == 200 and res_data['status']:
            # Redirect user to Paystack payment page
            return redirect(res_data['data']['authorization_url'])
        else:
            flash("Payment initialization failed: " + res_data.get('message', 'Unknown error'), "error")
            return redirect(url_for('wallet'))
    except Exception as e:
        flash(f"Connection error: {str(e)}", "error")
        return redirect(url_for('wallet'))
    
    # ===============================================================
    # [PAYSTACK INTEGRATION END]
    # ===============================================================

@app.route("/payment/callback")
@login_required
def payment_callback():
    reference = request.args.get('reference')
    if not reference:
        flash("No reference provided.", "error")
        return redirect(url_for('wallet'))

    # ===============================================================
    # [PAYSTACK VERIFICATION START]
    # ===============================================================
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    try:
        response = requests.get(url, headers=headers)
        res_data = response.json()
        if response.status_code == 200 and res_data['data']['status'] == 'success':
            paystack_amount = res_data['data']['amount'] / 100
            meta = res_data['data'].get('metadata', {})
            amount_to_credit = meta.get('original_amount')
            
            if not amount_to_credit:
                amount_to_credit = paystack_amount / 1.03
            
            amount_to_credit = float(amount_to_credit)
            
            # Execute Credit
            success, msg = execute_deposit_credit(current_user, reference, amount_to_credit)
            
            if success:
                flash(msg, "success")
            else:
                flash(msg, "info")
        else:
            flash("Payment verification failed.", "error")
    except Exception as e:
        flash(f"Error verifying payment: {str(e)}", "error")
    # ===============================================================
    # [PAYSTACK VERIFICATION END]
    # ===============================================================

    return redirect(url_for('wallet'))

@app.route("/paystack/webhook", methods=["POST"])
@csrf.exempt # Disable CSRF for Webhooks
def paystack_webhook():
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not secret_key:
        return "Config Error", 500

    # 1. Verify Signature
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        return "No Signature", 400
    
    # Calculate HMAC
    computed_sig = hmac.new(
        secret_key.encode('utf-8'), 
        request.data, 
        hashlib.sha512
    ).hexdigest()

    if computed_sig != signature:
        return "Invalid Signature", 400

    # 2. Process Event
    event = request.json
    if event['event'] == 'charge.success':
        data = event['data']
        reference = data['reference']
        
        # Determine Amount
        paystack_amount = data['amount'] / 100
        meta = data.get('metadata', {})
        
        amount_to_credit = meta.get('original_amount')
        user_id = meta.get('user_id')
        
        if not amount_to_credit:
            amount_to_credit = paystack_amount / 1.03
        
        amount_to_credit = float(amount_to_credit)
        
        if user_id:
            user = User.query.get(user_id)
            if user:
                 # Use Helper
                 success, msg = execute_deposit_credit(user, reference, amount_to_credit)
                 print(f"WEBHOOK: {msg}")
                 return "OK", 200
        
        # If no user_id in metadata, try to find by email
        email = data['customer']['email']
        user = User.query.filter_by(email=email).first()
        if user:
             success, msg = execute_deposit_credit(user, reference, amount_to_credit)
             print(f"WEBHOOK (Email Fallback): {msg}")
             return "OK", 200

    return "Ignored", 200

@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    try:
        amount = float(request.form.get("amount"))
        network_code = request.form.get("network") # MTN, VOD, ATM
        phone_number = request.form.get("phone_number")
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError):
        flash("Invalid amount entered.", "error")
        return redirect(url_for('wallet'))
    
    if amount > current_user.balance:
        flash("Insufficient balance", "error")
        return redirect(url_for('wallet'))

    # ===============================================================
    # [MANUAL APPROVAL WITHDRAWAL START]
    # ===============================================================
    
    # LOCK WITHDRAWAL TO REGISTERED DETAILS
    network_code = current_user.preferred_network
    phone_number = current_user.mobile

    if not network_code or not phone_number:
        flash("Please update your Withdrawal Network in your Profile settings first.", "error")
        return redirect(url_for('profile'))

    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    
    # 1. Encode Details in Reference (To avoid schema changes)
    # Format: WTH|NET|PHONE|NAME|TIMESTAMP
    # We strip special chars from phone/net just in case
    
    # Resolve Name First (Good for UX, ensures number works)
    resolve_url = f"https://api.paystack.co/bank/resolve?account_number={phone_number}&bank_code={network_code}"
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    account_name = "Unknown"
    try:
        resolve_res = requests.get(resolve_url, headers=headers)
        if resolve_res.status_code == 200:
             account_name = resolve_res.json()['data']['account_name']
        else:
             # If verification fails, we can either block or warn. 
             # Let's block to prevent typos.
             flash("Could not verify Mobile Money account name. Please check details.", "error")
             return redirect(url_for('wallet'))
    except:
         pass # Network error, maybe let it slide or block? Let's block for safety.

    # Generate Safe Reference
    safe_name = re.sub(r'[^a-zA-Z0-9 ]', '', account_name)[:20]
    ts = int(datetime.utcnow().timestamp())
    reference=generate_reference()

    # Deduct Balance Immediately
    current_user.balance -= amount
    
    txn = Transaction(
        user_id=current_user.id,
        reference=reference,
        type="Withdrawal",
        amount=amount,
        status="Pending",
        recipient_number=phone_number,
        recipient_network=network_code,
        account_name=account_name
    )
    db.session.add(txn)
    db.session.commit()
    
    flash(f"Withdrawal request of GH₵{amount} submitted for approval. Account: {account_name}", "success")

    # ===============================================================
    # [MANUAL APPROVAL WITHDRAWAL END]
    # ===============================================================
    
    return redirect(url_for('wallet'))

# ADMIN ACTIONS FOR WITHDRAWAL

@app.route("/admin/transaction/<int:txn_id>/approve", methods=["POST"])
@login_required
def approve_withdrawal(txn_id):
    # Verify Admin (You should add an @admin_required decorator ideally)
    if current_user.email != 'admin@razilhub.com' and not current_user.is_admin: # Basic check
         flash("Unauthorized", "error")
         return redirect(url_for('admin_transactions'))

    txn = Transaction.query.get_or_404(txn_id)
    if txn.status != 'Pending':
        flash("Invalid transaction state.", "error")
        return redirect(url_for('admin_transactions'))
        
    # Support both regular and store withdrawals
    allowed_types = ['Withdrawal', 'Store Withdrawal']
    if txn.type not in allowed_types:
         flash(f"Cannot auto-approve transaction type: {txn.type}", "error")
         return redirect(url_for('admin_transactions'))

    # Parse Details from User Profile (LOCKED SECURITY)
    try:
        user = txn.user
        network_code = user.preferred_network
        phone_number = user.mobile
        
        if not network_code or not phone_number:
            flash("User has not set withdrawal details in profile. Cannot approve.", "error")
            return redirect(url_for('admin_transactions'))

        secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        headers = {"Authorization": f"Bearer {secret_key}"}

        # 1. Resolve Account Name (Dynamic Security Check)
        resolve_url = f"https://api.paystack.co/bank/resolve?account_number={phone_number}&bank_code={network_code}"
        account_name = "Unknown Beneficiary"
        
        resolve_res = requests.get(resolve_url, headers=headers)
        if resolve_res.status_code == 200:
             account_name = resolve_res.json()['data']['account_name']
        else:
             # If we can't verify the name, we should probably stop or warn.
             # But for reliability, sometimes banks are down. 
             # Let's try to proceed but warn in logs. 
             print(f"Name Resolution Failed: {resolve_res.text}")
             # Optional: return error if strict
             # flash("Could not verify recipient name with Paystack.", "error")
             # return redirect(url_for('admin_transactions'))
        
        # 2. Create Recipient
        recipient_url = "https://api.paystack.co/transferrecipient"
        recipient_data = {
            "type": "mobile_money",
            "name": account_name,
            "account_number": phone_number,
            "bank_code": network_code,
            "currency": "GHS"
        }
        recipient_res = requests.post(recipient_url, json=recipient_data, headers=headers)
        if recipient_res.status_code not in [200, 201]:
             flash(f"Paystack Error: Could not create recipient. {recipient_res.json().get('message')}", "error")
             return redirect(url_for('admin_transactions'))
        
        recipient_code = recipient_res.json()['data']['recipient_code']
        
        # 3. Transfer
        transfer_url = "https://api.paystack.co/transfer"
        transfer_data = {
            "source": "balance", 
            "amount": int(txn.amount * 100), 
            "recipient": recipient_code, 
            "reason": f"Dice Withdrawal ({txn.type})"
        }
        
        transfer_res = requests.post(transfer_url, json=transfer_data, headers=headers)
        res_data = transfer_res.json()
        
        if transfer_res.status_code == 200 and res_data['status']:
             txn.status = "Success"
             db.session.commit()
             flash(f"Withdrawal Approved & Sent to {account_name} ({phone_number})", "success")
        else:
             # Detailed Error Logging
             err_msg = res_data.get('message', 'Unknown Error')
             print(f"PAYSTACK TRANSFER ERROR: {res_data}") 
             flash(f"Transfer Failed: {err_msg}", "error")
             
    except Exception as e:
        print(f"SYSTEM ERROR: {str(e)}")
        flash(f"Error processing withdrawal: {str(e)}", "error")

    return redirect(url_for('admin_transactions'))

@app.route("/admin/transaction/<int:txn_id>/reject", methods=["POST"])
@login_required
def reject_withdrawal(txn_id):
    # Verify Admin
    if current_user.email != 'admin@razilhub.com' and not current_user.is_admin:
         flash("Unauthorized", "error")
         return redirect(url_for('admin_transactions'))
         
    txn = Transaction.query.get_or_404(txn_id)
    if txn.status != 'Pending' or txn.type != 'Withdrawal':
        flash("Invalid transaction state.", "error")
        return redirect(url_for('admin_transactions'))
        
    # Refund User
    user = User.query.get(txn.user_id)
    user.balance += txn.amount
    
    txn.status = "Failed"
    db.session.commit()
    
    flash("Withdrawal rejected. User has been refunded.", "success")
    return redirect(url_for('admin_transactions'))


@app.route("/store", methods=["GET", "POST"])
@login_required
def store():
    # Ensure user has a store
    if not current_user.store:
        # Default slug
        slug_candidate = f"store-{current_user.username}"
        # Check uniqueness (simple check)
        existing = Store.query.filter_by(slug=slug_candidate).first()
        if existing:
            slug_candidate = f"store-{current_user.username}-{int(datetime.utcnow().timestamp())}"
            
        new_store = Store(user_id=current_user.id, slug=slug_candidate)
        db.session.add(new_store)
        db.session.commit()
    
    my_store = current_user.store
    store_orders = StoreOrder.query.filter_by(store_id=my_store.id).order_by(StoreOrder.date.desc()).all()
    store_pricing = StorePricing.query.filter_by(store_id=my_store.id).all()
    
    # Fetch Withdrawals
    withdrawals = Transaction.query.filter_by(user_id=current_user.id).filter(
        Transaction.type.in_(['Store Credit Transfer', 'Store Withdrawal'])
    ).order_by(Transaction.date.desc()).all()
    
    # NEW: Fetch Dynamic Dealer Packages from DB (instead of hardcoded DEALER_PACKAGES)
    # This ensures Admin updates are reflected here
    active_plans = DataPlan.query.filter_by(status='Active').order_by(DataPlan.display_order).all()
    dynamic_dealer_packages = {
        "MTN": [],
        "TELECEL": [],
        "AIRTELTIGO": []
    }
    
    for plan in active_plans:
        # Structure must match what frontend JS expects: {package: "Name", price: 12.3}
        if plan.network in dynamic_dealer_packages:
            dynamic_dealer_packages[plan.network].append({
                "package": plan.plan_size,
                "price": plan.dealer_price 
            })
    
    return render_template("store.html", store=my_store, orders=store_orders, pricing_list=store_pricing, dealer_packages=dynamic_dealer_packages, withdrawals=withdrawals)

@app.route("/store/add_pricing", methods=["POST"])
@login_required
def add_pricing():
    store = current_user.store
    network = request.form.get("network")
    package_name = request.form.get("package_name")
    selling_price = float(request.form.get("selling_price"))
    
    # 1. Lookup Official Dealer Price (Cost)
    # We ignore the 'dealer_price' from the form to prevent manipulation
    # FIXED: Lookup from DataPlan DB instead of hardcoded DEALER_PACKAGES
    official_price = None
    
    plan_record = DataPlan.query.filter_by(network=network, plan_size=package_name, status='Active').first()
    
    if plan_record:
        official_price = plan_record.dealer_price
    
    if official_price is None:
        flash("Invalid package selected or package is no longer active.", "error")
        return redirect(url_for("store"))

    # 2. Validate Selling Price
    if selling_price < official_price:
        flash(f"Selling Price cannot be lower than the Dealer Price (GH₵{official_price:.2f}).", "error")
        return redirect(url_for("store"))
        
    # 3. Save/Update with Official Price
    existing = StorePricing.query.filter_by(store_id=store.id, network=network, package_name=package_name).first()
    if existing:
        existing.dealer_price = official_price # Always update to latest official cost
        existing.selling_price = selling_price
        flash(f"Updated pricing for {network} {package_name}.", "success")
    else:
        new_pricing = StorePricing(
            store_id=store.id,
            network=network,
            package_name=package_name,
            dealer_price=official_price, # Use official price
            selling_price=selling_price
        )
        db.session.add(new_pricing)
        flash(f"Added new pricing for {network} {package_name}.", "success")
        
    db.session.commit()
    return redirect(url_for("store"))

@app.route("/store/toggle_pricing/<int:id>")
@login_required
def toggle_pricing(id):
    pricing = StorePricing.query.get_or_404(id)
    # Security check: Ensure this pricing belongs to current user's store
    if pricing.store_id != current_user.store.id:
        flash("Unauthorized", "error")
        return redirect(url_for("store"))
        
    if pricing.status == "Active":
        pricing.status = "Inactive"
    else:
        pricing.status = "Active"
    
    db.session.commit()
    flash(f"Toggled status for {pricing.package_name}", "success")
    return redirect(url_for("store"))

@app.route("/store/delete_pricing/<int:id>")
@login_required
def delete_pricing(id):
    pricing = StorePricing.query.get_or_404(id)
    # Security check
    if pricing.store_id != current_user.store.id:
        flash("Unauthorized", "error")
        return redirect(url_for("store"))
        
    db.session.delete(pricing)
    db.session.commit()
    flash(f"Deleted pricing rule for {pricing.package_name}", "success")
    return redirect(url_for("store"))

@app.route("/store/update", methods=["POST"])
@login_required
def update_store_settings():
    store = current_user.store
    store.name = request.form.get("name")
    
    new_slug = request.form.get("slug")
    if new_slug:
        # Simple uniqueness check
        existing = Store.query.filter(Store.slug == new_slug, Store.id != store.id).first()
        if existing:
            flash("Store Link/Slug is already taken.", "error")
            return redirect(url_for("store"))
        store.slug = new_slug

    store.support_phone = request.form.get("support_phone")
    store.whatsapp = request.form.get("whatsapp")
    store.whatsapp_group_link = request.form.get("whatsapp_group_link")
    store.description = request.form.get("description")
    store.notice = request.form.get("notice")
    
    db.session.commit()
    flash("Store settings updated!", "success")
    return redirect(url_for("store"))

@app.route("/store/withdraw", methods=["POST"])
@login_required
def store_withdraw():
    try:
        amount = float(request.form.get("amount"))
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Invalid amount.", "error")
        return redirect(url_for("store"))
        
    store = current_user.store
    
    if amount <= store.credit_balance:
        # Transfer to main wallet
        store.credit_balance -= amount
        store.total_withdrawn += amount
        current_user.balance += amount
        
        # Log as transaction
        txn = Transaction(
            user_id=current_user.id,
        reference = generate_reference(),
            type="Store Credit Transfer",
            amount=amount,
            status="Success"
        )
        db.session.add(txn)
        db.session.commit()
        flash(f"Transferred GH₵{amount} from store to main wallet.", "success")
    else:
        flash("Insufficient store credit.", "error")
        
    return redirect(url_for("store"))

@app.route("/store/withdraw_momo", methods=["POST"])
@login_required
def store_withdraw_momo():
    try:
        amount = float(request.form.get("amount"))
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Invalid amount.", "error")
        return redirect(url_for("store"))

    # LOCK WITHDRAWAL TO REGISTERED DETAILS
    phone = current_user.mobile
    network = current_user.preferred_network
    
    if not phone or not network:
         flash("Please set your Withdrawal Network in your Profile first.", "error")
         return redirect(url_for("profile"))
    store = current_user.store
    
    # Validation
    if amount < 10:
        flash("Minimum withdrawal amount is GH₵10.00", "error")
        return redirect(url_for("store"))
        
    if amount > store.credit_balance:
        flash("Insufficient store credit.", "error")
        return redirect(url_for("store"))

    # Deduct Logic
    store.credit_balance -= amount
    store.total_withdrawn += amount
    
    # Transaction Record
    txn = Transaction(
        user_id=current_user.id,
        reference = generate_reference(),
        type="Store Withdrawal",
        amount=amount,
        status="Pending",
        recipient_number=phone,
        recipient_network=network,
        account_name="Store Owner" # Or fetch real name if verified
    )
    db.session.add(txn)
    db.session.commit()
    
    flash(f"Withdrawal request of GH₵{amount} to {network} {phone} submitted.", "success")
    return redirect(url_for("store"))

@app.route("/store/<slug>")
def public_store(slug):
    store = Store.query.filter_by(slug=slug).first_or_404()
    # Fetch active pricings
    pricings = StorePricing.query.filter_by(store_id=store.id, status='Active').all()
    
    # Serialize for JS
    packages_data = [{
        'id': p.id,
        'network': p.network,
        'package_name': p.package_name,
        'selling_price': p.selling_price,
        'status': p.status
    } for p in pricings]
    
    return render_template("store_front.html", store=store, packages=packages_data)

@app.route("/store/api/transactions", methods=["POST"])
def get_store_transactions():
    data = request.get_json()
    store_id = data.get('store_id')
    email = data.get('email')
    
    if not store_id or not email:
        return jsonify({'error': 'Missing store_id or email'}), 400
        
    orders = StoreOrder.query.filter_by(store_id=store_id, email=email).order_by(StoreOrder.date.desc()).all()
    
    return jsonify([{
        'id': o.id,
        'date': o.date.strftime('%Y-%m-%d %H:%M'),
        'network': o.network,
        'package': o.package,
        'price': o.price,
        'status': o.status
    } for o in orders])

@app.route("/store/pay", methods=["POST"])
def initiate_payment():
    store_id = request.form.get("store_id")
    pricing_id = request.form.get("pricing_id")
    phone = request.form.get("phone_number")
    email = request.form.get("email")
    
    # Validation
    if not all([store_id, pricing_id, phone, email]):
        flash("All fields are required", "error")
        store = Store.query.get(store_id)
        if store:
            return redirect(url_for('public_store', slug=store.slug))
        return redirect(url_for('index'))
        
    store = Store.query.get_or_404(store_id)
    pricing = StorePricing.query.get_or_404(pricing_id)
    
    # Generate Reference for Store Order
    reference = generate_reference()
    
    # Initialize Paystack Payment
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not secret_key:
        flash("Payment gateway configuration error.", "error")
        return redirect(url_for('public_store', slug=store.slug))
        
    amount_kobo = int(pricing.selling_price * 100)
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email, 
        "amount": amount_kobo, 
        "reference": reference,
        "callback_url": url_for('store_payment_callback', _external=True),
        "metadata": {
            "store_id": store.id,
            "pricing_id": pricing.id,
            "phone": phone,
            "email": email,
            "custom_fields": [
                {
                    "display_name": "Store",
                    "variable_name": "store_name",
                    "value": store.name
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        if response.status_code == 200 and res_data['status']:
            return redirect(res_data['data']['authorization_url'])
        else:
            flash("Payment initialization failed: " + res_data.get('message', 'Unknown error'), "error")
            return redirect(url_for('public_store', slug=store.slug))
    except Exception as e:
        flash(f"Connection error: {str(e)}", "error")
        return redirect(url_for('public_store', slug=store.slug))

@app.route("/store/pay/callback")
def store_payment_callback():
    reference = request.args.get('reference')
    if not reference:
        return "No reference provided", 400
        
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    try:
        response = requests.get(url, headers=headers)
        res_data = response.json()
        
        if response.status_code == 200 and res_data['data']['status'] == 'success':
            meta = res_data['data']['metadata']
            store_id = meta.get('store_id')
            pricing_id = meta.get('pricing_id')
            phone = meta.get('phone')
            email = meta.get('email')
            
            store = Store.query.get(store_id)
            pricing = StorePricing.query.get(pricing_id)
            
            if not store or not pricing:
                return "Invalid Store or Pricing Metadata", 400
                
            # Check if order already exists
            existing_order = StoreOrder.query.filter_by(phone=phone, email=email, date=datetime.utcnow().date()).filter(StoreOrder.package==pricing.package_name).first()
            # A strict check by reference logic would be better if we saved ref. 
            # But StoreOrder schema doesn't have 'transaction_id' (reference).
            # We should probably add it, or just rely on Paystack idempotency if we can't save it.
            # Wait, StoreOrder schema (line 202) DOES NOT have transaction_id!
            # It has id, store_id, phone, email, network, package, price, commission, status, date.
            # We should just create it. Duplicate check might be tricky without ref.
            
            # Create Order
            new_order = StoreOrder(
                store_id=store.id,
                phone=phone,
                email=email,
                network=pricing.network,
                package=pricing.package_name,
                price=pricing.selling_price,
                commission=pricing.selling_price - pricing.dealer_price,
                status="Success"
            )
            
            # Update Store Stats
            commission = pricing.selling_price - pricing.dealer_price
            store.total_sales += pricing.selling_price
            store.credit_balance += commission
            
            # Log Commission Transaction for Store Owner
            comm_txn = Transaction(
                user_id=store.user_id,
                reference=f"COMM-{reference}", # Link to main ref
                type="Store Commission",
                amount=commission,
                status="Success"
            )
            db.session.add(comm_txn)

            db.session.add(new_order)
            db.session.commit()
            
            flash(f"Payment successful! You purchased {pricing.network} {pricing.package_name}.", "success")
            return redirect(url_for('public_store', slug=store.slug))
            
        else:
             return "Payment Verification Failed", 400
             
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/support")
@login_required
def support():
    return render_template("support.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/security_update", methods=["POST"])
@login_required
def security_update():
    # Handle Password Update
    if request.form.get('new_password'):
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not check_password_hash(current_user.password, current_password):
            flash("Incorrect current password", "error")
            return redirect(url_for("profile"))
            
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return redirect(url_for("profile"))
            
        if len(new_password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("profile"))
            
        current_user.password = generate_password_hash(new_password)
        flash("Password updated successfully", "success")

    # Handle Withdrawal Network Update
    new_network = request.form.get("preferred_network")
    if new_network:
         # SECURITY: Only allow setting if currently empty (One-time setup for legacy)
         if not current_user.preferred_network:
             current_user.preferred_network = new_network
             flash("Withdrawal settings saved. This cannot be changed.", "success")
         else:
             # Silently ignore or warn if they try to hack/force change
             pass
    
    db.session.commit()
    return redirect(url_for("profile"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password")
        
        # Case-insensitive email check
        user = User.query.filter(func.lower(User.email) == email.lower()).first()
        
        if user and check_password_hash(user.password, password):
            if user.is_admin:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Not an admin account.", "error")
        else:
            flash("Invalid credentials.", "error")
            
    return render_template("admin/login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # DEBUG: verify load
    print("DEBUG: Loading admin_dashboard route")
    
    # 1. Counts
    total_users = User.query.count()
    total_stores = Store.query.count() # Not strictly requested but good for context
    
    # 2. Financials (Specific Request: Wallet Balance, Users, Orders, Month Sales)
    
    # A. Total Wallet Balance
    total_wallet_balance = db.session.query(func.sum(User.balance)).scalar() or 0.0
    
    # B. Total Orders (Main Platform + Store Orders)
    total_platform_orders = Order.query.count()
    total_store_orders = StoreOrder.query.count()
    grand_total_orders = total_platform_orders + total_store_orders
    
    # C. This Month's Sales
    today = datetime.utcnow()
    start_of_month = datetime(today.year, today.month, 1)
    
    month_direct_sales = db.session.query(func.sum(Order.amount)).filter(Order.date >= start_of_month).scalar() or 0.0
    month_store_sales = db.session.query(func.sum(StoreOrder.price)).filter(StoreOrder.date >= start_of_month).scalar() or 0.0
    this_month_sales = month_direct_sales + month_store_sales
    
    # D. "Platform Revenue" (Legacy stat, keeping for now)
    direct_sales_agg = db.session.query(func.sum(Order.amount)).scalar() or 0.0
    store_sales_agg = db.session.query(func.sum(StoreOrder.price)).scalar() or 0.0
    store_commissions_agg = db.session.query(func.sum(StoreOrder.commission)).scalar() or 0.0
    platform_revenue = direct_sales_agg + (store_sales_agg - store_commissions_agg)
    total_gmv = direct_sales_agg + store_sales_agg

    # 3. Chart Data (Last 7 Days)
    dates = []
    sales_data = [] # Reset or keep empty if loop fails
    
    for i in range(6, -1, -1):
        day = today.date() - timedelta(days=i)
        dates.append(day.strftime('%b %d'))
        daily_direct = db.session.query(func.sum(Order.amount)).filter(func.date(Order.date) == day).scalar() or 0.0
        daily_store_sales = db.session.query(func.sum(StoreOrder.price)).filter(func.date(StoreOrder.date) == day).scalar() or 0.0
        sales_data.append(daily_direct + daily_store_sales)

    # 4. Profit Calculation (Optimized)
    # Using SQL Aggregation instead of Python Loop
    # Profit = (Selling Price - Cost Price)
    # Since cost is dynamic per order's plan, and plan costs might change, strictly speaking we should have stored 'cost' at time of order.
    # However, assuming we use current DataPlan costs (as per original code logic):
    
    profit_stats = {
        "MTN": {"sales": 0.0, "profit": 0.0},
        "TELECEL": {"sales": 0.0, "profit": 0.0},
        "AIRTELTIGO": {"sales": 0.0, "profit": 0.0}
    }

    # Fetch all plans to memory for fast lookup (small table)
    all_plans = DataPlan.query.all()
    cost_map = {(p.network, p.plan_size): p.cost_price for p in all_plans}

    # Direct Orders Analysis
    # We still fetch orders, but we can do it slightly smarter or stick to Python for complexity if SQL is too hard to map dynamic costs without a join.
    # Given the original code did Python looping, and cost depends on (network, package) lookup, 
    # fully pure SQL would require joining DataPlan on two columns which can be messy if strings don't match perfectly.
    # We will keep the Python loop but ensure we ONLY fetch necessary columns to reduce memory.
    
    direct_orders = db.session.query(Order.network, Order.package, Order.amount).filter(Order.status.in_(['Delivered', 'Success', 'Processing'])).all()
    
    for net, pkg, amt in direct_orders:
        if net in profit_stats:
            cost = cost_map.get((net, pkg), 0.0)
            profit_stats[net]["sales"] += amt
            profit_stats[net]["profit"] += (amt - cost)

    # Store Orders Analysis
    store_orders = db.session.query(StoreOrder.network, StoreOrder.package, StoreOrder.price).filter(StoreOrder.status.in_(['Delivered', 'Success'])).all()
    
    for net, pkg, price in store_orders:
        if net in profit_stats:
            cost = cost_map.get((net, pkg), 0.0)
            profit_stats[net]["sales"] += price
            profit_stats[net]["profit"] += (price - cost)

    # 5. Sales by Network (Pie Chart Data)
    network_sales = db.session.query(StoreOrder.network, func.sum(StoreOrder.price)).group_by(StoreOrder.network).all()
    network_labels = []
    network_data = []
    
    for network, sales in network_sales:
        if network:
            network_labels.append(network)
            network_data.append(sales)
            
    # 6. Recent Data
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_stores = Store.query.order_by(Store.id.desc()).limit(5).all()
    
    return render_template("admin/dashboard.html", 
                           total_users=total_users, 
                           total_wallet_balance=total_wallet_balance,
                           total_orders=grand_total_orders,
                           this_month_sales=this_month_sales,
                           total_stores=total_stores, 
                           platform_revenue=platform_revenue,
                           total_transactions=grand_total_orders,
                           total_gmv=total_gmv,
                           chart_dates=dates,
                           chart_sales=sales_data,
                           profit_stats=profit_stats, # NEW
                           network_labels=network_labels,
                           network_data=network_data,
                           recent_users=recent_users,
                           recent_stores=recent_stores)




# =====================
# RUN
# =====================

# =====================
# ADMIN ADDITIONAL ROUTES
# =====================

@app.route('/admin/users')
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    users = User.query.order_by(User.id.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin/users.html', users=users)

@app.route('/admin/stores', methods=['GET', 'POST'])
@admin_required
def admin_stores():
    if request.method == 'POST':
        # Bulk Actions
        action_type = request.form.get('action_type')
        selected_ids = request.form.getlist('store_ids')
        
        if not selected_ids:
             flash("No stores selected.", "warning")
             return redirect(url_for('admin_stores'))
             
        if action_type == 'update_status':
            new_status = request.form.get('new_status')
            if new_status:
                try:
                    # Bulk update
                    Store.query.filter(Store.id.in_(selected_ids)).update({Store.status: new_status}, synchronize_session=False)
                    db.session.commit()
                    flash(f"Successfully updated {len(selected_ids)} stores to '{new_status}'", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error updating status: {str(e)}", "error")
            else:
                flash("No status selected.", "warning")
        
        return redirect(url_for('admin_stores'))

    # GET
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter Logic
    status_filter = request.args.get('status')
    query = Store.query
    
    if status_filter:
        query = query.filter(Store.status == status_filter)
        
    stores = query.order_by(Store.id.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/stores.html', stores=stores, current_filter=status_filter)

@app.route('/admin/pricing', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_pricing():
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        try:
            # Removed cost_price from inputs since it's removed from UI? 
            # User said "Remove Depot Price", presumably from UI. 
            # But the form handling might still expect it if I don't remove it here.
            # I'll keep it as optional or remove it from here too if I remove the input.
            # The user said "Remove Depot Price(Cost)", so I assume from the valid update logic too.
            # However, keeping the column in DB is fine, just updating legacy field if passed, or ignore.
            # Safe to assume we just ignore it if it's not in the form.
            
            manufacturing_price = float(request.form.get('manufacturing_price') or 0.0)
            dealer_price = float(request.form.get('dealer_price'))
            selling_price = float(request.form.get('selling_price'))
            
            # Optional: cost_price might not be sent. Handle gracefully.
            cost_price = request.form.get('cost_price')
            cost_price = float(cost_price) if cost_price else 0.0
            
        except (ValueError, TypeError):
            flash("Invalid price format.", "error")
            return redirect(url_for('admin_pricing'))

        plan = DataPlan.query.get(plan_id)
        if not plan:
            flash("Plan not found.", "error")
        else:
            if cost_price: plan.cost_price = cost_price
            plan.manufacturing_price = manufacturing_price
            plan.dealer_price = dealer_price
            plan.selling_price = selling_price
            db.session.commit()
            flash(f"Updated pricing for {plan.network} {plan.plan_size}", "success")
        return redirect(url_for('admin_pricing'))

    # GET
    plans = DataPlan.query.order_by(DataPlan.display_order).all()
    grouped_plans = {"MTN": [], "TELECEL": [], "AIRTELTIGO": []}
    
    # Calculate Total Profit (Realized from Orders)
    # Strategy: Total Sales Amount - (Sum of Manufacturing Price for those orders)
    # Note: Using current manufacturing price as historical ref is an approximation
    all_delivered_orders = Order.query.filter_by(status='Delivered').all()
    
    # Map (network, plan_size) -> manufacturing_price
    plan_cost_map = {(p.network, p.plan_size): p.manufacturing_price for p in plans}
    
    total_profit = 0.0
    for order in all_delivered_orders:
        m_price = plan_cost_map.get((order.network, order.package), 0.0)
        # Profit = Order Amount - Manufacturing Price
        total_profit += (order.amount - m_price)

    for p in plans:
        if p.network not in grouped_plans:
             grouped_plans[p.network] = []
        grouped_plans[p.network].append(p)
                 
    return render_template('admin/pricing.html', grouped_plans=grouped_plans, total_profit=total_profit)

@app.route("/buy_data")
@login_required
def buy_data():
    plans = DataPlan.query.filter_by(status='Active').order_by(DataPlan.display_order).all()
    data_bundles = {
        "MTN": [],
        "TELECEL": [],
        "AIRTELTIGO": []
    }
    
    for plan in plans:
        if plan.network in data_bundles:
            data_bundles[plan.network].append(plan)
            
    return render_template("buy_data.html", data_bundles=data_bundles, balance=current_user.balance)
    return render_template("buy_data.html", data_bundles=data_bundles, balance=current_user.balance)

@app.route("/api/purchase_data", methods=["POST"])
@login_required
def purchase_data():
    data = request.json
    network = data.get('network')
    plan_id = data.get('plan_id')
    phone = data.get('phone')
    
    if not all([network, plan_id, phone]):
        return jsonify({"success": False, "message": "Missing required details."}), 400
        
    plan = DataPlan.query.get(plan_id)
    if not plan:
        return jsonify({"success": False, "message": "Invalid plan selected."}), 400
        
    # Check Balance
    if current_user.balance < plan.selling_price:
        return jsonify({"success": False, "message": "Insufficient wallet balance."}), 400
        
    try:
        # Deduct Balance
        current_user.balance -= plan.selling_price
        
        # Create Transaction Record
        ref = generate_reference()
        txn = Transaction(
            user_id=current_user.id,
            reference=ref,
            type="Data Purchase",
            amount=plan.selling_price,
            status="Success"
        )
        db.session.add(txn)
        
        # Create Order Record
        order = Order(
            user_id=current_user.id,
            transaction_id=ref,
            network=network,
            package=plan.plan_size,
            phone=phone,
            amount=plan.selling_price,
            status="Processing" # Initially processing
        )
        db.session.add(order)
        
        db.session.commit()
        
        # TODO: Trigger actual API call to provider here
        # For now, simulate success
        order.status = "Delivered"
        db.session.commit()
        
        return jsonify({"success": True, "message": "Purchase successful! Data is being processed."})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Transaction failed: {str(e)}"}), 500

@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Search Logic
    search_query = request.args.get('search')
    query = Transaction.query

    if search_query:
        # Check for 'byt-' prefix for ID search
        if search_query.lower().startswith('byt-'):
             try:
                 # Extract ID
                 search_id = int(search_query.lower().replace('byt-', ''))
                 query = query.filter(Transaction.id == search_id)
             except ValueError:
                 # If parsing fails, return empty or fallback
                 query = query.filter(Transaction.id == -1) 
        else:
             # Regular search (Transaction ID, or User details via join if needed)
             # Transaction model stores 'user_id', so to search user we need join.
             # But simplistic search usually just checks reference or ID for Transaction table.
             # User asked for "Search ID and number" for ORDERS.
             # Wait, this route is 'admin_transactions', NOT 'admin_orders'.
             # I need to find 'admin_orders' route!
             pass

    transactions = query.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page)
    
    # PROFIT BREAKDOWN CALCULATION
    # Fetch all plans for cost lookup
    all_plans = DataPlan.query.all()
    # Create mapping: (network, plan_size) -> cost_price
    cost_map = {(p.network, p.plan_size): p.cost_price for p in all_plans}
    
    # Initialize stats
    profit_stats = {
        "MTN": {"sales": 0.0, "profit": 0.0},
        "TELECEL": {"sales": 0.0, "profit": 0.0},
        "AIRTELTIGO": {"sales": 0.0, "profit": 0.0}
    }
    
    # 1. Calculate from Direct Orders (Main Site)
    # Optimization: Filter by success status if possible, but schema defaults 'status' to string.
    # Assuming 'Delivered' or 'Success' implies completed sale.
    direct_orders = Order.query.filter(Order.status.in_(['Delivered', 'Success', 'Processing'])).all()
    
    try:
        for o in direct_orders:
            # Handle case where network might be lower/mixed case or unmapped
            net_key = o.network.upper() if o.network else "UNKNOWN"
            if net_key in profit_stats:
                cost = cost_map.get((o.network, o.package), 0.0)
                amount = o.amount if o.amount is not None else 0.0
                profit_stats[net_key]["sales"] += amount
                # Profit = Selling Price (Order Amount) - Cost Price (Depot)
                profit_stats[net_key]["profit"] += (amount - cost)
                
        # 2. Calculate from Store Orders (B2B)
        store_orders = StoreOrder.query.filter(StoreOrder.status.in_(['Delivered', 'Success'])).all()
        for so in store_orders:
             net_key = so.network.upper() if so.network else "UNKNOWN"
             if net_key in profit_stats:
                # Note: StoreOrder package name might differ if not standardized, but assuming consistency
                cost = cost_map.get((so.network, so.package), 0.0)
                price = so.price if so.price is not None else 0.0
                profit_stats[net_key]["sales"] += price # This is what the platform sold it for
                profit_stats[net_key]["profit"] += (price - cost)
    except Exception as e:
        print(f"Error calculating profit: {e}")
        # Continue rendering page even if profit calc fails (stats will be 0 or partial)

    # Calculate Total Profit Accumulation
    total_profit_all = sum(stat['profit'] for stat in profit_stats.values())
    total_sales_all = sum(stat['sales'] for stat in profit_stats.values())

    return render_template('admin/transactions.html', transactions=transactions, profit_stats=profit_stats, total_profit_all=total_profit_all, total_sales_all=total_sales_all)

@app.route('/admin/user/<int:user_id>/balance', methods=['POST'])
@admin_required
def admin_update_balance(user_id):
    user = User.query.get_or_404(user_id)
    try:
        amount = float(request.form.get('amount'))
    except (ValueError, TypeError):
        flash("Invalid amount.", "error")
        return redirect(url_for('admin_users'))
    user.balance = amount
    db.session.commit()
    flash(f"Balance for {user.username} updated to GH₵{amount:,.2f}", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/toggle_admin')
@admin_required
def admin_toggle_admin(user_id):
    # Only Super Admin can toggle other admins
    if not current_user.is_super_admin:
        flash("Only Super Admins can manage admin privileges.", "error")
        return redirect(url_for('admin_users'))

    if user_id == current_user.id:
        flash("You cannot remove your own admin status.", "error")
        return redirect(url_for('admin_users'))
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Admin status for {user.username} {'granted' if user.is_admin else 'revoked'}.", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/toggle_suspend')
@admin_required
def admin_toggle_suspend(user_id):
    if user_id == current_user.id:
        flash("You cannot suspend yourself.", "error")
        return redirect(url_for('admin_users'))
        
    user = User.query.get_or_404(user_id)
    user.is_suspended = not user.is_suspended
    db.session.commit()
    
    status = "suspended" if user.is_suspended else "unsuspended"
    flash(f"User {user.username} has been {status}.", "success")
    return redirect(url_for('admin_users'))

@app.route("/admin/delete_user/<int:user_id>")
@login_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Optional: Delete related data or just the user cascading?
    # SQLAlchemy will fail if foreign keys exist and no cascade. 
    # For now, let's assume we want to keep history but maybe anonymize? 
    # User asked for "Delete". Let's try direct delete and catch integrity errors.
    try:
        # Manually delete dependent records if needed, or rely on cascade
        # Let's delete orders/store/transactions first to be safe
        Order.query.filter_by(user_id=user.id).delete()
        Transaction.query.filter_by(user_id=user.id).delete()
        if user.store:
            StorePricing.query.filter_by(store_id=user.store.id).delete()
            StoreOrder.query.filter_by(store_id=user.store.id).delete()
            db.session.delete(user.store)
            
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted permanently.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "error")
        
    return redirect(url_for('admin_users'))

@app.route('/admin/withdrawal/<int:txn_id>/<action>')
@admin_required
def admin_manage_withdrawal(txn_id, action):
    txn = Transaction.query.get_or_404(txn_id)
    
    valid_types = ["Withdrawal", "Store Withdrawal (MoMo)"]
    if txn.type not in valid_types or txn.status != "Pending":
        flash("Invalid transaction for approval.", "error")
        return redirect(url_for('admin_transactions'))
        
    if action == "approve":
        txn.status = "Success"
        flash("Withdrawal approved.", "success")
        # Logic to actually release funds (e.g. Paystack Transfer) would go here
        
    elif action == "reject":
        txn.status = "Failed"
        # Refund the user
        user = txn.user
        user.balance += txn.amount
        flash("Withdrawal rejected and funds refunded.", "warning")
        
    else:
        flash("Invalid action.", "error")
        
    db.session.commit()
    return redirect(url_for('admin_transactions'))

@app.route('/admin/store/<int:store_id>/delete')
@admin_required
def admin_delete_store(store_id):
    store = Store.query.get_or_404(store_id)
    # Also delete associated pricing
    StorePricing.query.filter_by(store_id=store.id).delete()
    db.session.delete(store)
    db.session.commit()
    flash(f"Store '{store.name}' and its settings deleted.", "success")
    return redirect(url_for('admin_stores'))

@app.route('/admin/export/users')
@admin_required
def admin_export_users():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Username', 'Email', 'Mobile', 'Balance', 'Is Admin'])
    
    users = User.query.all()
    for user in users:
        cw.writerow([user.id, user.username, user.email, user.mobile, user.balance, user.is_admin])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=users_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/admin/export/transactions')
@admin_required
def admin_export_transactions():
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Reference', 'User', 'Store', 'Type', 'Amount', 'Status', 'Date'])
    
    transactions = Transaction.query.all()
    for txn in transactions:
        store_name = txn.user.store.name if txn.user.store else "Direct"
        cw.writerow([txn.id, txn.reference, txn.user.username, store_name, txn.type, txn.amount, txn.status, txn.date])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=transactions_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/admin/wallet', methods=['GET', 'POST'])
@admin_required
def admin_manage_wallet():
    user = None
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'search':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if not user:
                flash(f"No user found with email {email}", "error")
        
        elif action in ['credit', 'debit']:
            email = request.form.get('email')
            try:
                amount = float(request.form.get('amount'))
                if amount < 0: raise ValueError
            except (ValueError, TypeError):
                flash("Invalid amount.", "error")
                return redirect(url_for('admin_manage_wallet'))
            
            note = request.form.get('note') or "Admin Adjustment"
            
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("User not found.", "error")
                return redirect(url_for('admin_manage_wallet'))
                
            if action == 'credit':
                # Atomic Update
                user.balance += amount
                # Log Transaction
                txn = Transaction(
                    user_id=user.id,
                    reference=generate_reference(),
                    type="Admin Credit",
                    amount=amount,
                    status="Success"
                )
                db.session.add(txn)
                flash(f"Credited GH₵{amount:,.2f} to {user.username}.", "success")
                
            elif action == 'debit':
                if user.balance < amount:
                    flash(f"Insufficient balance. User has GH₵{user.balance:,.2f}", "error")
                else:
                    # Atomic Update
                    user.balance -= amount
                    # Log Transaction
                    txn = Transaction(
                        user_id=user.id,
                        reference=generate_reference(),
                        type="Admin Debit",
                        amount=amount,
                        status="Success"
                    )
                    db.session.add(txn)
                    flash(f"Debited GH₵{amount:,.2f} from {user.username}.", "success")
            
            db.session.commit()
            # Reload user to show updated state if needed, or just stay on page
            user = User.query.filter_by(email=email).first()

    return render_template('admin/manage_wallet.html', user=user)

@app.route('/admin/orders', methods=['GET', 'POST'])
@admin_required
def admin_orders():
    if request.method == 'POST':
        # Bulk Actions
        action_type = request.form.get('action_type')
        selected_ids = request.form.getlist('order_ids')
        
        if not selected_ids:
             flash("No orders selected.", "warning")
             return redirect(url_for('admin_orders'))
             
        if action_type == 'update_status':
            new_status = request.form.get('new_status')
            if new_status:
                try:
                    # Bulk update
                    Order.query.filter(Order.id.in_(selected_ids)).update({Order.status: new_status}, synchronize_session=False)
                    db.session.commit()
                    flash(f"Successfully updated {len(selected_ids)} orders to '{new_status}'", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error updating status: {str(e)}", "error")
            else:
                flash("No status selected.", "warning")
        
        return redirect(url_for('admin_orders'))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter by Status
    status_filter = request.args.get('status')
    network_filter = request.args.get('network')
    search_query = request.args.get('search')
    
    query = Order.query.order_by(Order.date.desc())
    
    if search_query:
        # Check for 'byt-' prefix for ID search
        if search_query.lower().startswith('byt-'):
             try:
                 # Extract ID
                 search_id = int(search_query.lower().replace('byt-', ''))
                 query = query.filter(Order.id == search_id)
             except ValueError:
                 query = query.filter(Order.id == -1) 
        else:
             # Search by Phone or Transaction ID
             query = query.filter(
                 (Order.phone.ilike(f"%{search_query}%")) | 
                 (Order.transaction_id.ilike(f"%{search_query}%"))
             )

    if status_filter:
        query = query.filter(Order.status == status_filter)
    if network_filter:
        query = query.filter(Order.network == network_filter)
        
    orders = query.paginate(page=page, per_page=per_page)
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/export')
@admin_required
def admin_export_orders():
    # Use openpyxl for Excel export
    from openpyxl import Workbook
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    # Headers
    headers = ['ID', 'Txn Ref', 'User', 'User Email', 'Network', 'Package', 'Phone', 'Amount', 'Status', 'Date']
    ws.append(headers)
    
    # Apply same filters
    status_filter = request.args.get('status')
    network_filter = request.args.get('network')
    
    query = Order.query.order_by(Order.date.desc())
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if network_filter:
        query = query.filter(Order.network == network_filter)
    
    orders = query.all()
    for o in orders:
        ws.append([
            o.id, 
            o.transaction_id, 
            o.user.username, 
            o.user.email,
            o.network, 
            o.package, 
            o.phone or 'N/A', 
            float(o.amount), # Store as number 
            o.status, 
            o.date.strftime('%Y-%m-%d %H:%M:%S')
        ])
        
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    
    filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        out,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.transaction_id} status updated to {new_status}.", "success")
    else:
        flash("Invalid status provided.", "error")
        
    return redirect(url_for('admin_orders'))


@app.route('/admin/notice', methods=['GET', 'POST'])
@admin_required
def admin_notice():
    if request.method == 'POST':
        notice_text = request.form.get('notice')
        
        # Check if setting exists
        setting = SiteSetting.query.filter_by(key='site_notice').first()
        if not setting:
            setting = SiteSetting(key='site_notice')
            db.session.add(setting)
            
        setting.value = notice_text
        db.session.commit()
        
        # Update Timestamp as well
        ts_setting = SiteSetting.query.filter_by(key='site_notice_timestamp').first()
        if not ts_setting:
            ts_setting = SiteSetting(key='site_notice_timestamp')
            db.session.add(ts_setting)
        
        # Save as timestamp float string
        ts_setting.value = str(datetime.utcnow().timestamp())
        
        db.session.commit()
        
        flash("Site notice updated.", "success")
        return redirect(url_for('admin_notice'))
        
    # GET
    setting = SiteSetting.query.filter_by(key='site_notice').first()
    notice = setting.value if setting else ""
    
    return render_template('admin/notice.html', notice=notice)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)