"""
SehatHub - Simple in-memory rate limiter for login attempts.

Protects against brute-force password guessing: after too many failed
login attempts from the same IP address within a short time window,
further login attempts from that IP are blocked for a cool-down period.

NOTE: this is intentionally a plain in-process dictionary (no Redis, no
database table) since the app runs as a single Flask process for this
project. If this were ever deployed across multiple processes/servers,
this state would need to live somewhere shared (e.g. Redis) instead -
each process would otherwise track its own separate attempt counts.
"""

import time

MAX_FAILED_ATTEMPTS = 5       # attempts allowed...
WINDOW_SECONDS = 15 * 60      # ...within this many seconds (15 min)...
LOCKOUT_SECONDS = 15 * 60     # ...before being locked out for this long (15 min)

# { ip_address: [timestamp1, timestamp2, ...] } - only FAILED attempts
# are recorded here. Successful logins clear the IP's entry entirely.
_failed_attempts = {}


def is_locked_out(ip_address):
    """
    Checks whether this IP address is currently locked out from logging
    in due to too many recent failed attempts.

    Returns a tuple: (locked_out: bool, seconds_remaining: int)
    """
    now = time.time()
    attempts = _failed_attempts.get(ip_address, [])

    # Drop attempts older than the tracking window - they no longer count
    # towards the limit (e.g. 3 failed attempts an hour ago don't combine
    # with 2 failed attempts just now to trigger a lockout).
    attempts = [t for t in attempts if now - t < WINDOW_SECONDS]
    _failed_attempts[ip_address] = attempts

    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        most_recent_attempt = attempts[-1]
        seconds_remaining = int(LOCKOUT_SECONDS - (now - most_recent_attempt))
        if seconds_remaining > 0:
            return True, seconds_remaining
        # Lockout period has fully passed - clear it so they get a fresh start
        _failed_attempts[ip_address] = []

    return False, 0


def record_failed_attempt(ip_address):
    """Call this every time a login attempt fails (wrong email or password)."""
    _failed_attempts.setdefault(ip_address, []).append(time.time())


def clear_attempts(ip_address):
    """Call this on a SUCCESSFUL login to reset the counter for that IP."""
    _failed_attempts.pop(ip_address, None)
