"""
SehatHub - Delivery Manager Routes
Dashboard for delivery staff: orders that are packed and ready to
ship, and orders currently out for delivery. Completes the order
lifecycle that the Pharmacist Module starts (placed -> confirmed ->
packed), taking it the rest of the way (packed -> shipped -> delivered).

Like pharmacists, delivery manager accounts are not self-registerable -
they're created by an Admin (Admin Module > User Management), or seeded
directly via SQL for initial testing (see seed_delivery_account.sql).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from config.database import get_db_connection
from utils.auth_helpers import role_required
from utils.csrf import validate_csrf_token

delivery_bp = Blueprint('delivery', __name__, url_prefix='/delivery')


@delivery_bp.route('/dashboard')
@role_required('delivery')
def dashboard():
    """
    Shows two lists: orders that are 'packed' (ready to be picked up
    and shipped) and orders that are 'shipped' (currently out, waiting
    to be marked delivered once they arrive).
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return render_template('delivery/dashboard.html', stats={}, ready_to_ship=[], out_for_delivery=[])

    try:
        cursor = connection.cursor(dictionary=True)

        # ---- Stat cards ----
        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'packed'")
        ready_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'shipped'")
        shipped_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'delivered' AND DATE(created_at) = CURDATE()")
        delivered_today = cursor.fetchone()['count']

        stats = {
            'ready_count': ready_count,
            'shipped_count': shipped_count,
            'delivered_today': delivered_today,
        }

        # ---- Orders ready to ship (status = 'packed') ----
        cursor.execute("""
            SELECT
                o.order_id, o.status, o.total_amount, o.delivery_address, o.created_at,
                SUBSTRING_INDEX(o.delivery_address, ',', 1) AS customer_name, SUBSTRING_INDEX(o.delivery_address, '| Phone: ', -1) AS customer_phone,
                COUNT(oi.order_item_id) AS item_count
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status = 'packed'
            GROUP BY o.order_id, o.status, o.total_amount, o.delivery_address, o.created_at, customer_name, customer_phone
            ORDER BY o.created_at ASC
        """)
        ready_to_ship = cursor.fetchall()

        # ---- Orders currently out for delivery (status = 'shipped') ----
        cursor.execute("""
            SELECT
                o.order_id, o.status, o.total_amount, o.delivery_address, o.created_at,
                SUBSTRING_INDEX(o.delivery_address, ',', 1) AS customer_name, SUBSTRING_INDEX(o.delivery_address, '| Phone: ', -1) AS customer_phone,
                COUNT(oi.order_item_id) AS item_count
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status = 'shipped'
            GROUP BY o.order_id, o.status, o.total_amount, o.delivery_address, o.created_at, customer_name, customer_phone
            ORDER BY o.created_at ASC
        """)
        out_for_delivery = cursor.fetchall()

        cursor.close()
        return render_template('delivery/dashboard.html', stats=stats,
                                ready_to_ship=ready_to_ship, out_for_delivery=out_for_delivery)

    except Exception as e:
        print(f"Delivery dashboard error: {e}")
        flash('Something went wrong loading the dashboard.', 'error')
        return render_template('delivery/dashboard.html', stats={}, ready_to_ship=[], out_for_delivery=[])

    finally:
        connection.close()


@delivery_bp.route('/orders/<int:order_id>/advance', methods=['POST'])
@role_required('delivery')
def advance_order(order_id):
    """
    Moves an order forward exactly one stage: packed -> shipped, or
    shipped -> delivered. A single "next stage" action (not a status
    dropdown) keeps this consistent with the Pharmacist Module's
    pack_order pattern, and prevents a delivery manager from
    accidentally skipping a stage or moving an order backward.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('delivery.dashboard'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('delivery.dashboard'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('delivery.dashboard'))

        # Only these two specific transitions are allowed here - a
        # delivery manager should never be able to jump an order
        # straight from 'placed' to 'delivered', for example.
        valid_transitions = {'packed': 'shipped', 'shipped': 'delivered'}
        if order['status'] not in valid_transitions:
            cursor.close()
            flash(f"Order #{order_id} isn't ready for this action (current status: {order['status']}).", 'error')
            return redirect(url_for('delivery.dashboard'))

        next_status = valid_transitions[order['status']]
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
            if next_status == 'shipped':
                title = f"Order #{str(order_id).zfill(4)} Shipped 🚚"
                msg = "Your order is on its way!"
                icon = 'local_shipping'
            else: # delivered
                title = f"Order #{str(order_id).zfill(4)} Delivered 🎉"
                msg = "Your order has been delivered successfully. Thank you for choosing SehatHub!"
                icon = 'done_all'
                
            cursor.execute("""
                INSERT INTO notifications (user_id, type, title, message, link, icon, is_read)
                VALUES (%s, 'order_update', %s, %s, '/customer/orders', %s, FALSE)
            """, (user_row['user_id'], title, msg, icon))

        connection.commit()
        cursor.close()

        flash(f'Order #{order_id} marked as {next_status}.', 'success')
        return redirect(url_for('delivery.dashboard'))

    except Exception as e:
        connection.rollback()
        print(f"Advance order error: {e}")
        flash('Something went wrong updating this order.', 'error')
        return redirect(url_for('delivery.dashboard'))

    finally:
        connection.close()


# ============================================================
# REAL-TIME NOTIFICATIONS (polling)
# Same pattern as the customer/pharmacist notifications APIs - the
# navbar bell calls this every 30 seconds while a delivery manager
# is logged in, so a newly-packed order (ready to be picked up and
# shipped) shows up on the bell without a manual refresh.
# ============================================================
@delivery_bp.route('/api/notifications')
@role_required('delivery')
def api_notifications():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'ready_to_ship': 0})

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM orders WHERE status = 'packed'")
        ready_to_ship = cursor.fetchone()['count'] or 0
        return jsonify({'ready_to_ship': ready_to_ship})

    except Exception as e:
        print(f"Notifications API error: {e}")
        return jsonify({'ready_to_ship': 0})

    finally:
        connection.close()