from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import csv
import io
import re
import os
import requests
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

failed_logins = {}  # key = email, value = count
MAX_ATTEMPTS = 4

app = Flask(__name__)

# =====================
# CONFIG
# =====================
app.config["SECRET_KEY"] = "super-secret-key-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Context Processor for Cache Busting
@app.context_processor
def inject_version():
    return {'version': int(datetime.utcnow().timestamp())}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

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
    selling_price = db.Column(db.Float, nullable=False, default=0.0) # Site Price (Revenue)
    display_order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Active') # Active, Inactive

# =====================
# CONSTANTS
# =====================
# Base "Dealer" Prices
DEALER_PACKAGES = {
    "MTN": [
        {"package": "1 GB", "price": 4.60},
        {"package": "2 GB", "price": 9.60},
        {"package": "3 GB", "price": 14.00},
        {"package": "4 GB", "price": 18.50},
    ],
    "TELECEL": [],
    "AIRTELTIGO": []
}

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
        email = request.form.get('email')
        password = request.form.get('password')

        # check if input is a valid email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'error')
            attempts = failed_logins.get(email, 0) if email else 0
            return render_template('login.html', attempts=attempts, email=email)

        user = User.query.filter_by(email=email).first()

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
    data_bundles = {
        "MTN": [
            {"size": "1 GB", "price": "GH₵4.60", "expiry": "No-Expiry"},
            {"size": "2 GB", "price": "GH₵9.60", "expiry": "No-Expiry"},
            {"size": "3 GB", "price": "GH₵14.00", "expiry": "No-Expiry"},
            {"size": "4 GB", "price": "GH₵18.50", "expiry": "No-Expiry"},
        ],
        "TELECEL": [],
        "AIRTELTIGO": []
    }

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

@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    amount = float(request.form.get("amount"))
    reference = f"DEP-{int(datetime.utcnow().timestamp())}" # Mock reference

    # Mock Paystack Redirect
    # In reality, you'd call Paystack API to initialize, then get an auth URL
    # For now, we simulate a successful deposit after a "redirect"
    
    # Create Pending Transaction
    txn = Transaction(
        user_id=current_user.id,
        reference=reference,
        type="Deposit",
        amount=amount,
        status="Success" # Auto-success for demo
    )
    current_user.balance += amount
    db.session.add(txn)
    db.session.commit()

    flash(f"Deposit of GH₵{amount} successful!", "success")
    return redirect(url_for('wallet'))

@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    amount = float(request.form.get("amount"))
    
    if amount > current_user.balance:
        flash("Insufficient balance", "error")
        return redirect(url_for('wallet'))

    reference = f"WTH-{int(datetime.utcnow().timestamp())}"
    
    txn = Transaction(
        user_id=current_user.id,
        reference=reference,
        type="Withdrawal",
        amount=amount,
        status="Pending" # Withdrawal usually manual or async
    )
    current_user.balance -= amount
    db.session.add(txn)
    db.session.commit()

    flash(f"Withdrawal request of GH₵{amount} placed.", "info")
    return redirect(url_for('wallet'))


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
    
    return render_template("store.html", store=my_store, orders=store_orders, pricing_list=store_pricing, dealer_packages=DEALER_PACKAGES)

