"""
SehatHub - Shared Medicine Management Helpers
Used by BOTH the Admin Module and the Pharmacist Module - Obaid asked
for full medicine CRUD (name, generic, category, brand, price, pack
size, stock, image, OTC/Prescription, description) to be manageable
by either role, not just Admin.

Keeping the actual database logic in ONE shared place (rather than
copy-pasted separately into routes/admin.py and routes/pharmacist.py)
means there's only one version of each query to get right and test -
each portal's routes are thin wrappers that call these functions and
render their own branded template.
"""

from config.database import get_db_connection
import os
import time
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def is_allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_medicine_image(file):
    """
    Saves an uploaded medicine image to static/images/medicines/ with
    a safe, unique filename (same secure_filename + timestamp pattern
    used for prescription uploads), and returns the image_url value
    to store in the database (e.g. 'images/medicines/1720000000_panadol.jpg').
    Returns None if no valid file was given.
    """
    if not file or file.filename == '' or not is_allowed_image_file(file.filename):
        return None

    original_filename = secure_filename(file.filename)
    unique_filename = f"{int(time.time())}_{original_filename}"

    upload_folder = os.path.join('static', 'images', 'medicines')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    return f"images/medicines/{unique_filename}"


def get_categories():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_brands():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT brand_id, name FROM brands ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_or_create_brand(brand_name):
    """
    Looks up a brand/company by name (case-insensitive match, so
    "GSK" and "gsk" are treated as the same company) - if it already
    exists, returns its brand_id; if not, creates it on the spot and
    returns the new brand_id.

    WHY this exists: without it, adding a medicine from a manufacturer
    that isn't in the brands table yet would require going into
    phpMyAdmin and running an INSERT INTO brands query first, before
    the medicine could even be created. This lets Admin/Pharmacist
    type a new company name directly on the Add/Edit Medicine form
    instead.
    """
    connection = get_db_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT brand_id FROM brands WHERE LOWER(name) = LOWER(%s)", (brand_name,))
        existing = cursor.fetchone()
        if existing:
            return existing['brand_id']

        cursor.execute("INSERT INTO brands (name) VALUES (%s)", (brand_name,))
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id
    finally:
        connection.close()


