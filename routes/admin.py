"""
SehatHub - Admin Routes
Dashboard, User Management (including creating Pharmacist/Delivery/Admin
staff accounts), and Sales Reports.

SECURITY NOTES (read before modifying this file):
- EVERY route below is protected with @role_required('admin') - a
  customer or pharmacist who is logged in cannot reach any of these
  pages just by typing the URL.
- Every SQL query uses parameterized placeholders (%s) - never raw
  string formatting - to prevent SQL injection.
- Passwords are always hashed with bcrypt before storage, and are
  NEVER read back out or displayed anywhere (not even to the admin
  who set them).
- State-changing actions (create user, activate/deactivate) require
  a CSRF token that's tied to the admin's own session (see
  utils/csrf.py). This stops a malicious external site from tricking
  a logged-in admin's browser into submitting these forms without
  their knowledge (Cross-Site Request Forgery).
- An admin cannot deactivate their OWN account (prevents accidental
  self-lockout with no other admin able to fix it).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from config.database import get_db_connection
from utils.auth_helpers import role_required
from utils.csrf import generate_csrf_token, validate_csrf_token
import utils.medicine_helpers as med
import bcrypt
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

VALID_STAFF_ROLES = {'pharmacist', 'delivery', 'admin'}


def is_valid_password(password):
    """
    Minimum password strength check for staff accounts (admin, pharmacist,
    delivery manager) - these accounts can access sensitive data, so we
    hold them to a slightly higher bar than the customer signup form.
    Requires at least 8 characters. Kept simple on purpose - this is a
    university project, not a bank, but "at least something" is better
    than no check at all.
    """
    return len(password) >= 8


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    """
    Admin Dashboard - key metrics at a glance: total sales, active
    users, pending orders, plus a weekly revenue chart, top-selling
    medicines, and a real recent-activity feed built from actual
    orders/signups/stock data (not fake placeholder rows).
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return render_template('admin/admin_dashboard.html', stats={}, revenue_chart=[], top_medicines=[], recent_activity=[])

    try:
        cursor = connection.cursor(dictionary=True)

        # ---- Top stat cards ----
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders WHERE status != 'cancelled'")
        total_sales = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = TRUE")
        active_users = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM orders WHERE status = 'placed'")
        pending_orders = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) AS total FROM medicine_variants WHERE stock_qty <= 20
        """)
        low_stock_count = cursor.fetchone()['total']

        stats = {
            'total_sales': total_sales,
            'active_users': active_users,
            'pending_orders': pending_orders,
            'low_stock_count': low_stock_count,
        }

        # ---- Revenue trend: last 7 days ----
        cursor.execute("""
            SELECT DATE(created_at) AS day, COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) AND status != 'cancelled'
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """)
        revenue_by_day = {str(row['day']): float(row['revenue']) for row in cursor.fetchall()}
        # Fill in every day of the last 7 (even ones with zero orders) so the
        # chart always has exactly 7 points, not just the days with sales
        from datetime import date, timedelta
        revenue_chart = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            revenue_chart.append({'label': d.strftime('%a'), 'value': revenue_by_day.get(str(d), 0)})

        # ---- Top 5 medicines by units sold ----
        cursor.execute("""
            SELECT m.name, SUM(oi.quantity) AS units_sold
            FROM order_items oi
            JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            GROUP BY m.medicine_id, m.name
            ORDER BY units_sold DESC
            LIMIT 5
        """)
        top_medicines_raw = cursor.fetchall()
        max_units = max([m['units_sold'] for m in top_medicines_raw], default=1)
        top_medicines = [
            {'name': m['name'], 'units_sold': m['units_sold'], 'pct': round(m['units_sold'] / max_units * 100)}
            for m in top_medicines_raw
        ]

        # ---- Recent activity feed (real data: newest orders + newest signups) ----
        cursor.execute("""
            SELECT 'order' AS event_type, o.order_id AS ref_id, SUBSTRING_INDEX(o.delivery_address, ',', 1) AS person,
                   o.total_amount AS amount, o.status, o.created_at
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            ORDER BY o.created_at DESC LIMIT 5
        """)
        recent_orders = cursor.fetchall()

        cursor.execute("""
            SELECT full_name, role, created_at FROM users
            ORDER BY created_at DESC LIMIT 5
        """)
        recent_signups = cursor.fetchall()

        recent_activity = []
        for o in recent_orders:
            recent_activity.append({
                'type': 'New Order', 'icon': 'shopping_cart',
                'person': o['person'], 'detail': f"Order #{o['ref_id']} (Rs. {o['amount']:.0f})",
                'status': o['status'], 'time': o['created_at']
            })
        for s in recent_signups:
            recent_activity.append({
                'type': 'User Signup', 'icon': 'person_add',
                'person': s['full_name'], 'detail': f"New {s['role']} account",
                'status': 'active', 'time': s['created_at']
            })
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        recent_activity = recent_activity[:6]

        cursor.close()
        return render_template('admin/admin_dashboard.html', stats=stats, revenue_chart=revenue_chart,
                                top_medicines=top_medicines, recent_activity=recent_activity)

    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Something went wrong loading the dashboard.', 'error')
        return render_template('admin/admin_dashboard.html', stats={}, revenue_chart=[], top_medicines=[], recent_activity=[])

    finally:
        connection.close()


@admin_bp.route('/users')
@role_required('admin')
def user_list():
    """
    User Management - lists every account on the platform with role,
    status, and join date. Supports filtering by role and searching
    by name/email.
    """
    role_filter = request.args.get('role', default='all')
    search_query = request.args.get('search', default='', type=str).strip()

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return render_template('admin/users.html', users=[], stats={}, role_filter=role_filter,
                                search_query=search_query, csrf_token=generate_csrf_token())

    try:
        cursor = connection.cursor(dictionary=True)

        page = request.args.get('page', 1, type=int)
        per_page = 50

        where_clause = " WHERE 1=1"
        params = []

        if role_filter != 'all':
            where_clause += " AND role = %s"
            params.append(role_filter)

        if search_query:
            where_clause += " AND (full_name LIKE %s OR email LIKE %s)"
            like_term = f"%{search_query}%"
            params.extend([like_term, like_term])

        # Get total count for pagination
        count_query = f"SELECT COUNT(*) AS total FROM users {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page

        # Get the actual page data
        query = f"SELECT user_id, full_name, email, role, is_active, created_at FROM users {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [per_page, start_idx])
        users = cursor.fetchall()

        # Stat cards at the bottom of the page
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='pharmacist'")
        total_pharmacists = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='delivery'")
        total_delivery = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = FALSE")
        total_inactive = cursor.fetchone()['total']

        stats = {
            'total_users': total_users,
            'total_pharmacists': total_pharmacists,
            'total_delivery': total_delivery,
            'total_inactive': total_inactive,
        }

        cursor.close()
        return render_template('admin/users.html', users=users, stats=stats, role_filter=role_filter,
                                search_query=search_query, csrf_token=generate_csrf_token(),
                                page=page, total_pages=total_pages)

    except Exception as e:
        print(f"User list error: {e}")
        flash('Something went wrong loading users.', 'error')
        return render_template('admin/users.html', users=[], stats={}, role_filter=role_filter,
                                search_query=search_query, csrf_token=generate_csrf_token())

    finally:
        connection.close()


@admin_bp.route('/users/<int:user_id>/reset_password', methods=['POST'])
@role_required('admin')
def reset_user_password(user_id):
    """
    Generates a new random temporary password for a user and flashes it
    to the admin so they can communicate it to the user securely.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Invalid session. Please try again.', 'error')
        return redirect(url_for('admin.user_list'))

    # Don't let admins easily reset their own passwords here (prevent accidental lockouts)
    if user_id == session.get('user_id'):
        flash('You cannot reset your own password from here.', 'error')
        return redirect(url_for('admin.user_list'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('admin.user_list'))

    try:
        import string
        import secrets
        import bcrypt

        # Generate an 8-character random password. Using `secrets` instead
        # of `random` here since this generates an actual account password -
        # `secrets` is Python's cryptographically-secure random module,
        # meant specifically for passwords/tokens/security-sensitive values
        # (unlike `random`, which is predictable enough for games/simulations
        # but not for anything security-related).
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        
        password_bytes = temp_password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

        cursor = connection.cursor()
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (hashed_password, user_id))
        
        if cursor.rowcount > 0:
            connection.commit()
            flash(f'Password reset successfully. The new temporary password is: {temp_password} (Please copy this now, it won\'t be shown again)', 'success')
        else:
            flash('User not found.', 'error')
            
        cursor.close()

    except Exception as e:
        connection.rollback()
        print(f"Password reset error: {e}")
        flash('Something went wrong resetting the password.', 'error')
    finally:
        connection.close()

    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/create', methods=['POST'])
