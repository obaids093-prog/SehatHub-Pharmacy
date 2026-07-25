"""
SehatHub - Pharmacist Routes
Dashboard, prescription verification, and stock management for
pharmacist staff accounts (not self-registerable - created by an
Admin, or seeded directly via SQL for testing).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
from config.database import get_db_connection
from utils.auth_helpers import role_required
from utils.csrf import generate_csrf_token, validate_csrf_token
import utils.medicine_helpers as med
import os

pharmacist_bp = Blueprint('pharmacist', __name__, url_prefix='/pharmacist')

# A variant with stock at or below this number shows up as a "low stock" alert
LOW_STOCK_THRESHOLD = 20


@pharmacist_bp.route('/uploads/prescriptions/<path:filename>')
@role_required('pharmacist')
def serve_prescription_image(filename):
    """
    Serves an uploaded prescription image/PDF to a logged-in pharmacist.

    WHY this route exists: prescription files are saved under
    uploads/prescriptions/ (NOT under static/), so Flask does not serve
    them automatically the way it does for static/images/. Without this
    route, the pharmacist verification page could never actually show
    the prescription image - which defeats the entire point of
    "verification" (a pharmacist can't approve/reject something they
    can't see).

    WHY it's @role_required('pharmacist') and not just a plain static
    file: these are patients' private medical documents. A customer
    (or anyone with a guessed URL) must NOT be able to view another
    patient's prescription just by knowing/guessing the filename.
    """
    uploads_folder = os.path.join(os.getcwd(), 'uploads', 'prescriptions')
    return send_from_directory(uploads_folder, filename)


@pharmacist_bp.route('/dashboard')
@role_required('pharmacist')
def dashboard():
    """
    Overview page: key stats, recent pending prescriptions needing
    verification, low-stock alerts, and orders ready to be packed.
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return render_template('pharmacist/pharmacist_dashboard.html', stats={}, prescriptions=[],
                                low_stock_items=[], orders_to_fulfill=[])

    try:
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------------
        # STATS CARDS
        # ----------------------------------------------------------
        cursor.execute("SELECT COUNT(*) AS count FROM prescriptions WHERE status = 'pending'")
        pending_verifications = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE DATE(created_at) = CURDATE()")
        new_orders_today = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM medicine_variants WHERE stock_qty <= %s", (LOW_STOCK_THRESHOLD,))
        low_stock_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM prescriptions WHERE status IN ('approved', 'rejected')")
        completed_reviews = cursor.fetchone()['count']

        stats = {
            'pending_verifications': pending_verifications,
            'new_orders_today': new_orders_today,
            'low_stock_count': low_stock_count,
            'completed_reviews': completed_reviews,
        }

        # ----------------------------------------------------------
        # PRESCRIPTION VERIFICATION (most recent 5 pending)
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT p.prescription_id, p.image_path, p.status, p.uploaded_at, u.full_name AS patient_name,
                   GROUP_CONCAT(CONCAT(m.name, ' (x', oi.quantity, ')') SEPARATOR ', ') AS requested_medicines
            FROM prescriptions p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON p.order_id = oi.order_id
            LEFT JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            LEFT JOIN medicines m ON mv.medicine_id = m.medicine_id
            WHERE p.status = 'pending'
            GROUP BY p.prescription_id, p.image_path, p.status, p.uploaded_at, u.full_name
            ORDER BY p.uploaded_at ASC
            LIMIT 5
        """)
        prescriptions = cursor.fetchall()

        # ----------------------------------------------------------
        # INVENTORY ALERTS (lowest-stock items first)
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT mv.variant_id, mv.pack_size, mv.stock_qty, m.name AS medicine_name
            FROM medicine_variants mv
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            WHERE mv.stock_qty <= %s
            ORDER BY mv.stock_qty ASC
            LIMIT 5
        """, (LOW_STOCK_THRESHOLD,))
        low_stock_items = cursor.fetchall()

        # ----------------------------------------------------------
        # ORDER FULFILLMENT (orders placed/confirmed, ready to pack)
        # GROUP_CONCAT pulls all medicine names for the order into one
        # comma-separated string (e.g. "Panadol 500mg, Brufen 400mg")
        # so the pharmacist can see WHAT they're packing at a glance,
        # not just a bare item count.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                o.order_id, o.status, o.total_amount, o.created_at,
                u.full_name AS customer_name,
                COUNT(oi.order_item_id) AS item_count,
                GROUP_CONCAT(CONCAT(m.name, ' (x', oi.quantity, ')') SEPARATOR ', ') AS item_names
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            LEFT JOIN medicines m ON mv.medicine_id = m.medicine_id
            WHERE o.status IN ('placed', 'confirmed')
            GROUP BY o.order_id, o.status, o.total_amount, o.created_at, u.full_name
            ORDER BY o.created_at ASC
            LIMIT 6
        """)
        orders_to_fulfill = cursor.fetchall()

        cursor.close()

        return render_template(
            'pharmacist/pharmacist_dashboard.html',
            stats=stats,
            prescriptions=prescriptions,
            low_stock_items=low_stock_items,
            orders_to_fulfill=orders_to_fulfill
        )

    finally:
        connection.close()


@pharmacist_bp.route('/prescriptions')
@role_required('pharmacist')
def prescription_list():
    """
    Full list of ALL prescriptions (not just the top 5 pending shown
    on the dashboard), so the pharmacist can review the complete queue.
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    try:
        cursor = connection.cursor(dictionary=True)
        page = request.args.get('page', 1, type=int)
        per_page = 20

        # Get total count for pagination
        cursor.execute("SELECT COUNT(*) AS total FROM prescriptions")
        total_count = cursor.fetchone()['total']

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page

        cursor.execute("""
            SELECT p.prescription_id, p.image_path, p.status, p.uploaded_at, p.rejection_reason,
                   u.full_name AS patient_name, u.phone AS patient_phone,
                   GROUP_CONCAT(CONCAT(m.name, ' (x', oi.quantity, ')') SEPARATOR ', ') AS requested_medicines
            FROM prescriptions p
            JOIN customers c ON p.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON p.order_id = oi.order_id
            LEFT JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            LEFT JOIN medicines m ON mv.medicine_id = m.medicine_id
            GROUP BY p.prescription_id, p.image_path, p.status, p.uploaded_at, p.rejection_reason, u.full_name, u.phone
            ORDER BY
                CASE p.status WHEN 'pending' THEN 0 ELSE 1 END,
                p.uploaded_at ASC
            LIMIT %s OFFSET %s
        """, (per_page, start_idx))
        prescriptions = cursor.fetchall()
        cursor.close()

        return render_template('pharmacist/prescriptions.html', prescriptions=prescriptions,
                               page=page, total_pages=total_pages)

    finally:
        connection.close()