@app.route("/store/add_pricing", methods=["POST"])
@login_required
def add_pricing():
    store = current_user.store
    network = request.form.get("network")
    package_name = request.form.get("package_name")
    dealer_price = float(request.form.get("dealer_price"))
    selling_price = float(request.form.get("selling_price"))
    
    # Validation: Selling Price cannot be less than Dealer Price
    if selling_price < dealer_price:
        flash("Selling Price cannot be lower than the Dealer Price.", "error")
        return redirect(url_for("store"))
        
    # Check if package already exists for this store
    existing = StorePricing.query.filter_by(store_id=store.id, network=network, package_name=package_name).first()
    if existing:
        existing.dealer_price = dealer_price
        existing.selling_price = selling_price
        flash(f"Updated pricing for {network} {package_name}.", "success")
    else:
        new_pricing = StorePricing(
            store_id=store.id,
            network=network,
            package_name=package_name,
            dealer_price=dealer_price,
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
    store.whatsapp_group_link = request.form.get("whatsapp_group_link")
    store.description = request.form.get("description")
    store.notice = request.form.get("notice")
    
    db.session.commit()
    flash("Store settings updated!", "success")
    return redirect(url_for("store"))

@app.route("/store/withdraw", methods=["POST"])
@login_required
def store_withdraw():
    amount = float(request.form.get("amount"))
    store = current_user.store
    
    if amount <= store.credit_balance:
        # Transfer to main wallet
        store.credit_balance -= amount
        store.total_withdrawn += amount
        current_user.balance += amount
        
        # Log as transaction
        txn = Transaction(
            user_id=current_user.id,
            reference=f"ST-WTH-{int(datetime.utcnow().timestamp())}",
            type="Store Credit Transfer",
            amount=amount,
            status="Success"
        )
        db.session.add(txn)
        
        # Log to Store Orders History
        new_order = StoreOrder(
            store_id=store.id,
            phone=current_user.mobile or "N/A",  # Or "Wallet Transfer"
            email=current_user.email,
            network="System",
            package="Transfer to Wallet",
            price=amount,
            commission=0,
            status="Success"
        )
        db.session.add(new_order)
        
        db.session.commit()
        flash(f"Transferred GH₵{amount} from store to main wallet.", "success")
    else:
        flash("Insufficient store credit.", "error")
        
    return redirect(url_for("store"))

@app.route("/store/withdraw/momo", methods=["POST"])
@login_required
def store_withdraw_momo():
    amount = float(request.form.get("amount"))
    network = request.form.get("network")
    phone = request.form.get("phone")
    store = current_user.store

    # 1. Validation
    if amount > store.credit_balance:
        flash("Insufficient store credit.", "error")
        return redirect(url_for("store"))
        
    if amount < 10.00:
        flash("Minimum withdrawal amount is GH₵ 10.00", "error")
        return redirect(url_for("store"))
    
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    # Fallback to config if env not set, though env is preferred
    if not PAYSTACK_SECRET_KEY:
         PAYSTACK_SECRET_KEY = app.config.get("PAYSTACK_SECRET_KEY")

    if not PAYSTACK_SECRET_KEY:
        flash("System error: Payment gateway not configured. Please contact admin.", "error")
        return redirect(url_for("store"))

    # Map Network to Paystack Bank Code
    # MTN -> 'MTN', Telecel -> 'VOD', AirtelTigo -> 'ATL'
    bank_code_map = {
        'MTN': 'MTN',
        'TELECEL': 'VOD',
        'AIRTELTIGO': 'ATL'
    }
    bank_code = bank_code_map.get(network)
    
    if not bank_code:
        flash("Invalid Network selected.", "error")
        return redirect(url_for("store"))

    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        # 2. Create Transfer Recipient
        recipient_url = "https://api.paystack.co/transferrecipient"
        recipient_data = {
            "type": "mobile_money",
            "name": f"{current_user.first_name} {current_user.last_name}",
            "account_number": phone,
            "bank_code": bank_code,
            "currency": "GHS"
        }
        
        rec_response = requests.post(recipient_url, json=recipient_data, headers=headers)
        rec_json = rec_response.json()

        if not rec_json.get('status'):
            flash(f"Error creating recipient: {rec_json.get('message')}", "error")
            return redirect(url_for("store"))
        
        recipient_code = rec_json['data']['recipient_code']

        # 3. Initiate Transfer
        transfer_url = "https://api.paystack.co/transfer"
        transfer_data = {
            "source": "balance", 
            "reason": "Store Withdrawal", 
            "amount": int(amount * 100), # Amount in pesewas
            "recipient": recipient_code
        }
        
        transfer_res = requests.post(transfer_url, json=transfer_data, headers=headers)
        transfer_json = transfer_res.json()

        if transfer_json.get('status'):
            # Success - Update DB
            store.credit_balance -= amount
            store.total_withdrawn += amount
            
            txn = Transaction(
                user_id=current_user.id,
                reference=f"ST-MOMO-{int(datetime.utcnow().timestamp())}",
                type="Store Withdrawal (MoMo)",
                amount=amount,
                status="Pending" # Paystack transfers are async
            )
            db.session.add(txn)

            # Log to Store Orders History
            new_order = StoreOrder(
                store_id=store.id,
                phone=phone,
                email=current_user.email,
                network=network,
                package="Withdraw to MoMo",
                price=amount,
                commission=0,
                status="Pending" # Pending
            )
            db.session.add(new_order)

            db.session.commit()
            
            flash(f"Withdrawal of GH₵{amount} to {phone} ({network}) initiated successfully.", "success")
        else:
            flash(f"Transfer failed: {transfer_json.get('message')}", "error")

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        print(f"Paystack Error: {e}")

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
        # We need the slug to redirect back. 
        # Since we might not have it if lookups fail, we'll try to find the store first.
        store = Store.query.get(store_id)
        if store:
            return redirect(url_for('public_store', slug=store.slug))
        return redirect(url_for('index')) # Fallback
        
    store = Store.query.get_or_404(store_id)
    pricing = StorePricing.query.get_or_404(pricing_id)
    
    # Create Order
    new_order = StoreOrder(
        store_id=store.id,
        phone=phone,
        email=email,
        network=pricing.network,
        package=pricing.package_name,
        price=pricing.selling_price,
        commission=pricing.selling_price - pricing.dealer_price, # profit for store owner
        status="Success" # Auto-success for demo
    )
    
    # Update Store Stats
    store.total_sales += pricing.selling_price
    store.credit_balance += (pricing.selling_price - pricing.dealer_price)
    
    db.session.add(new_order)
    db.session.commit()
    
    flash(f"Payment successful! You purchased {pricing.network} {pricing.package_name}.", "success")
    return redirect(url_for('public_store', slug=store.slug))

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/profile/security", methods=["POST"])
@login_required
def security_update():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    # Check current password
    if not check_password_hash(current_user.password, current_password):
        flash("Incorrect current password.", "error")
        return redirect(url_for("profile"))
    
    # Validate new password
    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("profile"))
        
    if len(new_password) < 6:
        flash("Password must be at least 6 characters long.", "error")
        return redirect(url_for("profile"))
    
    # Update password
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    
    flash("Password updated successfully!", "success")
    return redirect(url_for("profile"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        
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

    # 4. Profit Calculation (NEW)
    all_plans = DataPlan.query.all()
    cost_map = {(p.network, p.plan_size): p.cost_price for p in all_plans}
    
    profit_stats = {
        "MTN": {"sales": 0.0, "profit": 0.0},
        "TELECEL": {"sales": 0.0, "profit": 0.0},
        "AIRTELTIGO": {"sales": 0.0, "profit": 0.0}
    }
    
    # Direct Orders Profit
    # Optimization: Loading all orders might be heavy for a dashboard. 
    # For now, we will do it to be accurate as requested.
    all_direct_orders = Order.query.filter(Order.status.in_(['Delivered', 'Success', 'Processing'])).all()
    for o in all_direct_orders:
        if o.network in profit_stats:
            cost = cost_map.get((o.network, o.package), 0.0)
            profit_stats[o.network]["sales"] += o.amount
            profit_stats[o.network]["profit"] += (o.amount - cost)
            
    # Store Orders Profit
    all_store_orders = StoreOrder.query.filter(StoreOrder.status.in_(['Delivered', 'Success'])).all()
    for so in all_store_orders:
         if so.network in profit_stats:
            cost = cost_map.get((so.network, so.package), 0.0)
            profit_stats[so.network]["sales"] += so.price
            profit_stats[so.network]["profit"] += (so.price - cost)

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

@app.route('/admin/pricing', methods=['GET', 'POST'])
@admin_required
def admin_pricing():
    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        cost_price = request.form.get('cost_price')
        selling_price = request.form.get('selling_price')
        
        plan = DataPlan.query.get_or_404(plan_id)
        if cost_price:
            plan.cost_price = float(cost_price)
        if selling_price:
            plan.selling_price = float(selling_price)
            
        db.session.commit()
        flash(f"Updated pricing for {plan.network} - {plan.plan_size}", "success")
        return redirect(url_for('admin_pricing'))
        
    plans = DataPlan.query.order_by(DataPlan.network, DataPlan.display_order).all()
    # Group by network
    grouped_plans = {}
    for p in plans:
        if p.network not in grouped_plans:
            grouped_plans[p.network] = []
        grouped_plans[p.network].append(p)
        
    return render_template('admin/pricing.html', grouped_plans=grouped_plans)


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

@app.route('/admin/stores')
@admin_required
def admin_stores():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    stores = Store.query.order_by(Store.id.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin/stores.html', stores=stores)

@app.route("/buy_data")
@login_required
def buy_data():
    plans = DataPlan.query.filter_by(status='Active').order_by(DataPlan.display_order).all()
    data_bundles = {
        "MTN": [],
        "TELECEL": [],
        "AIRTELTIGO": []
    }
# @app.route("/buy_data")
# ... replaced by DB driven route ...

# ... (omitted routes)

@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter Parameters
    search_query = request.args.get('search', '').strip()
    txn_type = request.args.get('type', '')
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Transaction.query

    # Apply Filters
    if search_query:
        query = query.join(Transaction.user).filter(
            db.or_(
                Transaction.reference.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        )
    
    if txn_type:
        query = query.filter(Transaction.type == txn_type)
    
    if status:
        query = query.filter(Transaction.status == status)

    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Transaction.date >= start_date)
        except ValueError:
            pass # Ignore invalid date format
            
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
             # Add one day to include the end date fully (up to 23:59:59 effectively if checking equality, but here we just do < next day usually, or just use date)
             # Simpler: just match date part. But field is DateTime.
            end_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Transaction.date < end_date)
        except ValueError:
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
    
    for o in direct_orders:
        if o.network in profit_stats:
            cost = cost_map.get((o.network, o.package), 0.0)
            profit_stats[o.network]["sales"] += o.amount
            # Profit = Selling Price (Order Amount) - Cost Price (Depot)
            profit_stats[o.network]["profit"] += (o.amount - cost)
            
    # 2. Calculate from Store Orders (B2B)
    store_orders = StoreOrder.query.filter(StoreOrder.status.in_(['Delivered', 'Success'])).all()
    for so in store_orders:
         if so.network in profit_stats:
            # Note: StoreOrder package name might differ if not standardized, but assuming consistency
            cost = cost_map.get((so.network, so.package), 0.0)
            profit_stats[so.network]["sales"] += so.price # This is what the platform sold it for
            profit_stats[so.network]["profit"] += (so.price - cost)

    return render_template('admin/transactions.html', transactions=transactions, profit_stats=profit_stats)

@app.route('/admin/user/<int:user_id>/balance', methods=['POST'])
@admin_required
def admin_update_balance(user_id):
    user = User.query.get_or_404(user_id)
    amount = float(request.form.get('amount'))
    user.balance = amount
    db.session.commit()
    flash(f"Balance for {user.username} updated to GH₵{amount:,.2f}", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/toggle_admin')
@admin_required
def admin_toggle_admin(user_id):
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

@app.route('/admin/user/<int:user_id>/delete')
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete yourself.", "error")
        return redirect(url_for('admin_users'))
        
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
    
    if txn.type != "Withdrawal" or txn.status != "Pending":
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
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')