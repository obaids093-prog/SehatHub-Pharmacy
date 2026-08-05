"""
SehatHub - Customer Routes
Handles the medicine catalog, product details, cart, and other
customer-facing shopping features.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, get_flashed_messages
from config.database import get_db_connection
from utils.auth_helpers import login_required
from utils.pricing import calculate_delivery_charge
from utils.csrf import validate_csrf_token
from utils.validators import is_valid_phone, is_valid_full_name, password_strength_error
import difflib

# All routes in this file start with /customer (e.g. /customer/medicines)
customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.route('/api/search')
def api_search():
    """JSON endpoint for navigation bar auto-complete"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])

    connection = get_db_connection()
    if not connection:
        return jsonify([])
    
    try:
        cursor = connection.cursor(dictionary=True)
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT m.medicine_id, m.name, m.generic_name, m.image_url, 
                   b.name as brand_name, c.name as category_name, MIN(mv.price) as min_price
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
            WHERE (m.name LIKE %s OR m.generic_name LIKE %s OR b.name LIKE %s OR c.name LIKE %s) AND m.is_active = TRUE
            GROUP BY m.medicine_id, m.name, m.generic_name, m.image_url, b.name, c.name
            LIMIT 6
        """, (search_term, search_term, search_term, search_term))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        print(f"API Search Error: {e}")
        return jsonify([])
    finally:
        if connection:
            connection.close()


@customer_bp.route('/medicines')
def medicine_catalog():
    """
    Shows the medicine catalog grid.
    Supports these optional URL query parameters:
      - ?category=<id>   -> only show medicines in that category
      - ?brand=<id>      -> only show medicines from that brand/company
      - ?search=<text>   -> only show medicines whose name or generic_name
                            matches the search text (partial match)
      - ?sort=<option>   -> price_low, price_high, or name (default: name)

    Example URL: /customer/medicines?category=2&brand=1&search=panadol&sort=price_low
    """

    # request.args reads query parameters from the URL.
    # .get() returns None if the parameter wasn't provided, instead of crashing.
    selected_category = request.args.get('category', type=int)
    selected_brand = request.args.get('brand', type=int)
    search_query = request.args.get('search', default='', type=str).strip()
    sort_option = request.args.get('sort', default='name')
    price_range = request.args.get('price_range', default='', type=str)
    in_stock_only = request.args.get('in_stock', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    per_page = 24

    connection = get_db_connection()
    if connection is None:
        return render_template('customer/catalog.html', medicines=[], categories=[], brands=[],
                                selected_category=selected_category, selected_brand=selected_brand,
                                search_query=search_query, sort_option=sort_option,
                                price_range=price_range, in_stock_only=in_stock_only,
                                page=1, total_pages=1,
                                error="Could not connect to the database.")

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------------
        # STEP 1: Get all categories (needed to render the filter checkboxes)
        # ----------------------------------------------------------
        cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()

        # STEP 1b: Get all brands that actually have at least one active
        # medicine (no point showing a brand filter with zero results).
        cursor.execute("""
            SELECT DISTINCT b.brand_id, b.name
            FROM brands b
            JOIN medicines m ON m.brand_id = b.brand_id
            WHERE m.is_active = TRUE
            ORDER BY b.name
        """)
        brands = cursor.fetchall()

        # ----------------------------------------------------------
        # STEP 2: Build the medicines query
        # We use MIN(price) because one medicine can have multiple pack-size
        # variants (e.g. "Strip of 10" vs "Bottle of 30") at different prices -
        # the catalog card shows the CHEAPEST available option, similar to
        # how Dawaai.pk shows "starting from Rs. X" pricing.
        # We also sum up stock across all variants to know if ANYTHING
        # is in stock for that medicine.
        # ----------------------------------------------------------
        where_clauses = ["m.is_active = TRUE"]
        params = []

        if selected_category:
            where_clauses.append("m.category_id = %s")
            params.append(selected_category)

        if selected_brand:
            where_clauses.append("m.brand_id = %s")
            params.append(selected_brand)

        if search_query:
            where_clauses.append("(m.name LIKE %s OR m.generic_name LIKE %s OR b.name LIKE %s)")
            like_term = f"%{search_query}%"
            params.extend([like_term, like_term, like_term])
            
        where_str = " AND ".join(where_clauses)

        having_clauses = []
        if price_range == 'under_100':
            having_clauses.append("MIN(mv.price) < 100")
        elif price_range == '100_500':
            having_clauses.append("MIN(mv.price) >= 100 AND MIN(mv.price) <= 500")
        elif price_range == '500_plus':
            having_clauses.append("MIN(mv.price) > 500")

        if in_stock_only == '1':
            having_clauses.append("SUM(mv.stock_qty) > 0")

        having_str = (" HAVING " + " AND ".join(having_clauses)) if having_clauses else ""

        # ----------------------------------------------------------
        # STEP 2: Get Total Count for Pagination (SQL-level)
        # ----------------------------------------------------------
        count_query = f"""
            SELECT COUNT(*) AS total FROM (
                SELECT m.medicine_id
                FROM medicines m
                LEFT JOIN brands b ON m.brand_id = b.brand_id
                LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
                WHERE {where_str}
                GROUP BY m.medicine_id
                {having_str}
            ) AS count_table
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page

        # ----------------------------------------------------------
        # STEP 3: Fetch Data for Current Page
        # ----------------------------------------------------------
        order_str = "ORDER BY m.name ASC"
        if sort_option == 'price_low':
            order_str = "ORDER BY min_price ASC"
        elif sort_option == 'price_high':
            order_str = "ORDER BY min_price DESC"

        main_query = f"""
            SELECT
                m.medicine_id, m.name, m.type, m.image_url,
                b.brand_id, b.name AS brand_name, c.name AS category_name,
                MIN(mv.price) AS min_price, SUM(mv.stock_qty) AS total_stock
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
            WHERE {where_str}
            GROUP BY m.medicine_id, m.name, m.type, m.image_url, b.brand_id, b.name, c.name
            {having_str}
            {order_str}
            LIMIT %s OFFSET %s
        """
        cursor.execute(main_query, params + [per_page, start_idx])
        medicines = cursor.fetchall()

        # ----------------------------------------------------------
        # STEP 4: "Did you mean...?"
        # ----------------------------------------------------------
        did_you_mean = None
        if search_query and total_count == 0:
            cursor.execute("SELECT DISTINCT name FROM medicines WHERE is_active = TRUE")
            raw_names = [row['name'] for row in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT generic_name FROM medicines WHERE is_active = TRUE")
            raw_names += [row['generic_name'] for row in cursor.fetchall() if row['generic_name']]
            cursor.execute("SELECT DISTINCT name FROM brands")
            raw_names += [row['name'] for row in cursor.fetchall()]

            # Build a lowercase -> original-casing lookup of both full names
            # AND individual words within them (e.g. "Hilton Pharma" also
            # registers "hilton" and "pharma" separately). This way searching
            # a partial/typo'd word like "hiltan" can still match "Hilton"
            # instead of only matching if the WHOLE phrase was typed.
            lookup = {}
            for full_name in raw_names:
                lookup[full_name.lower()] = full_name
                for word in full_name.split():
                    word_clean = word.strip("(),+").lower()
                    if len(word_clean) >= 3:
                        lookup.setdefault(word_clean, word.strip("(),+"))

            close_matches = difflib.get_close_matches(search_query.lower(), lookup.keys(), n=1, cutoff=0.6)
            if close_matches:
                did_you_mean = lookup[close_matches[0]]

        return render_template(
            'customer/catalog.html',
            medicines=medicines,
            categories=categories,
            brands=brands,
            selected_category=selected_category,
            selected_brand=selected_brand,
            search_query=search_query,
            did_you_mean=did_you_mean,
            sort_option=sort_option,
            price_range=price_range,
            in_stock_only=in_stock_only,
            page=page,
            total_pages=total_pages,
            total_count=total_count
        )

    except Exception as e:
        print(f"Catalog error: {e}")
        return render_template('customer/catalog.html', medicines=[], categories=[], brands=[],
                                selected_category=selected_category, selected_brand=selected_brand,
                                search_query=search_query, sort_option=sort_option,
                                error="Something went wrong loading medicines.")

    finally:
        cursor.close()
        connection.close()


@customer_bp.route('/api/search-suggestions')
def search_suggestions():
    """
    Live autocomplete endpoint for the navbar search bar.
    Called via AJAX (fetch) on every keystroke - returns a small JSON list
    of matching medicine names, generic names, and brand/company names, so
    the user sees real, correctly-spelled suggestions WHILE typing instead
    of finding out after hitting Enter that they made a typo.

    Example: GET /customer/api/search-suggestions?q=hilt
    Returns: {"suggestions": [{"label": "Hilton Pharma", "type": "Company"}, ...]}
    """
    q = request.args.get('q', default='', type=str).strip()

    if len(q) < 2:
        return jsonify({"suggestions": []})

    connection = get_db_connection()
    if connection is None:
        return jsonify({"suggestions": []})

    cursor = connection.cursor(dictionary=True)
    like_term = f"%{q}%"
    suggestions = []

    try:
        # Matching medicine names (e.g. typing "pana" -> "Panadol Tablet")
        cursor.execute("""
            SELECT m.name, c.name as category_name
            FROM medicines m
            LEFT JOIN categories c ON m.category_id = c.category_id
            WHERE m.is_active = TRUE AND m.name LIKE %s
            GROUP BY m.name, c.name
            LIMIT 5
        """, (like_term,))
        for row in cursor.fetchall():
            cat = row.get('category_name') or ''
            type_label = "Device" if cat == "Medical Devices" else "Medicine"
            suggestions.append({"label": row['name'], "type": type_label})

        # Matching generic/chemical names (e.g. typing "parace" -> "Paracetamol 500mg")
        cursor.execute("""
            SELECT DISTINCT generic_name FROM medicines
            WHERE is_active = TRUE AND generic_name LIKE %s
            LIMIT 3
        """, (like_term,))
        for row in cursor.fetchall():
            if row['generic_name']:
                suggestions.append({"label": row['generic_name'], "type": "Generic"})

        # Matching brand/company names (e.g. typing "hilt" -> "Hilton Pharma")
        cursor.execute("""
            SELECT DISTINCT b.name FROM brands b
            JOIN medicines m ON m.brand_id = b.brand_id
            WHERE m.is_active = TRUE AND b.name LIKE %s
            LIMIT 3
        """, (like_term,))
        for row in cursor.fetchall():
            suggestions.append({"label": row['name'], "type": "Company"})

        return jsonify({"suggestions": suggestions[:8]})

    except Exception as e:
        print(f"Search suggestions error: {e}")
        return jsonify({"suggestions": []})

    finally:
        cursor.close()
        connection.close()


@customer_bp.route('/medicines/<int:medicine_id>')
def product_detail(medicine_id):
    """
    Shows the full detail page for a single medicine.
    The <int:medicine_id> in the route above means Flask reads the
    number directly from the URL, e.g. /customer/medicines/4 gives
    medicine_id = 4 as a function argument automatically.
    """

    connection = get_db_connection()
    if connection is None:
        return render_template('customer/product_detail.html', medicine=None,
                                error="Could not connect to the database.")

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------------
        # STEP 1: Get the medicine's main details + brand/category names
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                m.medicine_id, m.name, m.generic_name, m.type, m.image_url,
                m.description, m.usage_info, m.side_effects,
                b.name AS brand_name, c.name AS category_name
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            WHERE m.medicine_id = %s AND m.is_active = TRUE
        """, (medicine_id,))
        medicine = cursor.fetchone()

        # If no medicine was found with that ID, show a "not found" page
        if medicine is None:
            return render_template('customer/product_detail.html', medicine=None,
                                    error="Medicine not found."), 404

        # ----------------------------------------------------------
        # STEP 2: Get all pack-size variants for this medicine
        # (this powers the "Select Pack Size" buttons)
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT variant_id, pack_size, price, stock_qty
            FROM medicine_variants
            WHERE medicine_id = %s
            ORDER BY price ASC
        """, (medicine_id,))
        variants = cursor.fetchall()

        # ----------------------------------------------------------
        # STEP 3: Get reviews for this medicine, with the reviewer's name
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT r.rating, r.comment, r.created_at, u.full_name
            FROM reviews r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN users u ON c.user_id = u.user_id
            WHERE r.medicine_id = %s
            ORDER BY r.created_at DESC
        """, (medicine_id,))
        reviews = cursor.fetchall()

        # Calculate the average rating to show as stars (e.g. 4.3 out of 5)
        if reviews:
            average_rating = sum(r['rating'] for r in reviews) / len(reviews)
        else:
            average_rating = 0

        # ----------------------------------------------------------
        # STEP 4: Get Similar Medicines
        # Fetch medicines from the same category, excluding this one.
        # ----------------------------------------------------------
        similar_medicines = []
        if medicine.get('category_name'):
            cursor.execute("""
                SELECT
                    m.medicine_id, m.name, m.image_url,
                    b.name AS brand_name,
                    c.name AS category_name,
                    MIN(mv.price) AS min_price
                FROM medicines m
                LEFT JOIN brands b ON m.brand_id = b.brand_id
                LEFT JOIN categories c ON m.category_id = c.category_id
                JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
                WHERE c.name = %s AND m.medicine_id != %s AND m.is_active = TRUE AND mv.stock_qty > 0
                GROUP BY m.medicine_id, m.name, m.image_url, b.name, c.name
                ORDER BY RAND()
                LIMIT 8
            """, (medicine['category_name'], medicine_id))
            similar_medicines = cursor.fetchall()

        return render_template(
            'customer/product_detail.html',
            medicine=medicine,
            variants=variants,
            reviews=reviews,
            average_rating=average_rating,
            similar_medicines=similar_medicines
        )

    except Exception as e:
        print(f"Product detail error: {e}")
        return render_template('customer/product_detail.html', medicine=None,
                                error="Something went wrong loading this medicine.")

    finally:
        cursor.close()
        connection.close()


def get_customer_id(connection, user_id):
    """
    Helper function: given a logged-in user's user_id (from the session),
    find their corresponding customer_id (from the customers table).
    We need this because cart_items links to customer_id, not user_id directly.
    """
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT customer_id FROM customers WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    return result['customer_id'] if result else None


@customer_bp.route('/cart')
@login_required
def view_cart():
    """
    Shows the logged-in customer's shopping cart.
    """
    connection = get_db_connection()
    if connection is None:
        return render_template('customer/cart.html', cart_items=[], subtotal=0,
                                delivery_charge=0, total=0, popular_medicines=[],
                                error="Could not connect to the database.")

    try:
        customer_id = get_customer_id(connection, session['user_id'])

        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                ci.cart_item_id, ci.quantity, ci.variant_id,
                mv.pack_size, mv.price, mv.stock_qty,
                m.medicine_id, m.name AS medicine_name, m.image_url,
                b.name AS brand_name
            FROM cart_items ci
            JOIN medicine_variants mv ON ci.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            WHERE ci.customer_id = %s
            ORDER BY ci.added_at DESC
        """, (customer_id,))
        cart_items = cursor.fetchall()

        cursor.execute("""
            SELECT
                si.saved_item_id, si.quantity, si.variant_id,
                mv.pack_size, mv.price, mv.stock_qty,
                m.medicine_id, m.name AS medicine_name, m.image_url,
                b.name AS brand_name
            FROM saved_items si
            JOIN medicine_variants mv ON si.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            WHERE si.customer_id = %s
            ORDER BY si.saved_at DESC
        """, (customer_id,))
        saved_items = cursor.fetchall()

        # Fetch a few popular medicines to suggest on the empty-cart screen.
        # We pick medicines that have stock, ordered by how many times they
        # have been ordered (most popular first), limited to 4.
        cursor.execute("""
            SELECT
                m.medicine_id, m.name, m.image_url,
                b.name AS brand_name,
                c.name AS category_name,
                MIN(mv.price) AS min_price
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
            WHERE m.is_active = TRUE AND mv.stock_qty > 0
            GROUP BY m.medicine_id, m.name, m.image_url, b.name, c.name
            ORDER BY (
                SELECT COALESCE(SUM(oi.quantity), 0)
                FROM order_items oi
                JOIN medicine_variants omv ON oi.variant_id = omv.variant_id
                WHERE omv.medicine_id = m.medicine_id
            ) DESC
            LIMIT 4
        """)
        popular_medicines = cursor.fetchall()
        cursor.close()

        # Calculate subtotal in Python: price * quantity, summed across all items
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        delivery_charge = calculate_delivery_charge(subtotal)

        return render_template('customer/cart.html', cart_items=cart_items, subtotal=subtotal,
                                delivery_charge=delivery_charge, total=subtotal + delivery_charge,
                                popular_medicines=popular_medicines, saved_items=saved_items)

    except Exception as e:
        print(f"Cart view error: {e}")
        return render_template('customer/cart.html', cart_items=[], subtotal=0,
                                delivery_charge=0, total=0, popular_medicines=[],
                                saved_items=[], error="Something went wrong loading your cart.")

    finally:
        connection.close()