@pharmacist_bp.route('/prescriptions/<int:prescription_id>/verify', methods=['POST'])
@role_required('pharmacist')
def verify_prescription(prescription_id):
    """
    Approves or rejects a prescription. Called from a small form with
    a hidden 'decision' field set to either 'approved' or 'rejected'.
    When rejecting, a 'reason' field is also required - this gets
    stored so the customer (and any pharmacist reviewing history
    later) can see WHY it was rejected, instead of just a bare
    status change with no explanation.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.prescription_list'))

    decision = request.form.get('decision')
    reason = request.form.get('reason', '').strip()

    if decision not in ('approved', 'rejected'):
        flash('Invalid decision.', 'error')
        return redirect(url_for('pharmacist.prescription_list'))

    if decision == 'rejected' and not reason:
        flash('Please provide a reason for rejecting this prescription.', 'error')
        return redirect(url_for('pharmacist.prescription_list'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.prescription_list'))

    try:
        cursor = connection.cursor(dictionary=True)
        # Fetch user_id for the notification
        cursor.execute("""
            SELECT c.user_id 
            FROM prescriptions p 
            JOIN customers c ON p.customer_id = c.customer_id 
            WHERE p.prescription_id = %s
        """, (prescription_id,))
        user_row = cursor.fetchone()
        user_id = user_row['user_id'] if user_row else None

        cursor.execute(
            "UPDATE prescriptions SET status = %s, rejection_reason = %s, customer_seen = FALSE WHERE prescription_id = %s",
            (decision, reason if decision == 'rejected' else None, prescription_id)
        )

        if user_id:
            if decision == 'approved':
                title = f"Prescription #{prescription_id} Approved ✅"
                msg = "Your prescription has been verified. You can now order the prescribed medicines."
                ntype = 'prescription_approved'
                icon = 'task_alt'
            else:
                title = f"Prescription #{prescription_id} Rejected"
                msg = f"Reason: {reason}"
                ntype = 'prescription_rejected'
                icon = 'error'
                
            cursor.execute("""
                INSERT INTO notifications (user_id, type, title, message, link, icon, is_read)
                VALUES (%s, %s, %s, %s, '/customer/prescriptions', %s, FALSE)
            """, (user_id, ntype, title, msg, icon))

        connection.commit()
        cursor.close()

        flash(f'Prescription #{prescription_id} marked as {decision}.', 'success')
        return redirect(url_for('pharmacist.prescription_list'))

    except Exception as e:
        connection.rollback()
        print(f"Verify prescription error: {e}")
        flash('Something went wrong updating this prescription.', 'error')
        return redirect(url_for('pharmacist.prescription_list'))

    finally:
        connection.close()


@pharmacist_bp.route('/orders/<int:order_id>/pack', methods=['POST'])
@role_required('pharmacist')
def pack_order(order_id):
    """
    Advances an order's status: placed -> confirmed -> packed.
    Keeping this as a single "next stage" action (rather than a
    dropdown of every possible status) matches the dashboard's
    simple "Pack Order" button design.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('pharmacist.dashboard'))

        # Simple one-step progression for the "Pack Order" button
        next_status = 'confirmed' if order['status'] == 'placed' else 'packed'

        cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (next_status, order_id))

        # Insert notification for the customer
        cursor.execute("""
            SELECT c.user_id 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.customer_id 
            WHERE o.order_id = %s
        """, (order_id,))
        user_row = cursor.fetchone()
        if user_row:
            if next_status == 'packed':
                title = f"Order #{str(order_id).zfill(4)} Packed 📦"
                msg = "Your order has been packed by our pharmacist and is waiting for delivery."
                icon = 'inventory_2'
            else:
                title = f"Order #{str(order_id).zfill(4)} Confirmed"
                msg = "Your order has been confirmed and is currently being prepared."
                icon = 'fact_check'
                
            cursor.execute("""
                INSERT INTO notifications (user_id, type, title, message, link, icon, is_read)
                VALUES (%s, 'order_update', %s, %s, '/customer/orders', %s, FALSE)
            """, (user_row['user_id'], title, msg, icon))

        connection.commit()
        cursor.close()

        flash(f'Order #{order_id} marked as {next_status}.', 'success')
        return redirect(url_for('pharmacist.dashboard'))

    except Exception as e:
        connection.rollback()
        print(f"Pack order error: {e}")
        flash('Something went wrong updating this order.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    finally:
        connection.close()


@pharmacist_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@role_required('pharmacist')
def cancel_order(order_id):
    """
    Cancels an order that hasn't been packed yet. Only allowed while
    status is 'placed' or 'confirmed' - once it's been packed, physical
    medicines have already been pulled and boxed, so cancelling at that
    point needs a different (manual/offline) process, not a button click.

    A reason is required (same pattern as prescription rejection) so
    the customer knows WHY, and stock is added back to each variant
    since it was deducted when the order was originally placed.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    reason = request.form.get('reason', '').strip()
    if not reason:
        flash('Please provide a reason for cancelling this order.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('pharmacist.dashboard'))

        if order['status'] not in ('placed', 'confirmed'):
            cursor.close()
            flash(f"Order #{order_id} can't be cancelled - it's already been packed.", 'error')
            return redirect(url_for('pharmacist.dashboard'))

        # Give the stock back - it was deducted when the customer
        # originally placed the order (see customer.checkout)
        cursor.execute("SELECT variant_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute(
                "UPDATE medicine_variants SET stock_qty = stock_qty + %s WHERE variant_id = %s",
                (item['quantity'], item['variant_id'])
            )

        cursor.execute(
            "UPDATE orders SET status = 'cancelled', cancellation_reason = %s WHERE order_id = %s",
            (reason, order_id)
        )

        # Insert notification for the customer
        cursor.execute("""
            SELECT c.user_id 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.customer_id 
            WHERE o.order_id = %s
        """, (order_id,))
        user_row = cursor.fetchone()
        if user_row:
            title = f"Order #{str(order_id).zfill(4)} Cancelled ❌"
            msg = f"Your order was cancelled by the pharmacist. Reason: {reason}"
            cursor.execute("""
                INSERT INTO notifications (user_id, type, title, message, link, icon, is_read)
                VALUES (%s, 'order_update', %s, %s, '/customer/orders', 'cancel', FALSE)
            """, (user_row['user_id'], title, msg))

        connection.commit()
        cursor.close()

        flash(f'Order #{order_id} has been cancelled and stock restored.', 'success')
        return redirect(url_for('pharmacist.dashboard'))

    except Exception as e:
        connection.rollback()
        print(f"Cancel order error: {e}")
        flash('Something went wrong cancelling this order.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    finally:
        connection.close()


@pharmacist_bp.route('/inventory')
@role_required('pharmacist')
def inventory():
    """
    Full stock management page - lists every medicine variant with
    its current stock level, lowest-stock items first, with a quick
    inline form to update stock quantity.
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.dashboard'))

    try:
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        cursor = connection.cursor(dictionary=True)
        
        # Base query components
        where_clause = ""
        params = []
        
        if search_query:
            where_clause = "WHERE m.name LIKE %s OR b.name LIKE %s"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
            
        # Get total count for pagination
        cursor.execute(f"""
            SELECT COUNT(*) AS total
            FROM medicine_variants mv
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            {where_clause}
        """, tuple(params))
        total_items = cursor.fetchone()['total']
        total_pages = (total_items + per_page - 1) // per_page
        
        # Fetch actual data
        query = f"""
            SELECT mv.variant_id, mv.pack_size, mv.stock_qty, mv.price,
                   m.name AS medicine_name, b.name AS brand_name
            FROM medicine_variants mv
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            {where_clause}
            ORDER BY mv.stock_qty ASC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        
        cursor.execute(query, tuple(params))
        variants = cursor.fetchall()
        cursor.close()

        return render_template('pharmacist/inventory.html', 
                               variants=variants, 
                               low_stock_threshold=LOW_STOCK_THRESHOLD,
                               search_query=search_query,
                               page=page,
                               total_pages=total_pages)

    finally:
        connection.close()


@pharmacist_bp.route('/inventory/<int:variant_id>/update', methods=['POST'])
@role_required('pharmacist')
def update_stock(variant_id):
    """
    Updates the stock quantity for a single medicine variant.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.inventory'))

    new_stock = request.form.get('stock_qty', type=int)

    if new_stock is None or new_stock < 0:
        flash('Please enter a valid stock quantity.', 'error')
        return redirect(url_for('pharmacist.inventory'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('pharmacist.inventory'))

    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE medicine_variants SET stock_qty = %s WHERE variant_id = %s",
            (new_stock, variant_id)
        )
        connection.commit()
        cursor.close()

        flash('Stock updated successfully.', 'success')
        return redirect(url_for('pharmacist.inventory'))

    except Exception as e:
        connection.rollback()
        print(f"Update stock error: {e}")
        flash('Something went wrong updating stock.', 'error')
        return redirect(url_for('pharmacist.inventory'))

    finally:
        connection.close()


# ============================================================
# MEDICINE MANAGEMENT
# Shared logic lives in utils/medicine_helpers.py - the Admin
# Module has its own copy of these routes (routes/admin.py)
# pointing at the same helper functions, so both roles can manage
# the catalog without duplicating the underlying database logic.
# ============================================================

@pharmacist_bp.route('/medicines')
@role_required('pharmacist')
def medicine_list():
    search = request.args.get('search', default='', type=str).strip()
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', default='active')
    page = request.args.get('page', 1, type=int)

    medicines, total_pages = med.get_medicines_list(search=search, category_id=category_id, status=status, page=page)
    categories = med.get_categories()

    return render_template('pharmacist/medicines.html', medicines=medicines, categories=categories,
                            search=search, category_id=category_id, status=status,
                            page=page, total_pages=total_pages,
                            csrf_token=generate_csrf_token())


@pharmacist_bp.route('/medicines/new', methods=['GET', 'POST'])
@role_required('pharmacist')
def medicine_new():
    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return redirect(url_for('pharmacist.medicine_list'))

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

        if not data['name'] or not data['pack_size'] or not data['price']:
            flash('Name, pack size, and price are required.', 'error')
            return redirect(url_for('pharmacist.medicine_new'))

        image_file = request.files.get('image')
        new_id, error = med.create_medicine(data, image_file)

        if error:
            flash(error, 'error')
            return redirect(url_for('pharmacist.medicine_new'))

        flash(f"{data['name']} was added to the catalog.", 'success')
        return redirect(url_for('pharmacist.medicine_list'))

    categories = med.get_categories()
    brands = med.get_brands()
    return render_template('pharmacist/medicine_form.html', medicine=None, variants=[],
                            categories=categories, brands=brands, csrf_token=generate_csrf_token())


@pharmacist_bp.route('/medicines/<int:medicine_id>/edit', methods=['GET', 'POST'])
@role_required('pharmacist')
def medicine_edit(medicine_id):
    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))

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

        if not data['name']:
            flash('Name is required.', 'error')
            return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))

        image_file = request.files.get('image')
        error = med.update_medicine(medicine_id, data, image_file)

        if error:
            flash(error, 'error')
        else:
            flash(f"{data['name']} was updated.", 'success')

        return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))

    medicine, variants = med.get_medicine_detail(medicine_id)
    if not medicine:
        flash('Medicine not found.', 'error')
        return redirect(url_for('pharmacist.medicine_list'))

    categories = med.get_categories()
    brands = med.get_brands()
    return render_template('pharmacist/medicine_form.html', medicine=medicine, variants=variants,
                            categories=categories, brands=brands, csrf_token=generate_csrf_token())