@role_required('admin')
def create_user():
    """
    Creates a new STAFF account (pharmacist, delivery manager, or
    another admin). This is the "front door" for staff accounts -
    they deliberately cannot be created through the public signup
    form, only by an existing admin, here.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('admin.user_list'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')
    # Role-specific extra fields
    license_number = request.form.get('license_number', '').strip()
    branch = request.form.get('branch', '').strip()
    zone = request.form.get('zone', '').strip()

    if not full_name or not email or not password or role not in VALID_STAFF_ROLES:
        flash('Please fill in all required fields with a valid role.', 'error')
        return redirect(url_for('admin.user_list'))

    # Phone is required for Pharmacist/Delivery (real field staff who need
    # to be reachable for scheduling/coordination), but optional for Admin
    # (back-office role, less operationally critical to have on file)
    if role in ('pharmacist', 'delivery') and not phone:
        flash('Phone number is required for Pharmacist and Delivery accounts.', 'error')
        return redirect(url_for('admin.user_list'))

    if not is_valid_password(password):
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('admin.user_list'))

    if role == 'pharmacist' and not license_number:
        flash('License number is required for a pharmacist account.', 'error')
        return redirect(url_for('admin.user_list'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('admin.user_list'))

    try:
        cursor = connection.cursor(dictionary=True)

        # Email must be unique across the whole platform
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('admin.user_list'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO users (full_name, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, %s)",
            (full_name, email, hashed_password.decode('utf-8'), phone or None, role)
        )
        new_user_id = cursor.lastrowid

        if role == 'pharmacist':
            cursor.execute(
                "INSERT INTO pharmacists (user_id, license_number, branch) VALUES (%s, %s, %s)",
                (new_user_id, license_number, branch or None)
            )
        elif role == 'delivery':
            cursor.execute(
                "INSERT INTO delivery_managers (user_id, zone) VALUES (%s, %s)",
                (new_user_id, zone or None)
            )
        elif role == 'admin':
            cursor.execute(
                "INSERT INTO admins (user_id, permission_level) VALUES (%s, 'manager')",
                (new_user_id,)
            )

        connection.commit()
        cursor.close()
        flash(f'{role.capitalize()} account created for {full_name}.', 'success')
        return redirect(url_for('admin.user_list'))

    except Exception as e:
        connection.rollback()
        print(f"Create user error: {e}")
        flash('Something went wrong creating this account.', 'error')
        return redirect(url_for('admin.user_list'))

    finally:
        connection.close()


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id):
    """
    Activates or deactivates a user account (soft "ban", not a hard
    delete - we never destroy account/order history). An admin cannot
    deactivate their own account, to avoid accidentally locking
    themselves out with no other admin left to undo it.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('admin.user_list'))

    if user_id == session.get('user_id'):
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.user_list'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('admin.user_list'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT is_active, full_name FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            flash('User not found.', 'error')
            return redirect(url_for('admin.user_list'))

        new_status = not user['is_active']
        cursor.execute("UPDATE users SET is_active = %s WHERE user_id = %s", (new_status, user_id))
        connection.commit()
        cursor.close()

        flash(f"{user['full_name']} has been {'activated' if new_status else 'deactivated'}.", 'success')
        return redirect(url_for('admin.user_list'))

    except Exception as e:
        connection.rollback()
        print(f"Toggle user status error: {e}")
        flash('Something went wrong updating this account.', 'error')
        return redirect(url_for('admin.user_list'))

    finally:
        connection.close()


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    """
    Permanently deletes a user account. Unlike toggle_user_status
    (which just deactivates - reversible, keeps history), this is
    irreversible, so it should be used sparingly - e.g. removing a
    mistakenly-created staff account, not a real customer with order
    history.

    SAFETY:
    - An admin cannot delete their own account (same protection as
      the self-deactivation block).
    - The database itself protects order history: the orders table's
      foreign key to customers does NOT cascade-delete, so MySQL will
      refuse this operation if the account is a customer who has ever
      placed an order. We catch that specific database error and show
      a clear, friendly explanation instead of a raw SQL error message.
    - Pharmacist/Delivery/Admin accounts, and customers who never
      placed an order, delete cleanly (their role-specific rows in
      pharmacists/delivery_managers/admins/customers all cascade).
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('admin.user_list'))

    if user_id == session.get('user_id'):
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.user_list'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('admin.user_list'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT full_name, role FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            flash('User not found.', 'error')
            return redirect(url_for('admin.user_list'))

        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        connection.commit()
        cursor.close()

        flash(f"{user['full_name']}'s account has been permanently deleted.", 'success')
        return redirect(url_for('admin.user_list'))

    except Exception as e:
        connection.rollback()
        error_text = str(e).lower()
        # MySQL error 1451: "Cannot delete or update a parent row: a
        # foreign key constraint fails" - happens specifically when this
        # customer has order history (orders.customer_id references them
        # without cascade). This is a GOOD thing - it protects sales
        # records - so we explain it clearly instead of showing raw SQL.
        if 'foreign key constraint' in error_text or '1451' in error_text:
            flash(f"{user['full_name']} has order history and can't be deleted (this protects sales records). Deactivate the account instead.", 'error')
        else:
            print(f"Delete user error: {e}")
            flash('Something went wrong deleting this account.', 'error')
        return redirect(url_for('admin.user_list'))

    finally:
        connection.close()


@admin_bp.route('/reports')
@role_required('admin')
def sales_reports():
    """
    Sales & Revenue Reports - revenue trend over the last 30 days,
    sales split by category, and a detailed transaction log.
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return render_template('admin/reports.html', stats={}, revenue_chart=[], category_split=[], transactions=[])

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS total, COUNT(*) AS cnt FROM orders WHERE status != 'cancelled'")
        row = cursor.fetchone()
        total_revenue = float(row['total'])
        total_orders = row['cnt']
        avg_order_value = (total_revenue / total_orders) if total_orders else 0

        stats = {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
        }

        # ---- Revenue trend: last 30 days ----
        cursor.execute("""
            SELECT DATE(created_at) AS day, COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 29 DAY) AND status != 'cancelled'
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """)
        revenue_by_day = {str(r['day']): float(r['revenue']) for r in cursor.fetchall()}
        from datetime import date, timedelta
        revenue_chart = []
        for i in range(29, -1, -1):
            d = date.today() - timedelta(days=i)
            revenue_chart.append({'label': d.strftime('%b %d'), 'value': revenue_by_day.get(str(d), 0)})

        # ---- Sales split by category ----
        cursor.execute("""
            SELECT c.name, COALESCE(SUM(oi.quantity * oi.price_at_purchase), 0) AS revenue
            FROM order_items oi
            JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            JOIN categories c ON m.category_id = c.category_id
            GROUP BY c.category_id, c.name
            ORDER BY revenue DESC
        """)
        category_split = cursor.fetchall()

        # ---- Detailed transaction log (most recent 20 orders) ----
        cursor.execute("""
            SELECT o.order_id, o.created_at, SUBSTRING_INDEX(o.delivery_address, ',', 1) AS customer_name,
                   o.total_amount, o.status
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            ORDER BY o.created_at DESC
            LIMIT 20
        """)
        transactions = cursor.fetchall()

        cursor.close()
        return render_template('admin/reports.html', stats=stats, revenue_chart=revenue_chart,
                                category_split=category_split, transactions=transactions)

    except Exception as e:
        print(f"Sales reports error: {e}")
        flash('Something went wrong loading reports.', 'error')
        return render_template('admin/reports.html', stats={}, revenue_chart=[], category_split=[], transactions=[])

    finally:
        connection.close()


