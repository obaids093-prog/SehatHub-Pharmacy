"""
SehatHub - Main Flask Application
This is the entry point of our website. We run this file to start the server.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os

# Load secret variables from .env file (database password, secret key, etc.)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')

# Deployment Hygiene & Hardening
from datetime import timedelta
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file upload size
app.config['SESSION_COOKIE_SECURE'] = True          # Ensure cookies are sent over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True        # Prevent JS access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'       # CSRF mitigation
app.config['TEMPLATES_AUTO_RELOAD'] = True          # Auto-reload templates for development
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # "Remember Me" session length

# ============================================================
# REGISTER BLUEPRINTS
# A Blueprint groups related routes into their own file (see routes/auth.py).
# Registering it here "plugs it into" the main app so its routes become active.
# ============================================================
from routes.auth import auth_bp
app.register_blueprint(auth_bp)

from routes.customer import customer_bp
app.register_blueprint(customer_bp)

from routes.pharmacist import pharmacist_bp
app.register_blueprint(pharmacist_bp)

from routes.admin import admin_bp
app.register_blueprint(admin_bp)

from routes.delivery import delivery_bp
app.register_blueprint(delivery_bp)

# ============================================================
# GLOBAL CSRF TOKEN
# Makes {{ csrf_token }} available in EVERY template automatically
# (customer, pharmacist, delivery, auth, admin - all of them) without
# each route having to import and call generate_csrf_token() itself.
# The admin module already did this manually per-route before; this
# doesn't break that (it's harmless to pass the same value twice),
# it just means new modules don't need to repeat the same line.
# ============================================================
@app.context_processor
def inject_csrf_token():
    from utils.csrf import generate_csrf_token
    return {'csrf_token': generate_csrf_token()}


# ============================================================
# CONTEXT PROCESSOR
# This function runs automatically before EVERY template is rendered,
# and whatever it returns becomes available in ALL templates without
# us needing to pass it manually in every single route. We use this
# to make the cart item count AND the category list available to the
# navbar in base.html, since base.html is shared by every page.
# ============================================================
@app.context_processor
def inject_navbar_data():
    from flask import session
    from config.database import get_db_connection

    navbar_data = {'cart_item_count': 0, 'navbar_categories': [], 'prescription_notification_count': 0, 'prescription_notifications': []}

    connection = get_db_connection()
    if connection is None:
        return navbar_data

    try:
        cursor = connection.cursor(dictionary=True)

        # Categories are needed on every page for the navbar's second
        # row (mirrors D.Watson-style category tabs), regardless of
        # whether the person is logged in.
        cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
        navbar_data['navbar_categories'] = cursor.fetchall()

        # Cart count only applies to logged-in customers
        if 'user_id' in session:
            cursor.execute("SELECT customer_id FROM customers WHERE user_id = %s", (session['user_id'],))
            customer = cursor.fetchone()

            if customer:
                # SUM(quantity) counts total items (e.g. 2 Panadol + 3 Brufen = 5),
                # not just the number of distinct cart rows
                cursor.execute("SELECT SUM(quantity) AS total FROM cart_items WHERE customer_id = %s", (customer['customer_id'],))
                result = cursor.fetchone()
                navbar_data['cart_item_count'] = result['total'] or 0

                # Fetch initial notifications from the new dedicated table
                cursor.execute(
                    """SELECT notification_id, title, message, link, icon, is_read, created_at 
                       FROM notifications 
                       WHERE user_id = %s 
                       ORDER BY created_at DESC LIMIT 20""",
                    (session['user_id'],)
                )
                notifications = cursor.fetchall()
                navbar_data['unread_notification_count'] = sum(1 for n in notifications if not n['is_read'])
                navbar_data['notifications'] = notifications

        cursor.close()
        return navbar_data
    finally:
        connection.close()

# ============================================================
# MARK NOTIFICATIONS AS READ API
# ============================================================
@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    from flask import session, jsonify, request
    from config.database import get_db_connection
    from utils.csrf import validate_csrf_token
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    if not validate_csrf_token(request.headers.get('X-CSRFToken')):
        return jsonify({'status': 'error', 'message': 'Invalid CSRF token'}), 403
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error'}), 500
        
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
            (session['user_id'],)
        )
        connection.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error marking notifications read: {e}")
        return jsonify({'status': 'error'}), 500
    finally:
        connection.close()
# ============================================================
# NO-CACHE HEADERS FOR LOGGED-IN PAGES
# Without this, the browser can cache a rendered page (e.g. the
# cart, a dashboard) and show that CACHED version again later -
# including after logging out and back in as a DIFFERENT user, or
# via the browser's Back button after logging out. That makes it
# look like "the new account has the old account's cart items",
# when really the browser just never asked the server for a fresh
# page. This runs after every request and tells the browser not to
# cache any page while a session is active, so every page load
# (and every login/logout) always fetches fresh data from the server.
# ============================================================
@app.after_request
def add_no_cache_headers(response):
    from flask import session
    if 'user_id' in session:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response


# ============================================================
# BASIC TEST ROUTE - Home Page
# ============================================================
@app.route('/page/<page_slug>')
def coming_soon(page_slug):
    """
    Generic placeholder route for footer links that don't have real
    designs/content yet (About Us, Contact Us, Privacy Policy, Terms
    of Service, Careers, Wellness Products, Personal Care, Medical
    Devices). Turns the URL slug into a readable title.
    """
    page_title = page_slug.replace('-', ' ').title()
    return render_template('coming_soon.html', page_title=page_title)


@app.route('/refund-policy')
def refund_policy():
    """
    Dedicated Refund Policy page. Replaces the old homepage popup
    banner with a real page (see templates/refund_policy.html),
    linked from the footer.
    """
    return render_template('refund_policy.html')


@app.route('/about-us')
def about_us():
    """Dedicated About Us page (replaces the old coming_soon placeholder)."""
    return render_template('about_us.html')


@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    """
    Dedicated Contact Us page (replaces the old coming_soon placeholder).
    The message form doesn't have a support-ticket system behind it yet
    (out of scope for now) - it just confirms receipt with a flash
    message. Wiring it to actually store/email messages is a natural
    next step if that's needed later.
    """
    from utils.csrf import validate_csrf_token

    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return render_template('contact_us.html')

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please fill in all fields.', 'error')
            return render_template('contact_us.html')

        flash("Thanks for reaching out! We'll get back to you soon.", 'success')
        return redirect(url_for('contact_us'))

    return render_template('contact_us.html')


@app.route('/privacy-policy')
def privacy_policy():
    """Dedicated Privacy Policy page (replaces the old coming_soon placeholder)."""
    return render_template('privacy_policy.html')


@app.route('/terms-of-service')
def terms_of_service():
    """Dedicated Terms of Service page (replaces the old coming_soon placeholder)."""
    return render_template('terms_of_service.html')


@app.route('/newsletter-subscribe', methods=['POST'])
def newsletter_subscribe():
    """
    Handles the "Join our healthy community" footer form. Like the
    Contact Us form, this doesn't have a real mailing-list service
    wired up yet (out of scope for now) - it validates the email and
    confirms the subscription. Connecting it to an actual mailing
    list provider is a natural next step if that's needed later.
    """
    from utils.csrf import validate_csrf_token
    from utils.validators import is_valid_email

    if not validate_csrf_token(request.form.get('csrf_token')):
        msg = 'Your session expired or this request looked suspicious. Please try again.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('home'))

    email = request.form.get('email', '').strip()
    if not is_valid_email(email):
        msg = 'Please enter a valid email address.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('home'))

    msg = "You're subscribed! Watch your inbox for health tips and offers."
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': msg})
    
    flash(msg, 'success')
    return redirect(url_for('home'))

@app.route('/api/public-stats')
def api_public_stats():
    from config.database import get_db_connection
    connection = get_db_connection()
    if not connection:
        return jsonify({})
    try:
        cursor = connection.cursor(dictionary=True)
        stats = {}
        cursor.execute("SELECT COUNT(*) AS count FROM customers")
        stats['customers'] = cursor.fetchone()['count'] or 0
        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'delivered'")
        stats['orders_delivered'] = cursor.fetchone()['count'] or 0
        cursor.execute("SELECT COUNT(*) AS count FROM pharmacists")
        stats['pharmacists'] = cursor.fetchone()['count'] or 0
        cursor.execute("SELECT COUNT(DISTINCT city) AS count FROM customers WHERE city IS NOT NULL AND city != ''")
        stats['cities'] = cursor.fetchone()['count'] or 0
        return jsonify(stats)
    finally:
        connection.close()

@app.route('/')
def home():
    """
    Home page. Pulls a handful of real, active medicines from the
    database to power the "Trending Products" and "Bestsellers"
    sections - these used to be hardcoded fake products with fake
    prices that could never actually be added to cart.
    """
    from flask import session
    
    # If a staff member visits the root URL, redirect them directly to their dashboard.
    # They have no need to browse the customer-facing storefront.
    if 'user_id' in session and session.get('role') in ['admin', 'pharmacist', 'delivery']:
        if session['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session['role'] == 'pharmacist':
            return redirect(url_for('pharmacist.dashboard'))
        elif session['role'] == 'delivery':
            return redirect(url_for('delivery.dashboard'))

    from config.database import get_db_connection

    trending = []
    bestsellers = []
    category_products = {}
    top_brands = []
    # Real counts for the "Trusted by..." badges and the animated stats
    # counter - these used to be hardcoded fake numbers (50,000+ in one
    # place, 1M+ in another, 50 in a third) that all contradicted each
    # other. Pulling one real number from the database and reusing it
    # everywhere means it's always internally consistent, and it's an
    # honest number instead of an invented one.
    stats = {'customers': 0, 'orders_delivered': 0, 'pharmacists': 0, 'cities': 0}

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT COUNT(*) AS count FROM customers")
            stats['customers'] = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'delivered'")
            stats['orders_delivered'] = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM pharmacists")
            stats['pharmacists'] = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(DISTINCT city) AS count FROM customers WHERE city IS NOT NULL AND city != ''")
            stats['cities'] = cursor.fetchone()['count'] or 0

            cursor.execute("""
                WITH RankedMedicines AS (
                    SELECT
                        m.medicine_id, m.name, m.type, m.image_url,
                        b.name AS brand_name, COALESCE(c.name, 'Other') AS category_name, c.category_id,
                        MIN(mv.price) AS min_price,
                        (SELECT mv2.variant_id FROM medicine_variants mv2
                         WHERE mv2.medicine_id = m.medicine_id ORDER BY mv2.price ASC LIMIT 1) AS cheapest_variant_id,
                        ROW_NUMBER() OVER(PARTITION BY COALESCE(c.name, 'Other') ORDER BY RAND()) as rn
                    FROM medicines m
                    LEFT JOIN brands b ON m.brand_id = b.brand_id
                    LEFT JOIN categories c ON m.category_id = c.category_id
                    LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
                    WHERE m.is_active = TRUE
                    GROUP BY m.medicine_id, m.name, m.type, m.image_url, b.name, c.name, c.category_id
                )
                SELECT * FROM RankedMedicines WHERE rn <= 4
            """)
            results = cursor.fetchall()
            
            # Group products by category (max 4 per category)
            category_products = {}
            for row in results:
                cat_key = (row['category_name'], row['category_id'])
                if cat_key not in category_products:
                    category_products[cat_key] = []
                category_products[cat_key].append(row)
            
            # Fetch random diverse products for trending (hero section)
            cursor.execute("""
                SELECT m.medicine_id, m.name, m.image_url, MIN(mv.price) AS min_price,
                       (SELECT mv2.variant_id FROM medicine_variants mv2
                        WHERE mv2.medicine_id = m.medicine_id ORDER BY mv2.price ASC LIMIT 1) AS cheapest_variant_id
                FROM medicines m LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
                WHERE m.is_active = TRUE GROUP BY m.medicine_id, m.name, m.image_url ORDER BY RAND() LIMIT 3
            """)
            trending = cursor.fetchall()

            # Fetch random diverse products for bestsellers
            cursor.execute("""
                SELECT m.medicine_id, m.name, m.image_url, MIN(mv.price) AS min_price, b.name AS brand_name,
                       (SELECT mv2.variant_id FROM medicine_variants mv2
                        WHERE mv2.medicine_id = m.medicine_id ORDER BY mv2.price ASC LIMIT 1) AS cheapest_variant_id
                FROM medicines m LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id LEFT JOIN brands b ON m.brand_id = b.brand_id
                WHERE m.is_active = TRUE GROUP BY m.medicine_id, m.name, m.image_url, b.name ORDER BY RAND() LIMIT 8
            """)
            bestsellers = cursor.fetchall()
            
            # Fetch Top Brands
            cursor.execute("SELECT brand_id, name FROM brands WHERE name IS NOT NULL AND name != 'Eisai Pharmaceuticals' ORDER BY RAND() LIMIT 6")
            top_brands = cursor.fetchall()
            
            cursor.close()
        finally:
            connection.close()

    return render_template('index.html', category_products=category_products, trending=trending, bestsellers=bestsellers, stats=stats, top_brands=top_brands)


# ============================================================
# CUSTOM ERROR PAGES
# Without these, a wrong URL or an unexpected server error shows
# Flask's plain default error page - not on-brand, and not
# reassuring for a customer mid-checkout. These replace both with
# a simple branded page that points back home.
# ============================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


# ============================================================
# Run the Flask development server
# ============================================================
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', debug=debug_mode, port=5000)