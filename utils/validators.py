"""
SehatHub - Shared input validation helpers.

Centralizes the validation rules used in multiple places (signup,
checkout, profile edit) so they stay consistent - fixing a rule here
fixes it everywhere it's used, instead of having to remember every
route that checks phone numbers or passwords.
"""

import re

# Pakistani mobile numbers: 03XXXXXXXXX (11 digits, starts with 03)
# or +923XXXXXXXXX / 923XXXXXXXXX (international format). We normalize
# by stripping spaces/dashes first so "0301-2345678" still passes.
PHONE_PATTERN = re.compile(r'^(03\d{9}|(\+92|92)3\d{9})$')

# Reasonably strict but not annoying: standard "name@domain.tld" shape
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def is_valid_full_name(name):
    """
    True if `name` looks like an actual name - at least 2 characters,
    and contains at least one letter (blocks someone entering just
    numbers or symbols, e.g. "12345" or "...").
    """
    if not name or len(name.strip()) < 2:
        return False
    if '<' in name or '>' in name:
        return False
    return bool(re.search(r'[A-Za-z]', name))


def is_valid_phone(phone):
    """
    True if `phone` looks like a real Pakistani mobile number.
    Accepts optional spaces/dashes (e.g. "0301-2345678", "0301 2345678").
    """
    if not phone:
        return False
    cleaned = phone.replace(' ', '').replace('-', '')
    return bool(PHONE_PATTERN.match(cleaned))


def is_valid_email(email):
    """
    True if `email` has a plausible email shape. This is a basic
    format check, NOT proof the address exists/receives mail - just
    catches obviously-wrong input like "notanemail" or "a@b".
    """
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


def password_strength_error(password):
    """
    Returns an error message string if the password is too weak, or
    None if it passes. Requires: 8+ characters, at least one uppercase
    letter, one lowercase letter, and one digit.
    """
    if not password or len(password) < 8:
        return 'Password must be at least 8 characters long.'
    if not re.search(r'[A-Z]', password):
        return 'Password must include at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return 'Password must include at least one lowercase letter.'
    if not re.search(r'\d', password):
        return 'Password must include at least one number.'
    return None