@pharmacist_bp.route('/medicines/<int:medicine_id>/toggle-status', methods=['POST'])
@role_required('pharmacist')
def medicine_toggle_status(medicine_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.medicine_list'))

    medicine, _ = med.get_medicine_detail(medicine_id)
    if not medicine:
        flash('Medicine not found.', 'error')
        return redirect(url_for('pharmacist.medicine_list'))

    error = med.set_medicine_active(medicine_id, not medicine['is_active'])
    if error:
        flash(error, 'error')
    else:
        action = 'deactivated' if medicine['is_active'] else 'reactivated'
        flash(f"{medicine['name']} was {action}.", 'success')

    return redirect(url_for('pharmacist.medicine_list'))


@pharmacist_bp.route('/medicines/<int:medicine_id>/variants/add', methods=['POST'])
@role_required('pharmacist')
def medicine_variant_add(medicine_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))

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

    return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))


@pharmacist_bp.route('/medicines/variants/<int:variant_id>/update', methods=['POST'])
@role_required('pharmacist')
def medicine_variant_update(variant_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(request.referrer or url_for('pharmacist.medicine_list'))

    medicine_id = request.form.get('medicine_id', type=int)
    pack_size = request.form.get('pack_size', '').strip()
    price = request.form.get('price', type=float)
    stock_qty = request.form.get('stock_qty', type=int, default=0)

    error = med.update_variant(variant_id, pack_size, price, stock_qty)
    flash(error if error else 'Pack size updated.', 'error' if error else 'success')

    return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))