@admin_bp.route('/reports/export-csv')
@role_required('admin')
def export_sales_csv():
    """
    Generates and downloads a CSV file of all orders (transaction log)
    for accounting/bookkeeping. The CSV is generated on-the-fly using
    a Python generator so it doesn't load the entire result set into
    memory at once.
    """
    import csv
    import io
    from datetime import datetime

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('admin.sales_reports'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.order_id, o.created_at, SUBSTRING_INDEX(o.delivery_address, ',', 1) AS customer_name,
                   o.total_amount, o.status, o.payment_method, o.delivery_address,
                   GROUP_CONCAT(CONCAT(m.name, ' x', oi.quantity) SEPARATOR ' | ') AS items
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            LEFT JOIN medicines m ON mv.medicine_id = m.medicine_id
            GROUP BY o.order_id, o.created_at, customer_name, o.total_amount, o.status, o.payment_method, o.delivery_address
            ORDER BY o.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Order ID', 'Date', 'Customer', 'Amount (Rs.)', 'Status', 'Payment Method', 'Delivery Address', 'Items'])

        for row in rows:
            writer.writerow([
                f'SH-{row["order_id"]:04d}',
                row['created_at'].strftime('%Y-%m-%d %H:%M'),
                row['customer_name'],
                f'{row["total_amount"]:.2f}',
                row['status'],
                row['payment_method'] or 'N/A',
                row['delivery_address'],
                row['items'] or 'N/A',
            ])

        csv_content = output.getvalue()
        output.close()

        filename = f'SehatHub_Sales_Report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        print(f"CSV export error: {e}")
        flash('Something went wrong exporting the report.', 'error')
        return redirect(url_for('admin.sales_reports'))

    finally:
        connection.close()

# ============================================================
# MEDICINE MANAGEMENT
# Shared logic lives in utils/medicine_helpers.py - the Pharmacist
# Module has its own copy of these routes (routes/pharmacist.py)
# pointing at the same helper functions, so both roles can manage
# the catalog without duplicating the underlying database logic.
# ============================================================

@admin_bp.route('/medicines')
@role_required('admin')
def medicine_list():
    search = request.args.get('search', default='', type=str).strip()
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', default='active')
    page = request.args.get('page', 1, type=int)

    medicines, total_pages = med.get_medicines_list(search=search, category_id=category_id, status=status, page=page)
    categories = med.get_categories()

    return render_template('admin/medicines.html', medicines=medicines, categories=categories,
                            search=search, category_id=category_id, status=status,
                            page=page, total_pages=total_pages,
                            csrf_token=generate_csrf_token())


@admin_bp.route('/medicines/new', methods=['GET', 'POST'])
@role_required('admin')
def medicine_new():
    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return redirect(url_for('admin.medicine_list'))

        data = {
            'name': request.form.get('name', '').strip(),
            'generic_name': request.form.get('generic_name', '').strip(),
            'category_id': request.form.get('category_id', type=int),
            'brand_id': request.form.get('brand_id', type=int),
            'type': request.form.get('type', 'OTC'),
            'description': request.form.get('description', '').strip(),
            'usage_info': request.form.get('usage_info', '').strip(),
            'side_effects': request.form.get('side_effects', '').strip(),
            'pack_size': request.form.get('pack_size', '').strip(),
            'price': request.form.get('price', type=float),
            'stock_qty': request.form.get('stock_qty', type=int, default=0),
        }

        # If a new company name was typed in (instead of picking an
        # existing one from the dropdown), create it on the spot and
        # use its new brand_id - lets staff add medicines from a
        # manufacturer that isn't in the system yet without needing
        # to run a separate SQL query first.
        new_brand_name = request.form.get('new_brand_name', '').strip()
        if new_brand_name:
            data['brand_id'] = med.get_or_create_brand(new_brand_name)

        if not data['name'] or not data['pack_size'] or not data['price']:
            flash('Name, pack size, and price are required.', 'error')
            return redirect(url_for('admin.medicine_new'))

        image_file = request.files.get('image')
        new_id, error = med.create_medicine(data, image_file)

        if error:
            flash(error, 'error')
            return redirect(url_for('admin.medicine_new'))

        flash(f"{data['name']} was added to the catalog.", 'success')
        return redirect(url_for('admin.medicine_list'))

    categories = med.get_categories()
    brands = med.get_brands()
    return render_template('admin/medicine_form.html', medicine=None, variants=[],
                            categories=categories, brands=brands, csrf_token=generate_csrf_token())


@admin_bp.route('/medicines/<int:medicine_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def medicine_edit(medicine_id):
    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))

        data = {
            'name': request.form.get('name', '').strip(),
            'generic_name': request.form.get('generic_name', '').strip(),
            'category_id': request.form.get('category_id', type=int),
            'brand_id': request.form.get('brand_id', type=int),
            'type': request.form.get('type', 'OTC'),
            'description': request.form.get('description', '').strip(),
            'usage_info': request.form.get('usage_info', '').strip(),
            'side_effects': request.form.get('side_effects', '').strip(),
        }

        new_brand_name = request.form.get('new_brand_name', '').strip()
        if new_brand_name:
            data['brand_id'] = med.get_or_create_brand(new_brand_name)

        if not data['name']:
            flash('Name is required.', 'error')
            return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))

        image_file = request.files.get('image')
        error = med.update_medicine(medicine_id, data, image_file)

        if error:
            flash(error, 'error')
        else:
            flash(f"{data['name']} was updated.", 'success')

        return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))

    medicine, variants = med.get_medicine_detail(medicine_id)
    if not medicine:
        flash('Medicine not found.', 'error')
        return redirect(url_for('admin.medicine_list'))

    categories = med.get_categories()
    brands = med.get_brands()
    return render_template('admin/medicine_form.html', medicine=medicine, variants=variants,
                            categories=categories, brands=brands, csrf_token=generate_csrf_token())