def get_medicines_list(search='', category_id=None, status='active', page=1, per_page=20):
    """
    Returns medicines for the management list page, with brand/category
    names, price range, and total stock across all pack-size variants.

    status: 'active' (default - hides soft-deleted medicines),
            'inactive' (only soft-deleted ones), or 'all'.
    
    Returns a tuple: (medicines_list, total_pages).
    """
    connection = get_db_connection()
    if connection is None:
        return [], 0
    try:
        cursor = connection.cursor(dictionary=True)

        # Build the shared WHERE clause once so COUNT and SELECT stay in sync
        where_clause = " WHERE 1=1"
        params = []

        if status == 'active':
            where_clause += " AND m.is_active = TRUE"
        elif status == 'inactive':
            where_clause += " AND m.is_active = FALSE"

        if search:
            where_clause += " AND (m.name LIKE %s OR m.generic_name LIKE %s)"
            like_term = f"%{search}%"
            params.extend([like_term, like_term])

        if category_id:
            where_clause += " AND m.category_id = %s"
            params.append(category_id)

        # ---- Total count for pagination ----
        cursor.execute(f"""
            SELECT COUNT(DISTINCT m.medicine_id) AS total
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            {where_clause}
        """, tuple(params))
        total_items = cursor.fetchone()['total']
        total_pages = max(1, (total_items + per_page - 1) // per_page)

        # ---- Actual data with LIMIT/OFFSET ----
        offset = (page - 1) * per_page
        query = f"""
            SELECT
                m.medicine_id, m.name, m.type, m.image_url, m.is_active,
                b.name AS brand_name, c.name AS category_name,
                MIN(mv.price) AS min_price, MAX(mv.price) AS max_price,
                COALESCE(SUM(mv.stock_qty), 0) AS total_stock
            FROM medicines m
            LEFT JOIN brands b ON m.brand_id = b.brand_id
            LEFT JOIN categories c ON m.category_id = c.category_id
            LEFT JOIN medicine_variants mv ON m.medicine_id = mv.medicine_id
            {where_clause}
            GROUP BY m.medicine_id, m.name, m.type, m.image_url, m.is_active, b.name, c.name
            ORDER BY m.name ASC
            LIMIT %s OFFSET %s
        """
        full_params = list(params) + [per_page, offset]
        cursor.execute(query, tuple(full_params))
        return cursor.fetchall(), total_pages
    finally:
        connection.close()


def get_medicine_detail(medicine_id):
    """Returns one medicine's full details plus its list of pack-size variants."""
    connection = get_db_connection()
    if connection is None:
        return None, []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT medicine_id, name, generic_name, category_id, brand_id, type,
                   description, usage_info, side_effects, image_url, is_active
            FROM medicines WHERE medicine_id = %s
        """, (medicine_id,))
        medicine = cursor.fetchone()

        if not medicine:
            return None, []

        cursor.execute("""
            SELECT variant_id, pack_size, price, stock_qty
            FROM medicine_variants WHERE medicine_id = %s ORDER BY price ASC
        """, (medicine_id,))
        variants = cursor.fetchall()

        return medicine, variants
    finally:
        connection.close()


def create_medicine(data, image_file=None):
    """
    Creates a new medicine plus its first pack-size variant.
    `data` is a dict with keys: name, generic_name, category_id, brand_id,
    type, description, usage_info, side_effects, pack_size, price, stock_qty.
    Returns (new_medicine_id, error_message). error_message is None on success.
    """
    connection = get_db_connection()
    if connection is None:
        return None, "Could not connect to the database."

    price = data.get('price')
    stock_qty = data.get('stock_qty', 0)
    if price is None or price <= 0:
        return None, "Price must be greater than zero."
    if stock_qty is None or stock_qty < 0:
        return None, "Stock quantity can't be negative."

    try:
        cursor = connection.cursor()

        image_url = save_medicine_image(image_file) if image_file else None

        cursor.execute("""
            INSERT INTO medicines (name, generic_name, category_id, brand_id, type,
                                    description, usage_info, side_effects, image_url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (
            data['name'], data.get('generic_name') or None, data.get('category_id') or None,
            data.get('brand_id') or None, data.get('type', 'OTC'),
            data.get('description') or None, data.get('usage_info') or None,
            data.get('side_effects') or None, image_url
        ))
        new_medicine_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO medicine_variants (medicine_id, pack_size, price, stock_qty)
            VALUES (%s, %s, %s, %s)
        """, (new_medicine_id, data['pack_size'], data['price'], data.get('stock_qty', 0)))

        connection.commit()
        cursor.close()
        return new_medicine_id, None

    except Exception as e:
        connection.rollback()
        print(f"Create medicine error: {e}")
        return None, "Something went wrong creating this medicine."

    finally:
        connection.close()


def update_medicine(medicine_id, data, image_file=None):
    """Updates a medicine's core fields. Image is only replaced if a new file was uploaded."""
    connection = get_db_connection()
    if connection is None:
        return "Could not connect to the database."

    try:
        cursor = connection.cursor()

        new_image_url = save_medicine_image(image_file) if image_file else None

        if new_image_url:
            cursor.execute("""
                UPDATE medicines SET name=%s, generic_name=%s, category_id=%s, brand_id=%s,
                    type=%s, description=%s, usage_info=%s, side_effects=%s, image_url=%s
                WHERE medicine_id=%s
            """, (
                data['name'], data.get('generic_name') or None, data.get('category_id') or None,
                data.get('brand_id') or None, data.get('type', 'OTC'),
                data.get('description') or None, data.get('usage_info') or None,
                data.get('side_effects') or None, new_image_url, medicine_id
            ))
        else:
            cursor.execute("""
                UPDATE medicines SET name=%s, generic_name=%s, category_id=%s, brand_id=%s,
                    type=%s, description=%s, usage_info=%s, side_effects=%s
                WHERE medicine_id=%s
            """, (
                data['name'], data.get('generic_name') or None, data.get('category_id') or None,
                data.get('brand_id') or None, data.get('type', 'OTC'),
                data.get('description') or None, data.get('usage_info') or None,
                data.get('side_effects') or None, medicine_id
            ))

        connection.commit()
        cursor.close()
        return None

    except Exception as e:
        connection.rollback()
        print(f"Update medicine error: {e}")
        return "Something went wrong updating this medicine."

    finally:
        connection.close()


def set_medicine_active(medicine_id, is_active):
    """
    Soft-deletes (or restores) a medicine by flipping is_active, rather
    than a hard DELETE - this preserves order_items/reviews history that
    references this medicine (same reasoning as the Admin Module's user
    deletion: protect historical records). An inactive medicine simply
    stops appearing in the customer-facing catalog (all customer queries
    already filter WHERE is_active = TRUE).
    """
    connection = get_db_connection()
    if connection is None:
        return "Could not connect to the database."
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE medicines SET is_active = %s WHERE medicine_id = %s", (is_active, medicine_id))
        connection.commit()
        cursor.close()
        return None
    except Exception as e:
        connection.rollback()
        print(f"Set medicine active error: {e}")
        return "Something went wrong updating this medicine's status."
    finally:
        connection.close()


def add_variant(medicine_id, pack_size, price, stock_qty):
    if price is None or price <= 0:
        return "Price must be greater than zero."
    if stock_qty is None or stock_qty < 0:
        return "Stock quantity can't be negative."

    connection = get_db_connection()
    if connection is None:
        return "Could not connect to the database."
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO medicine_variants (medicine_id, pack_size, price, stock_qty) VALUES (%s, %s, %s, %s)",
            (medicine_id, pack_size, price, stock_qty)
        )
        connection.commit()
        cursor.close()
        return None
    except Exception as e:
        connection.rollback()
        print(f"Add variant error: {e}")
        return "Something went wrong adding this pack size."
    finally:
        connection.close()