@pharmacist_bp.route('/medicines/variants/<int:variant_id>/delete', methods=['POST'])
@role_required('pharmacist')
def medicine_variant_delete(variant_id):
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(request.referrer or url_for('pharmacist.medicine_list'))

    medicine_id = request.form.get('medicine_id', type=int)
    error = med.delete_variant(variant_id)
    flash(error if error else 'Pack size removed.', 'error' if error else 'success')

    return redirect(url_for('pharmacist.medicine_edit', medicine_id=medicine_id))


# ============================================================
# REAL-TIME NOTIFICATIONS (polling)
# Same pattern as the customer notifications API - the navbar bell
# calls this every 30 seconds while a pharmacist is logged in, so
# a new prescription upload or a new order shows up on the bell
# without needing a manual refresh, even while browsing other
# pages like Inventory or Medicines (not just the Dashboard).
# ============================================================
@pharmacist_bp.route('/api/notifications')
@role_required('pharmacist')
def api_notifications():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'pending_prescriptions': 0, 'orders_to_pack': 0})

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS count FROM prescriptions WHERE status = 'pending'")
        pending_prescriptions = cursor.fetchone()['count'] or 0

        # "placed" (needs confirming) and "confirmed" (needs packing)
        # are both work waiting on the pharmacist's queue
        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status IN ('placed', 'confirmed')")
        orders_to_pack = cursor.fetchone()['count'] or 0

        return jsonify({'pending_prescriptions': pending_prescriptions, 'orders_to_pack': orders_to_pack})

    except Exception as e:
        print(f"Notifications API error: {e}")
        return jsonify({'pending_prescriptions': 0, 'orders_to_pack': 0})

    finally:
        connection.close()