@customer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """
    Adds an item to the cart. Called from the product detail page's
    "Add to Cart" form. Redirects back with a flash message.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('customer.medicine_catalog'))

    variant_id = request.form.get('variant_id', type=int)
    quantity = request.form.get('quantity', type=int, default=1)

    if not variant_id:
        flash('Something went wrong adding that item.', 'error')
        return redirect(url_for('customer.medicine_catalog'))

    if not quantity or quantity < 1:
        flash('Please choose a valid quantity.', 'error')
        return redirect(url_for('customer.medicine_catalog'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('customer.medicine_catalog'))

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # Check if this exact variant is already in the cart - if so,
        # just increase the quantity instead of creating a duplicate row.
        cursor.execute(
            "SELECT cart_item_id, quantity FROM cart_items WHERE customer_id = %s AND variant_id = %s",
            (customer_id, variant_id)
        )
        existing = cursor.fetchone()

        # Check stock quantity
        cursor.execute("SELECT stock_qty FROM medicine_variants WHERE variant_id = %s", (variant_id,))
        variant = cursor.fetchone()
        if not variant:
            flash('Invalid medicine variant.', 'error')
            return redirect(url_for('customer.medicine_catalog'))
        
        current_cart_qty = existing['quantity'] if existing else 0
        if current_cart_qty + quantity > variant['stock_qty']:
            flash(f'Cannot add to cart. Only {variant["stock_qty"]} in stock.', 'error')
            return redirect(url_for('customer.medicine_catalog'))

        if existing:
            new_quantity = existing['quantity'] + quantity
            cursor.execute(
                "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
                (new_quantity, existing['cart_item_id'])
            )
        else:
            cursor.execute(
                "INSERT INTO cart_items (customer_id, variant_id, quantity) VALUES (%s, %s, %s)",
                (customer_id, variant_id, quantity)
            )

        connection.commit()
        cursor.close()
        flash('Added to cart!', 'success')
        return redirect(url_for('customer.view_cart'))

    except Exception as e:
        connection.rollback()
        print(f"Add to cart error: {e}")
        flash('Something went wrong adding that item to your cart.', 'error')
        return redirect(url_for('customer.medicine_catalog'))

    finally:
        connection.close()


@customer_bp.route('/cart/quick-add', methods=['POST'])
@login_required
def quick_add_to_cart():
    """
    Same insert-or-increment logic as add_to_cart(), but returns JSON
    and doesn't navigate away - used by the "+" quick-add button on
    product cards (homepage, catalog grid) so adding an item doesn't
    interrupt browsing by jumping to a different page. The full
    add_to_cart() form (on the product detail page, where the customer
    picks a specific pack size) is unaffected by this.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired. Please refresh the page.'}), 400

    variant_id = request.form.get('variant_id', type=int)
    if not variant_id:
        return jsonify({'success': False, 'message': 'Something went wrong adding that item.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Could not connect to the database.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        if customer_id is None:
            return jsonify({'success': False, 'message': 'No customer account found for this login.'}), 400

        cursor = connection.cursor(dictionary=True)

        # Make sure this variant is actually in stock before adding
        cursor.execute("SELECT stock_qty FROM medicine_variants WHERE variant_id = %s", (variant_id,))
        variant = cursor.fetchone()
        if not variant or variant['stock_qty'] <= 0:
            cursor.close()
            return jsonify({'success': False, 'message': 'This item is currently out of stock.'}), 400

        cursor.execute(
            "SELECT cart_item_id, quantity FROM cart_items WHERE customer_id = %s AND variant_id = %s",
            (customer_id, variant_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "UPDATE cart_items SET quantity = quantity + 1 WHERE cart_item_id = %s",
                (existing['cart_item_id'],)
            )
        else:
            cursor.execute(
                "INSERT INTO cart_items (customer_id, variant_id, quantity) VALUES (%s, %s, 1)",
                (customer_id, variant_id)
            )

        connection.commit()

        cursor.execute(
            "SELECT COALESCE(SUM(quantity), 0) AS total FROM cart_items WHERE customer_id = %s",
            (customer_id,)
        )
        cart_count = cursor.fetchone()['total']
        cursor.close()

        return jsonify({'success': True, 'cart_count': cart_count})

    except Exception as e:
        connection.rollback()
        print(f"Quick add to cart error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong adding that item.'}), 500

    finally:
        connection.close()


@customer_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    """
    Updates the quantity of a single cart item. Called via AJAX (fetch)
    from the cart page's +/- buttons - returns JSON, not a full page,
    so the page doesn't need to reload.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired. Please refresh the page and try again.'}), 400

    cart_item_id = request.form.get('cart_item_id', type=int)
    new_quantity = request.form.get('quantity', type=int)

    if not cart_item_id or new_quantity is None or new_quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # Security check: make sure this cart item actually belongs to
        # the logged-in customer, so nobody can edit someone else's cart
        # just by guessing a cart_item_id number.
        cursor.execute(
            "SELECT mv.price, mv.stock_qty FROM cart_items ci JOIN medicine_variants mv ON ci.variant_id = mv.variant_id "
            "WHERE ci.cart_item_id = %s AND ci.customer_id = %s",
            (cart_item_id, customer_id)
        )
        item = cursor.fetchone()

        if not item:
            cursor.close()
            return jsonify({'success': False, 'message': 'Item not found.'}), 404
            
        if new_quantity > item['stock_qty']:
            cursor.close()
            return jsonify({'success': False, 'message': f'Cannot update quantity. Only {item["stock_qty"]} in stock.'}), 400

        cursor.execute(
            "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s",
            (new_quantity, cart_item_id)
        )
        connection.commit()
        cursor.close()

        new_line_total = float(item['price']) * new_quantity
        return jsonify({'success': True, 'line_total': new_line_total})

    except Exception as e:
        connection.rollback()
        print(f"Update cart error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong.'}), 500

    finally:
        connection.close()


@customer_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_cart_item():
    """
    Removes an item from the cart. Called via AJAX (fetch) from the
    cart page's trash icon - returns JSON.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired. Please refresh the page and try again.'}), 400

    cart_item_id = request.form.get('cart_item_id', type=int)

    if not cart_item_id:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor()

        # Same security check as above - only delete if it belongs to this customer
        cursor.execute(
            "DELETE FROM cart_items WHERE cart_item_id = %s AND customer_id = %s",
            (cart_item_id, customer_id)
        )
        connection.commit()
        cursor.close()

        return jsonify({'success': True})

    except Exception as e:
        connection.rollback()
        print(f"Remove cart item error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong.'}), 500

    finally:
        connection.close()


@customer_bp.route('/cart/save_for_later', methods=['POST'])
@login_required
def save_for_later():
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired.'}), 400

    cart_item_id = request.form.get('cart_item_id', type=int)
    if not cart_item_id:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT variant_id, quantity FROM cart_items WHERE cart_item_id = %s AND customer_id = %s", (cart_item_id, customer_id))
        item = cursor.fetchone()

        if not item:
            cursor.close()
            return jsonify({'success': False, 'message': 'Item not found.'}), 404

        # Check if already in saved_items
        cursor.execute("SELECT saved_item_id, quantity FROM saved_items WHERE customer_id = %s AND variant_id = %s", (customer_id, item['variant_id']))
        saved = cursor.fetchone()
        
        if saved:
            cursor.execute("UPDATE saved_items SET quantity = quantity + %s WHERE saved_item_id = %s", (item['quantity'], saved['saved_item_id']))
        else:
            cursor.execute("INSERT INTO saved_items (customer_id, variant_id, quantity) VALUES (%s, %s, %s)", (customer_id, item['variant_id'], item['quantity']))
            
        cursor.execute("DELETE FROM cart_items WHERE cart_item_id = %s", (cart_item_id,))
        connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        connection.rollback()
        print(f"Save for later error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong.'}), 500
    finally:
        connection.close()


@customer_bp.route('/cart/move_to_cart', methods=['POST'])
@login_required
def move_to_cart():
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired.'}), 400

    saved_item_id = request.form.get('saved_item_id', type=int)
    if not saved_item_id:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT variant_id, quantity FROM saved_items WHERE saved_item_id = %s AND customer_id = %s", (saved_item_id, customer_id))
        item = cursor.fetchone()

        if not item:
            cursor.close()
            return jsonify({'success': False, 'message': 'Item not found.'}), 404

        cursor.execute("SELECT cart_item_id FROM cart_items WHERE customer_id = %s AND variant_id = %s", (customer_id, item['variant_id']))
        cart_item = cursor.fetchone()
        
        if cart_item:
            cursor.execute("UPDATE cart_items SET quantity = quantity + %s WHERE cart_item_id = %s", (item['quantity'], cart_item['cart_item_id']))
        else:
            cursor.execute("INSERT INTO cart_items (customer_id, variant_id, quantity) VALUES (%s, %s, %s)", (customer_id, item['variant_id'], item['quantity']))
            
        cursor.execute("DELETE FROM saved_items WHERE saved_item_id = %s", (saved_item_id,))
        connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        connection.rollback()
        print(f"Move to cart error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong.'}), 500
    finally:
        connection.close()


@customer_bp.route('/cart/remove_saved', methods=['POST'])
@login_required
def remove_saved_item():
    if not validate_csrf_token(request.form.get('csrf_token')):
        return jsonify({'success': False, 'message': 'Your session expired.'}), 400

    saved_item_id = request.form.get('saved_item_id', type=int)
    if not saved_item_id:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'message': 'Database error.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor()
        cursor.execute("DELETE FROM saved_items WHERE saved_item_id = %s AND customer_id = %s", (saved_item_id, customer_id))
        connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        connection.rollback()
        print(f"Remove saved item error: {e}")
        return jsonify({'success': False, 'message': 'Something went wrong.'}), 500
    finally:
        connection.close()



@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    GET  -> show the checkout page (address form + order summary)
    POST -> form submitted, place the order
    """
    # On a plain GET visit (not a form submission), clear out any old
    # flash messages that may have piled up from earlier actions and
    # never gotten displayed (e.g. multiple "Added to cart!" clicks).
    # This stops old messages from suddenly appearing all at once here.
    if request.method == 'GET':
        get_flashed_messages()

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('customer.view_cart'))

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------------
        # Get the customer's current cart items (needed for both
        # GET - to show the order summary - and POST - to actually
        # build the order)
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                ci.cart_item_id, ci.quantity, ci.variant_id,
                mv.pack_size, mv.price, mv.stock_qty,
                m.name AS medicine_name, m.image_url, m.type
            FROM cart_items ci
            JOIN medicine_variants mv ON ci.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            WHERE ci.customer_id = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()

        # If the cart is empty, there's nothing to check out
        if not cart_items:
            cursor.close()
            flash('Your cart is empty. Add some medicines first!', 'error')
            return redirect(url_for('customer.medicine_catalog'))

        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
        delivery_charge = calculate_delivery_charge(subtotal)
        total = subtotal + delivery_charge

        # ----------------------------------------------------------
        # PRESCRIPTION ENFORCEMENT
        # If ANY item in the cart is a Prescription-type medicine
        # (e.g. Diagesic-P, Alp), the customer must attach an uploaded
        # prescription to this order before we let them check out.
        # Rejected prescriptions don't count - only pending/approved.
        # Each prescription can only be used for ONE order - once it's
        # linked to an order (order_id gets set), it no longer counts
        # as "available", so a fresh prescription is required for the
        # next order that needs one (matches real pharmacy practice).
        # ----------------------------------------------------------
        requires_prescription = any(item['type'] == 'Prescription' for item in cart_items)
        available_prescriptions = []

        if requires_prescription:
            cursor.execute("""
                SELECT prescription_id, image_path, status, uploaded_at
                FROM prescriptions
                WHERE customer_id = %s AND status != 'rejected' AND order_id IS NULL
                AND uploaded_at >= NOW() - INTERVAL 1 HOUR
                ORDER BY uploaded_at DESC
            """, (customer_id,))
            available_prescriptions = cursor.fetchall()

            # GATE: if a prescription is required and the customer has NONE
            # on file yet, show the "Upload Prescription to Proceed" page
            # (mirrors D.Watson.pk's checkout flow) INSTEAD OF the normal
            # checkout page - they can't even see the address/payment form
            # until they've uploaded at least one prescription.
            if not available_prescriptions:
                cursor.close()
                items_needing_prescription = [item for item in cart_items if item['type'] == 'Prescription']
                return render_template('customer/checkout_prescription_required.html',
                                        items_needing_prescription=items_needing_prescription,
                                        cart_items=cart_items, subtotal=subtotal,
                                        delivery_charge=delivery_charge, total=total)

        # The most recently uploaded (non-rejected) prescription is the one
        # we'll attach to this order - no manual selection needed, matching
        # the simple D.Watson-style flow (upload once, checkout proceeds).
        selected_prescription_id = available_prescriptions[0]['prescription_id'] if available_prescriptions else None

        # ----------------------------------------------------------
        # POST: the address form was submitted - place the order
        # ----------------------------------------------------------
        if request.method == 'POST':
            if not validate_csrf_token(request.form.get('csrf_token')):
                cursor.close()
                flash('Your session expired or this request looked suspicious. Please try again.', 'error')
                return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                        delivery_charge=delivery_charge, total=total)

            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone', '').strip()
            address_line = request.form.get('address_line', '').strip()
            city = request.form.get('city', '').strip()
            payment_method = request.form.get('payment_method', 'cash_on_delivery')
            special_instructions = request.form.get('special_instructions', '').strip() or None

            if not full_name or not phone or not address_line or not city:
                cursor.close()
                flash('Please fill in all delivery address fields.', 'error')
                return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                        delivery_charge=delivery_charge, total=total)

            if not is_valid_full_name(full_name):
                cursor.close()
                flash('Please enter a valid full name.', 'error')
                return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                        delivery_charge=delivery_charge, total=total)

            if not is_valid_phone(phone):
                cursor.close()
                flash('Please enter a valid Pakistani mobile number (e.g. 0301-2345678).', 'error')
                return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                        delivery_charge=delivery_charge, total=total)

            # Combine the address fields into one string for the
            # orders.delivery_address column (we kept the schema simple
            # with a single address field rather than separate columns)
            full_address = f"{full_name}, {address_line}, {city} | Phone: {phone}"
            
            # Final Stock Check before placing order
            for item in cart_items:
                if item['quantity'] > item['stock_qty']:
                    cursor.close()
                    flash(f"Only {item['stock_qty']} of {item['medicine_name']} available in stock. Please update your cart.", 'error')
                    return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                            delivery_charge=delivery_charge, total=total)

            # In the real world, the shipping address for a specific order
            # should NOT overwrite the user's primary profile address. 
            # We save the full_address directly to the order record below.

            # Create the order record - total_amount includes delivery charge,
            # not just the medicine subtotal
            cursor.execute(
                """INSERT INTO orders (customer_id, total_amount, status, delivery_address, special_instructions, payment_method)
                   VALUES (%s, %s, 'placed', %s, %s, %s)""",
                (customer_id, total, full_address, special_instructions, payment_method)
            )
            new_order_id = cursor.lastrowid

            # Link the chosen prescription to this order, so a pharmacist
            # reviewing it later can see exactly which order it belongs to
            if requires_prescription and selected_prescription_id:
                cursor.execute(
                    "UPDATE prescriptions SET order_id = %s WHERE prescription_id = %s AND customer_id = %s",
                    (new_order_id, selected_prescription_id, customer_id)
                )

            # Copy each cart item into order_items, and reduce stock
            for item in cart_items:
                cursor.execute(
                    """INSERT INTO order_items (order_id, variant_id, quantity, price_at_purchase)
                       VALUES (%s, %s, %s, %s)""",
                    (new_order_id, item['variant_id'], item['quantity'], item['price'])
                )
                # Reduce stock by the quantity ordered, so the catalog
                # reflects what's actually still available
                cursor.execute(
                    "UPDATE medicine_variants SET stock_qty = stock_qty - %s WHERE variant_id = %s",
                    (item['quantity'], item['variant_id'])
                )

            # Empty the cart now that the order has been placed
            cursor.execute("DELETE FROM cart_items WHERE customer_id = %s", (customer_id,))

            connection.commit()
            cursor.close()

            flash('Your order has been placed successfully!', 'success')
            return redirect(url_for('customer.order_confirmation', order_id=new_order_id))

        # ----------------------------------------------------------
        # GET: just show the checkout page
        # ----------------------------------------------------------
        # Fetch user's phone and name from users table
        cursor.execute("SELECT full_name, phone FROM users WHERE user_id = %s", (session['user_id'],))
        user_record = cursor.fetchone()
        default_full_name = user_record['full_name'] if user_record else ''
        default_phone = user_record['phone'] if user_record else ''

        # Fetch last delivery address from orders
        cursor.execute("SELECT delivery_address FROM orders WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1", (customer_id,))
        last_order = cursor.fetchone()
        
        default_address = ''
        default_city = ''
        if last_order and last_order['delivery_address']:
            addr_str = last_order['delivery_address'].split('|')[0].strip()
            parts = [p.strip() for p in addr_str.split(',')]
            if len(parts) >= 3:
                default_city = parts[-1]
                default_address = ", ".join(parts[1:-1])

        cursor.close()
        return render_template('customer/checkout.html', cart_items=cart_items, subtotal=subtotal,
                                delivery_charge=delivery_charge, total=total,
                                default_full_name=default_full_name, default_phone=default_phone,
                                default_address=default_address, default_city=default_city,
                                requires_prescription=requires_prescription)

    except Exception as e:
        connection.rollback()
        print(f"Checkout error: {e}")
        flash('Something went wrong placing your order. Please try again.', 'error')
        return redirect(url_for('customer.view_cart'))

    finally:
        connection.close()


@customer_bp.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """
    Shows a simple "thank you" confirmation page after an order is placed.
    """
    connection = get_db_connection()
    if connection is None:
        return redirect(url_for('home'))

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # Make sure this order actually belongs to the logged-in customer
        cursor.execute(
            "SELECT order_id, total_amount, status, created_at, delivery_address, payment_method FROM orders WHERE order_id = %s AND customer_id = %s",
            (order_id, customer_id)
        )
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('home'))

        # Fetch order items to display a summary
        cursor.execute("""
            SELECT oi.quantity, oi.price_at_purchase, m.name, m.image_url, mv.pack_size
            FROM order_items oi
            JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            WHERE oi.order_id = %s
        """, (order_id,))
        order_items = cursor.fetchall()

        # Check if this order requires prescription verification
        cursor.execute("SELECT prescription_id FROM prescriptions WHERE order_id = %s", (order_id,))
        has_prescription = cursor.fetchone() is not None

        cursor.close()

        return render_template('customer/order_confirmation.html', 
                               order=order, 
                               order_items=order_items, 
                               has_prescription=has_prescription)

    finally:
        connection.close()


@customer_bp.route('/orders')
@login_required
def order_history():
    """
    Shows a list of all past orders for the logged-in customer,
    most recent first.
    """
    connection = get_db_connection()
    if connection is None:
        return render_template('customer/order_history.html', orders=[],
                                error="Could not connect to the database.")

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------------
        # For each order, count how many distinct items it contains
        # using COUNT() - this lets the list show "3 items" without
        # needing a separate query per order.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                o.order_id, o.total_amount, o.status, o.payment_method, o.created_at,
                COUNT(oi.order_item_id) AS item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.customer_id = %s
            GROUP BY o.order_id, o.total_amount, o.status, o.payment_method, o.created_at
            ORDER BY o.created_at DESC
        """, (customer_id,))
        orders = cursor.fetchall()
        cursor.close()

        return render_template('customer/order_history.html', orders=orders)

    except Exception as e:
        print(f"Order history error: {e}")
        return render_template('customer/order_history.html', orders=[],
                                error="Something went wrong loading your orders.")

    finally:
        connection.close()


@customer_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """
    Shows full detail for a single past order, including every item
    ordered and a simple status timeline (for the "Track Order" view).
    """
    connection = get_db_connection()
    if connection is None:
        return redirect(url_for('customer.order_history'))

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # Security check: only show this order if it belongs to the
        # logged-in customer (same pattern used everywhere else in cart/checkout)
        cursor.execute(
            "SELECT order_id, total_amount, status, delivery_address, special_instructions, payment_method, created_at, cancellation_reason "
            "FROM orders WHERE order_id = %s AND customer_id = %s",
            (order_id, customer_id)
        )
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('customer.order_history'))

        # Get every item that was part of this order
        cursor.execute("""
            SELECT
                oi.quantity, oi.price_at_purchase,
                mv.pack_size, m.name AS medicine_name, m.image_url, b.name AS brand_name
            FROM order_items oi
            JOIN medicine_variants mv ON oi.variant_id = mv.variant_id
            JOIN medicines m ON mv.medicine_id = m.medicine_id
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        cursor.close()

        # ----------------------------------------------------------
        # Build a simple status timeline for the "Track Order" display.
        # Our orders.status is a single ENUM value (placed/confirmed/
        # packed/shipped/delivered/cancelled), not a history log - so
        # we simulate a timeline by showing every stage up to and
        # including the current one as "completed".
        # ----------------------------------------------------------
        all_stages = ['placed', 'confirmed', 'packed', 'shipped', 'delivered']
        current_stage_index = all_stages.index(order['status']) if order['status'] in all_stages else -1

        timeline = []
        for i, stage in enumerate(all_stages):
            timeline.append({
                'name': stage,
                'completed': i <= current_stage_index,
                'is_current': i == current_stage_index
            })

        return render_template(
            'customer/order_detail.html',
            order=order,
            items=items,
            timeline=timeline,
            is_cancelled=(order['status'] == 'cancelled')
        )

    finally:
        connection.close()


@customer_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """
    Allows a customer to cancel their order if it is still 'placed' or 'confirmed'.
    Restores the stock quantities for the items in the order.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired or this request looked suspicious. Please try again.', 'error')
        return redirect(url_for('customer.order_detail', order_id=order_id))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('customer.order_detail', order_id=order_id))

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        cursor = connection.cursor(dictionary=True)

        # Ensure the order belongs to the user and is in a cancellable state
        cursor.execute(
            "SELECT status FROM orders WHERE order_id = %s AND customer_id = %s",
            (order_id, customer_id)
        )
        order = cursor.fetchone()

        if not order:
            cursor.close()
            flash('Order not found.', 'error')
            return redirect(url_for('customer.order_history'))

        if order['status'] not in ['placed', 'confirmed']:
            cursor.close()
            flash('This order can no longer be cancelled.', 'error')
            return redirect(url_for('customer.order_detail', order_id=order_id))

        # Update the order status
        cursor.execute(
            "UPDATE orders SET status = 'cancelled', cancellation_reason = 'Cancelled by customer' WHERE order_id = %s",
            (order_id,)
        )

        title = f"Order #{str(order_id).zfill(4)} Cancelled"
        msg = "You successfully cancelled this order."
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, link, icon, is_read)
            VALUES (%s, 'order_update', %s, %s, '/customer/orders', 'cancel', FALSE)
        """, (session['user_id'], title, msg))

        # Restore stock for each item in the order
        cursor.execute("SELECT variant_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()

        for item in items:
            cursor.execute(
                "UPDATE medicine_variants SET stock_qty = stock_qty + %s WHERE variant_id = %s",
                (item['quantity'], item['variant_id'])
            )

        connection.commit()
        cursor.close()
        flash('Order has been cancelled successfully.', 'success')

    except Exception as e:
        connection.rollback()
        print(f"Cancel order error: {e}")
        flash('Something went wrong trying to cancel the order.', 'error')

    finally:
        connection.close()

    return redirect(url_for('customer.order_detail', order_id=order_id))

# ============================================================
# PRESCRIPTION UPLOAD
# ============================================================

ALLOWED_PRESCRIPTION_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}


def is_allowed_prescription_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PRESCRIPTION_EXTENSIONS


@customer_bp.route('/prescriptions', methods=['GET', 'POST'])
@login_required
def upload_prescription():
    import os
    import time
    from werkzeug.utils import secure_filename

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('home'))

    try:
        customer_id = get_customer_id(connection, session['user_id'])

        if request.method == 'POST':
            if not validate_csrf_token(request.form.get('csrf_token')):
                flash('Your session expired or this request looked suspicious. Please try again.', 'error')
                return redirect(url_for('customer.upload_prescription'))

            if 'prescription_file' not in request.files:
                flash('Please choose a file to upload.', 'error')
                return redirect(url_for('customer.upload_prescription'))

            file = request.files['prescription_file']

            if file.filename == '':
                flash('Please choose a file to upload.', 'error')
                return redirect(url_for('customer.upload_prescription'))

            if not is_allowed_prescription_file(file.filename):
                flash('Only image files (JPG, PNG) or PDF are allowed.', 'error')
                return redirect(url_for('customer.upload_prescription'))

            original_filename = secure_filename(file.filename)
            unique_filename = f"customer{customer_id}_{int(time.time())}_{original_filename}"

            upload_folder = os.path.join('uploads', 'prescriptions')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO prescriptions (customer_id, image_path, status) VALUES (%s, %s, 'pending')",
                (customer_id, file_path.replace('\\', '/'))
            )
            connection.commit()
            cursor.close()

            next_url = request.args.get('next')
            if next_url == 'checkout':
                flash('Prescription uploaded! You can now complete your checkout. Our pharmacist will review it before dispatching.', 'success')
                return redirect(url_for('customer.checkout'))
            else:
                flash('Prescription uploaded successfully! Our pharmacist will review it shortly.', 'success')
                return redirect(url_for('customer.upload_prescription'))

        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT prescription_id, image_path, status, uploaded_at, rejection_reason FROM prescriptions "
            "WHERE customer_id = %s ORDER BY uploaded_at DESC",
            (customer_id,)
        )
        prescriptions = cursor.fetchall()

        # Now that the customer is looking at this page, clear the
        # "new update" notification badge - they've seen the latest
        # status of everything.
        cursor.execute(
            "UPDATE prescriptions SET customer_seen = TRUE WHERE customer_id = %s AND customer_seen = FALSE",
            (customer_id,)
        )
        connection.commit()
        cursor.close()

        return render_template('customer/prescription_upload.html', prescriptions=prescriptions)

    finally:
        connection.close()


# ============================================================
# MY PROFILE
# ============================================================

@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    GET  -> show the customer's profile form, pre-filled
    POST -> update full_name, username, and phone
    (email is NOT editable here - it's the login identifier)
    """
    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('home'))

    try:
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            if not validate_csrf_token(request.form.get('csrf_token')):
                flash('Your session expired or this request looked suspicious. Please try again.', 'error')
                return redirect(url_for('customer.profile'))

            full_name = request.form.get('full_name', '').strip()
            username = request.form.get('username', '').strip() or None
            phone = request.form.get('phone', '').strip() or None
            address = request.form.get('address', '').strip() or None
            city = request.form.get('city', '').strip() or None

            if not full_name:
                flash('Full name is required.', 'error')
                return redirect(url_for('customer.profile'))

            if not is_valid_full_name(full_name):
                flash('Please enter a valid full name.', 'error')
                return redirect(url_for('customer.profile'))

            if phone and not is_valid_phone(phone):
                flash('Please enter a valid Pakistani mobile number (e.g. 0301-2345678).', 'error')
                return redirect(url_for('customer.profile'))

            # If a username was entered, make sure nobody else already has it
            if username:
                cursor.execute(
                    "SELECT user_id FROM users WHERE username = %s AND user_id != %s",
                    (username, session['user_id'])
                )
                if cursor.fetchone():
                    cursor.close()
                    flash('That username is already taken. Please choose another.', 'error')
                    return redirect(url_for('customer.profile'))

            cursor.execute(
                "UPDATE users SET full_name = %s, username = %s, phone = %s WHERE user_id = %s",
                (full_name, username, phone, session['user_id'])
            )
            
            # Update customer specific fields (address, city)
            cursor.execute(
                "UPDATE customers SET address = %s, city = %s WHERE user_id = %s",
                (address, city, session['user_id'])
            )
            
            connection.commit()
            cursor.close()

            # Keep the navbar's displayed name in sync immediately
            session['full_name'] = full_name

            flash('Your profile has been updated.', 'success')
            return redirect(url_for('customer.profile'))

        # ---- GET: show the form pre-filled ----
        cursor.execute(
            """SELECT u.full_name, u.email, u.username, u.phone, u.created_at, 
                      c.address, c.city 
               FROM users u
               LEFT JOIN customers c ON u.user_id = c.user_id
               WHERE u.user_id = %s""",
            (session['user_id'],)
        )
        user = cursor.fetchone()
        cursor.close()

        return render_template('customer/profile.html', user=user)

    finally:
        connection.close()


@customer_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Allows a customer to change their password from the profile page.
    """
    if not validate_csrf_token(request.form.get('csrf_token')):
        flash('Your session expired. Please try again.', 'error')
        return redirect(url_for('customer.profile'))

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        flash('Please fill in all password fields.', 'error')
        return redirect(url_for('customer.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('customer.profile'))
        
    password_error = password_strength_error(new_password)
    if password_error:
        flash(password_error, 'error')
        return redirect(url_for('customer.profile'))

    connection = get_db_connection()
    if connection is None:
        flash('Could not connect to the database.', 'error')
        return redirect(url_for('customer.profile'))

    try:
        import bcrypt
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (session['user_id'],))
        user = cursor.fetchone()

        stored_hash = user['password_hash'].encode('utf-8')
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('customer.profile'))

        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, session['user_id']))
        connection.commit()
        cursor.close()

        flash('Your password has been changed successfully.', 'success')

    except Exception as e:
        connection.rollback()
        print(f"Change password error: {e}")
        flash('Something went wrong changing your password.', 'error')
    finally:
        connection.close()

    return redirect(url_for('customer.profile'))


# ============================================================
# REAL-TIME NOTIFICATIONS (polling)
# The navbar's notification bell (base.html) calls this every 30
# seconds via JS to check for updates without a full page reload -
# same idea as the existing prescription badge, just live instead
# of only updating on the next page load. Returns the customer's
# prescription notification count (same logic as the navbar context
# processor) PLUS their active orders' current status, so the
# frontend can detect a status change (e.g. "packed" -> "shipped")
# and show a toast telling the customer to take their next step.
# ============================================================
@customer_bp.route('/api/notifications')
@login_required
def api_notifications():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'prescription_count': 0, 'prescriptions': [], 'orders': []})

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT customer_id FROM customers WHERE user_id = %s", (session['user_id'],))
        customer = cursor.fetchone()
        if not customer:
            return jsonify({'prescription_count': 0, 'prescriptions': [], 'orders': []})

        # Fetch notifications from the new dedicated notifications table
        cursor.execute("""
            SELECT notification_id, title, message, link, icon, is_read, created_at 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT 20
        """, (session['user_id'],))
        notifications = cursor.fetchall()

        unread_count = sum(1 for n in notifications if not n['is_read'])

        # Keep polling active orders to show toast updates
        cursor.execute(
            """SELECT order_id, status FROM orders
               WHERE customer_id = %s AND status != 'delivered'
               ORDER BY order_id DESC LIMIT 10""",
            (customer['customer_id'],)
        )
        orders = cursor.fetchall()

        return jsonify({
            'unread_count': unread_count,
            'notifications': notifications,
            'orders': orders
        })

    except Exception as e:
        print(f"Notifications API error: {e}")
        return jsonify({'prescription_count': 0, 'prescriptions': [], 'orders': []})

    finally:
        connection.close()


# ============================================================
# AI CHATBOT API
# ============================================================

@customer_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """
    AI Chatbot endpoint - accepts a user message and returns an AI response.
    Rate-limited to 15 messages per minute per session.
    No login required so even guest visitors can use it.
    """
    import time
    from utils.ai_chatbot import get_ai_response

    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    image_data = data.get('image_data')  # Base64 string
    mime_type = data.get('mime_type', 'image/jpeg')

    if not user_message and not image_data:
        return jsonify({'error': 'Please type a message or upload an image.'}), 400

    # ---- Input length guard ----
    if len(user_message) > 300:
        return jsonify({'reply': 'Please shorten your message (max 300 characters).'}), 200

    # ---- Rate limiting: max 15 messages per minute per session ----
    now = time.time()
    if 'chat_timestamps' not in session:
        session['chat_timestamps'] = []

    session['chat_timestamps'] = [t for t in session['chat_timestamps'] if now - t < 60]

    if len(session['chat_timestamps']) >= 15:
        return jsonify({'reply': '⚠️ You are sending too many messages. Please wait a moment and try again.'}), 200

    session['chat_timestamps'].append(now)
    session.modified = True

    # ---- Maintain chat history in session for AI context memory ----
    if 'chat_history' not in session:
        session['chat_history'] = []

    chat_history = session['chat_history']

    # ---- Get AI response ----
    try:
        reply = get_ai_response(
            user_message,
            image_data=image_data,
            mime_type=mime_type,
            session_history=chat_history
        )

        # Store turn in history
        if user_message:
            chat_history.append({'role': 'user', 'text': user_message})
        chat_history.append({'role': 'model', 'text': reply})

        # Keep history lightweight (max 6 items)
        session['chat_history'] = chat_history[-6:]
        session.modified = True

        return jsonify({'reply': reply, 'has_image': bool(image_data)})
    except Exception as e:
        print(f"[AI Chat API Error] {e}")
        return jsonify({'reply': 'Sorry, something went wrong processing your request.'}), 200



@customer_bp.route('/api/chat/submit-prescription', methods=['POST'])
def api_chat_submit_prescription():
    """
    Submits an uploaded prescription from the chatbot to the Pharmacist Verification Queue
    only when the customer confirms they want to place an order!
    """
    import base64
    import os
    import time
    from werkzeug.utils import secure_filename

    data = request.get_json(silent=True) or {}
    image_data = data.get('image_data')

    if not image_data:
        return jsonify({'error': 'No prescription image attached.'}), 400

    if 'user_id' not in session:
        return jsonify({'reply': '🔑 Please **Log In** to submit prescriptions for ordering.', 'require_login': True}), 200

    connection = get_db_connection()
    if connection is None:
        return jsonify({'reply': 'Database error. Please try again.'}), 500

    try:
        customer_id = get_customer_id(connection, session['user_id'])
        
        # Save base64 image file to static/uploads/prescriptions/
        upload_folder = os.path.join('static', 'uploads', 'prescriptions')
        os.makedirs(upload_folder, exist_ok=True)

        header, encoded = image_data.split(',', 1) if ',' in image_data else ('', image_data)
        ext = 'png' if 'png' in header else ('pdf' if 'pdf' in header else 'jpg')
        filename = f"chat_rx_{customer_id}_{int(time.time())}.{ext}"
        filepath = os.path.join(upload_folder, filename)

        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(encoded))

        rel_path = f"uploads/prescriptions/{filename}"

        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO prescriptions (customer_id, file_path, status, notes)
               VALUES (%s, %s, 'pending', 'Uploaded via AI Support Chatbot')""",
            (customer_id, rel_path)
        )
        connection.commit()
        cursor.close()

        return jsonify({
            'reply': '✅ **Prescription Sent to Pharmacist!**\n\n'
                     'Our licensed pharmacist has received your prescription and is reviewing it. '
                     'You will receive a notification as soon as it is verified!'
        })

    except Exception as e:
        print(f"[Submit Prescription Chat Error] {e}")
        return jsonify({'reply': 'Failed to submit prescription. Please use the main Upload Prescription page.'}), 200

    finally:
        connection.close()