def update_variant(variant_id, pack_size, price, stock_qty):
    if price is None or price <= 0:
        return "Price must be greater than zero."
    if stock_qty is None or stock_qty < 0:
        return "Stock quantity can't be negative."

    connection = get_db_connection()
    if connection is None:
        return "Could not connect to the database."
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE medicine_variants SET pack_size=%s, price=%s, stock_qty=%s WHERE variant_id=%s",
            (pack_size, price, stock_qty, variant_id)
        )
        connection.commit()
        cursor.close()
        return None
    except Exception as e:
        connection.rollback()
        print(f"Update variant error: {e}")
        return "Something went wrong updating this pack size."
    finally:
        connection.close()


def delete_variant(variant_id):
    """
    Hard-deletes a single pack-size variant. Only safe for variants
    that were never actually ordered - if this variant has order_items
    referencing it, the database's foreign key (no cascade on that
    table) will block the delete and we surface a friendly message,
    same pattern as Admin user deletion.
    """
    connection = get_db_connection()
    if connection is None:
        return "Could not connect to the database."
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM medicine_variants WHERE variant_id = %s", (variant_id,))
        connection.commit()
        cursor.close()
        return None
    except Exception as e:
        connection.rollback()
        error_text = str(e).lower()
        if 'foreign key constraint' in error_text or '1451' in error_text:
            return "This pack size has already been ordered by a customer and can't be removed (protects order history)."
        print(f"Delete variant error: {e}")
        return "Something went wrong removing this pack size."
    finally:
        connection.close()