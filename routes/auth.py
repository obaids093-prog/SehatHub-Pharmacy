"""
SehatHub - Authentication Routes
Handles signup, login, and logout.

This file uses a Flask "Blueprint" - a way to organize routes into
separate files instead of cramming everything into app.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt
import secrets
from datetime import datetime, timedelta
from config.database import get_db_connection
from utils.csrf import validate_csrf_token
from utils.rate_limit import is_locked_out, record_failed_attempt, clear_attempts
from utils.validators import is_valid_phone, is_valid_email, password_strength_error, is_valid_full_name

# Create a Blueprint named "auth". The url_prefix means every route
# in this file automatically starts with /auth (e.g. /auth/signup)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET  -> just show the empty signup form
    POST -> form was submitted, validate and save the new customer
    """

    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return render_template('auth/signup.html')

        # ----------------------------------------------------------
        # STEP 0: Spam-signup protection - block this IP if it has
        # submitted too many signup attempts recently (see
        # utils/rate_limit.py). Unlike login, we count EVERY attempt
        # here (not just failed ones) since the goal is limiting how
        # many accounts one IP can create in a short time, not just
        # catching wrong passwords. The "signup:" prefix keeps this
        # counter completely separate from the login rate limiter.
        # ----------------------------------------------------------
        ip_address = request.remote_addr
        signup_key = f'signup:{ip_address}'
        locked_out, seconds_remaining = is_locked_out(signup_key)
        if locked_out:
            minutes_remaining = max(1, seconds_remaining // 60)
            flash(f'Too many signup attempts from this connection. Please try again in {minutes_remaining} minute(s).', 'error')
            return render_template('auth/signup.html')
        record_failed_attempt(signup_key)

        # ----------------------------------------------------------
        # STEP 1: Get the data the user typed into the form
        # ----------------------------------------------------------
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # ----------------------------------------------------------
        # STEP 2: Validate the data (basic server-side checks)
        # We NEVER trust the frontend alone - someone could bypass
        # the HTML form and send bad data directly to this route.
        # ----------------------------------------------------------
        if not full_name or not email or not phone or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/signup.html')

        if not is_valid_full_name(full_name):
            flash('Please enter your full name.', 'error')
            return render_template('auth/signup.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/signup.html')

        if not is_valid_phone(phone):
            flash('Please enter a valid Pakistani mobile number (e.g. 0301-2345678).', 'error')
            return render_template('auth/signup.html')

        password_error = password_strength_error(password)
        if password_error:
            flash(password_error, 'error')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('auth/signup.html')

        connection = get_db_connection()
        if connection is None:
            flash('Something went wrong connecting to the database. Please try again.', 'error')
            return render_template('auth/signup.html')

        cursor = connection.cursor()

        try:
            # ----------------------------------------------------------
            # STEP 3: Check if this email is already registered
            # ----------------------------------------------------------
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('An account with this email already exists. Please log in instead.', 'error')
                return render_template('auth/signup.html')

            # ----------------------------------------------------------
            # STEP 4: Hash the password using bcrypt
            # WHY: We never store plain-text passwords. If our database
            # were ever leaked, bcrypt-hashed passwords are extremely
            # hard to reverse, protecting our users' accounts.
            # ----------------------------------------------------------
            password_bytes = password.encode('utf-8')
            hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            # Store as a string in the database (bcrypt gives us bytes)
            hashed_password_str = hashed_password.decode('utf-8')

            # ----------------------------------------------------------
            # STEP 5: Insert into the `users` table first
            # role is hard-coded to 'customer' - public signup can ONLY
            # create customer accounts (pharmacist/admin/delivery accounts
            # are added directly to the database by us, never through
            # this public form - this is a security decision).
            # ----------------------------------------------------------
            cursor.execute(
                """INSERT INTO users (full_name, email, password_hash, phone, role)
                   VALUES (%s, %s, %s, %s, 'customer')""",
                (full_name, email, hashed_password_str, phone)
            )

            # Get the user_id that was just generated, so we can link
            # the customers table row to it
            new_user_id = cursor.lastrowid

            # ----------------------------------------------------------
            # STEP 6: Insert into the `customers` table
            # address/city are left empty for now - they get filled in
            # later at checkout time, not at signup (per Obaid's UX call)
            # ----------------------------------------------------------
            cursor.execute(
                """INSERT INTO customers (user_id, address, city)
                   VALUES (%s, NULL, NULL)""",
                (new_user_id,)
            )

            # Commit = actually save these changes permanently to the database
            connection.commit()

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            # If anything went wrong, undo any partial changes
            connection.rollback()
            print(f"Signup error: {e}")  # shows in terminal for debugging
            flash('Something went wrong creating your account. Please try again.', 'error')
            return render_template('auth/signup.html')

        finally:
            # Always close the database connection when we're done with it
            cursor.close()
            connection.close()

    # If it's just a GET request (user is visiting the page normally),
    # show the empty signup form
    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  -> just show the empty login form
    POST -> form was submitted, verify credentials and log the user in
    """

    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return render_template('auth/login.html')

        # ----------------------------------------------------------
        # STEP 0: Brute-force protection - block this IP if it has
        # failed too many login attempts recently (see utils/rate_limit.py)
        # ----------------------------------------------------------
        ip_address = request.remote_addr
        locked_out, seconds_remaining = is_locked_out(ip_address)
        if locked_out:
            minutes_remaining = max(1, seconds_remaining // 60)
            flash(f'Too many failed login attempts. Please try again in {minutes_remaining} minute(s).', 'error')
            return render_template('auth/login.html')

        # ----------------------------------------------------------
        # STEP 1: Get the data the user typed into the form
        # ----------------------------------------------------------
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')

        connection = get_db_connection()
        if connection is None:
            flash('Something went wrong connecting to the database. Please try again.', 'error')
            return render_template('auth/login.html')

        cursor = connection.cursor(dictionary=True)

        try:
            # ----------------------------------------------------------
            # STEP 2: Look up the user by email
            # ----------------------------------------------------------
            cursor.execute(
                "SELECT user_id, full_name, password_hash, role FROM users WHERE email = %s OR username = %s",
                (email, email)
            )
            user = cursor.fetchone()

            # ----------------------------------------------------------
            # STEP 3: Verify the password
            # We use the SAME generic error message whether the email
            # doesn't exist OR the password is wrong. This is a security
            # best practice - it stops attackers from being able to guess
            # which emails are registered in our system.
            # ----------------------------------------------------------
            if user is None:
                record_failed_attempt(ip_address)
                flash('Incorrect email or password.', 'error')
                return render_template('auth/login.html')

            stored_hash = user['password_hash'].encode('utf-8')
            submitted_password = password.encode('utf-8')

            if not bcrypt.checkpw(submitted_password, stored_hash):
                record_failed_attempt(ip_address)
                flash('Incorrect email or password.', 'error')
                return render_template('auth/login.html')

            # ----------------------------------------------------------
            # STEP 4: Password is correct - create the session
            # WHY: HTTP is "stateless" - the server forgets who you are
            # after every request. The session stores a few small pieces
            # of info in a secure, signed cookie in the user's browser,
            # so every future page request can check "is this person
            # logged in, and what role do they have?"
            # ----------------------------------------------------------
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']

            # "Remember Me" checkbox: if checked, make the session
            # PERMANENT (survives closing the browser, lasts as long as
            # PERMANENT_SESSION_LIFETIME below). If unchecked, leave it
            # as a normal session cookie that clears when the browser closes.
            session.permanent = bool(request.form.get('remember'))

            # Successful login - this IP is no longer under suspicion
            clear_attempts(ip_address)

            flash(f"Welcome back, {user['full_name']}!", 'success')

            # Send pharmacist/admin accounts to their own dashboards
            # instead of the customer-facing homepage
            if user['role'] == 'pharmacist':
                return redirect(url_for('pharmacist.dashboard'))
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            if user['role'] == 'delivery':
                return redirect(url_for('delivery.dashboard'))

            return redirect(url_for('home'))

        except Exception as e:
            print(f"Login error: {e}")  # shows in terminal for debugging
            flash('Something went wrong while logging in. Please try again.', 'error')
            return render_template('auth/login.html')

        finally:
            cursor.close()
            connection.close()

    # GET request - just show the empty login form
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Clears the session, logging the user out.
    """
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# ============================================================
# FORGOT PASSWORD
# Standard token-based reset flow (the same mechanism real sites
# use): a random, single-use token is generated and stored on the
# user's row with a 30-minute expiry. In a live deployment with an
# email service configured, this token would be emailed as a link.
# We don't have a domain/email service set up for this project, so
# the reset link is shown directly on screen instead - the rest of
# the security mechanism (random token, expiry, single-use) is the
# same either way.
# ============================================================
RESET_TOKEN_VALID_MINUTES = 30


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if not validate_csrf_token(request.form.get('csrf_token')):
            flash('Your session expired or this request looked suspicious. Please try again.', 'error')
            return render_template('auth/forgot_password.html')

        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')

        connection = get_db_connection()
        if connection is None:
            flash('Something went wrong connecting to the database. Please try again.', 'error')
            return render_template('auth/forgot_password.html')

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            # We only actually generate/show a link if the email exists,
            # but we DON'T say "email not found" in the flash message -
            # that would let someone probe which emails are registered.
            # The confirmation screen looks the same either way.
            reset_link = None
            if user:
                token = secrets.token_urlsafe(32)
                expiry = datetime.now() + timedelta(minutes=RESET_TOKEN_VALID_MINUTES)
                cursor.execute(
                    "UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE user_id = %s",
                    (token, expiry, user['user_id'])
                )
                connection.commit()
                reset_link = url_for('auth.reset_password', token=token, _external=True)

            cursor.close()
            return render_template('auth/forgot_password.html', reset_link=reset_link, submitted=True)

        except Exception as e:
            connection.rollback()
            print(f"Forgot password error: {e}")
            flash('Something went wrong. Please try again.', 'error')
            return render_template('auth/forgot_password.html')

        finally:
            connection.close()

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    connection = get_db_connection()
    if connection is None:
        flash('Something went wrong connecting to the database. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, reset_token_expiry FROM users WHERE reset_token = %s",
            (token,)
        )
        user = cursor.fetchone()

        if not user or user['reset_token_expiry'] < datetime.now():
            cursor.close()
            flash('This reset link is invalid or has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))

        if request.method == 'POST':
            if not validate_csrf_token(request.form.get('csrf_token')):
                cursor.close()
                flash('Your session expired or this request looked suspicious. Please try again.', 'error')
                return render_template('auth/reset_password.html', token=token)

            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            password_error = password_strength_error(password)
            if password_error:
                cursor.close()
                flash(password_error, 'error')
                return render_template('auth/reset_password.html', token=token)

            if password != confirm_password:
                cursor.close()
                flash('Passwords do not match. Please try again.', 'error')
                return render_template('auth/reset_password.html', token=token)

            new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Clear the token so it can't be reused (single-use link)
            cursor.execute(
                "UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expiry = NULL WHERE user_id = %s",
                (new_hash, user['user_id'])
            )
            connection.commit()
            cursor.close()

            flash('Your password has been reset. Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))

        cursor.close()
        return render_template('auth/reset_password.html', token=token)

    except Exception as e:
        connection.rollback()
        print(f"Reset password error: {e}")
        flash('Something went wrong. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    finally:
        connection.close()