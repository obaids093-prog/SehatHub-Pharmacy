"""
SehatHub - Lightweight CSRF Protection

WHY this exists: Flask-WTF (the usual way to get CSRF tokens) isn't
installed in this project yet. Since Obaid specifically asked for
extra security care on the Admin Module - which can create staff
accounts and activate/deactivate any user - we add basic CSRF
protection here rather than skipping it for these particular forms.

WHAT is CSRF, in plain terms: without this protection, if a logged-in
admin visited a malicious website in another browser tab, that site
could secretly submit a form to OUR site (e.g. "deactivate this
admin's own account" or "create a new admin account") using the
admin's already-logged-in session, without the admin ever clicking
anything on our site. A CSRF token stops this because the malicious
site has no way to know/guess the token value.

HOW it works here:
1. Every GET request to an admin page that has a form calls
   generate_csrf_token() - this creates a random token, stores it in
   the admin's own server-side session, and returns it to embed as a
   hidden field in the form.
2. When that form is submitted, validate_csrf_token() checks the
   submitted value against the one stored in the session. They must
   match exactly.
3. Since the attacker's malicious page has no access to read the
   admin's session, it cannot forge a matching token.

NOTE: this is a simplified, single-token-per-session implementation.
A production system would typically use Flask-WTF's per-form tokens
with expiry. This is a reasonable middle ground for a university
project that still meaningfully blocks CSRF attacks.
"""

import secrets
from flask import session


def generate_csrf_token():
    """Returns the current CSRF token for this session, creating one if needed."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token(submitted_token):
    """
    Compares the submitted token against the session's token using a
    constant-time comparison (secrets.compare_digest) - this avoids
    leaking timing information that could theoretically help an
    attacker guess the token character-by-character.
    """
    session_token = session.get('csrf_token')
    if not session_token or not submitted_token:
        return False
    return secrets.compare_digest(session_token, submitted_token)