@admin_bp.route('/medicines/<int:medicine_id>/toggle-status', methods=['POST'])
@role_required('admin')
def medicine_toggle_status(medicine_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('admin.medicine_list'))

    medicine, _ = med.get_medicine_detail(medicine_id)
    if not medicine:
        flash('Medicine not found.', 'error')
        return redirect(url_for('admin.medicine_list'))

    error = med.set_medicine_active(medicine_id, not medicine['is_active'])
    if error:
        flash(error, 'error')
    else:
        action = 'deactivated' if medicine['is_active'] else 'reactivated'
        flash(f"{medicine['name']} was {action}.", 'success')

    return redirect(url_for('admin.medicine_list'))


@admin_bp.route('/medicines/<int:medicine_id>/variants/add', methods=['POST'])
@role_required('admin')
def medicine_variant_add(medicine_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))

    pack_size = request.form.get('pack_size', '').strip()
    price = request.form.get('price', type=float)
    stock_qty = request.form.get('stock_qty', type=int, default=0)

    if not pack_size or not price:
        flash('Pack size and price are required.', 'error')
    else:
        error = med.add_variant(medicine_id, pack_size, price, stock_qty)
        if error:
            flash(error, 'error')
        else:
            flash('Pack size added.', 'success')

    return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))


@admin_bp.route('/medicines/variants/<int:variant_id>/update', methods=['POST'])
@role_required('admin')
def medicine_variant_update(variant_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(request.referrer or url_for('admin.medicine_list'))

    medicine_id = request.form.get('medicine_id', type=int)
    pack_size = request.form.get('pack_size', '').strip()
    price = request.form.get('price', type=float)
    stock_qty = request.form.get('stock_qty', type=int, default=0)

    error = med.update_variant(variant_id, pack_size, price, stock_qty)
    flash(error if error else 'Pack size updated.', 'error' if error else 'success')

    return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))


@admin_bp.route('/medicines/variants/<int:variant_id>/delete', methods=['POST'])
@role_required('admin')
def medicine_variant_delete(variant_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(request.referrer or url_for('admin.medicine_list'))

    medicine_id = request.form.get('medicine_id', type=int)
    error = med.delete_variant(variant_id)
    flash(error if error else 'Pack size removed.', 'error' if error else 'success')

    return redirect(url_for('admin.medicine_edit', medicine_id=medicine_id))


@admin_bp.route('/api/notifications')
@role_required('admin')
def api_notifications():
    """
    Polling endpoint for Admin dashboard notifications.
    Returns counts of total users and total orders so the client
    can diff them and show "New user registered!" or "New order placed!"
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database error'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()['total_users']

        cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
        total_orders = cursor.fetchone()['total_orders']

        cursor.close()
        return jsonify({
            'total_users': total_users,
            'total_orders': total_orders
        })
    except Exception as e:
        print(f"Admin notifications API error: {e}")
        return jsonify({'error': 'Server error'}), 500
    finally:
        connection.close()