# ============================================================
# AI PRESCRIPTION SCANNER ROUTES
# ============================================================
import os
import time
from werkzeug.utils import secure_filename
from utils.ai_prescription import analyze_prescription_image

@customer_bp.route('/scan-prescription')
def scan_prescription_page():
    """Renders the AI Prescription Scanner & Analyzer page."""
    return render_template('customer/ai_prescription.html')


@customer_bp.route('/api/ai/scan-prescription', methods=['POST'])
def api_scan_prescription():
    """
    API Endpoint for uploading and analyzing prescription images with Groq Vision AI.
    Handles invalid image detection and automatic file deletion.
    """
    if 'prescription' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded. Please select a prescription image.'}), 400

    file = request.files['prescription']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No image file selected.'}), 400

    # 1. Allowed Extension Check
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    allowed_exts = {'.jpg', '.jpeg', '.png', '.webp'}
    
    if ext not in allowed_exts:
        return jsonify({'success': False, 'error': 'Unsupported file format! Please upload JPG, PNG, or WEBP images.'}), 400

    # 2. File Size Check (Max 5MB)
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > 5 * 1024 * 1024:
        return jsonify({'success': False, 'error': 'File size too large! Maximum image size allowed is 5MB.'}), 400

    # 3. Save temp file for AI analysis
    upload_dir = os.path.join('static', 'uploads', 'prescriptions')
    os.makedirs(upload_dir, exist_ok=True)
    
    unique_filename = f"scan_rx_{int(time.time())}_{secure_filename(filename)}"
    saved_path = os.path.join(upload_dir, unique_filename)
    
    try:
        file.save(saved_path)
    except Exception as e:
        print(f"[Upload Error] {e}")
        return jsonify({'success': False, 'error': 'Failed to save file on server.'}), 500

    # 4. Invoke Groq Vision AI Scanner
    result = analyze_prescription_image(saved_path)

    # Note: If is_prescription was False, analyze_prescription_image has already deleted saved_path!
    return jsonify(result)