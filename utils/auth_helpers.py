"""
SehatHub - Authentication Helper Functions
Reusable security helpers used across multiple route files.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    """
    A "decorator" - a special wrapper you place above a route function
    using @login_required. It checks if someone is logged in BEFORE
    letting them access that page.

    WHY we need this: routes like the cart only make sense for a
    logged-in customer (cart_items are tied to a customer_id in the
    database). Without this check, someone who isn't logged in could
    try to view/add to a cart that doesn't belong to them, or crash
    the page because there's no customer_id to use.

    HOW to use it: put @login_required directly above any route
    function that should require login, like this:

        @customer_bp.route('/cart')
        @login_required
        def view_cart():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            # Remember where they were trying to go, so we could send
            # them back there after login (not implemented yet, but
            # the 'next' parameter is ready for that future improvement)
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """
    A "decorator factory" - like login_required, but ALSO checks the
    logged-in user has a specific role (e.g. 'pharmacist', 'admin').

    WHY we need this separate from login_required: pages like the
    Pharmacist Dashboard must only be usable by pharmacist accounts -
    a regular customer who is logged in should NOT be able to just
    type in the URL and see other people's prescriptions/orders.

    HOW to use it: put @role_required('pharmacist') above any route
    that should be pharmacist-only:

        @pharmacist_bp.route('/dashboard')
        @role_required('pharmacist')
        def dashboard():
            ...

    Note: this is a "decorator factory" (a function that RETURNS a
    decorator) rather than a plain decorator, because it needs to
    know WHICH role to check for - that's why it's used with
    parentheses and an argument: @role_required('pharmacist').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'error')
                return redirect(url_for('auth.login', next=request.path))
            if session.get('role') != required_role:
                flash('You do not have permission to view that page.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
