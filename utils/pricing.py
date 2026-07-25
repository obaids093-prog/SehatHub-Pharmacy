"""
SehatHub - Pricing Helper Functions
Reusable pricing/calculation logic used across cart, checkout, and orders.
"""

from decimal import Decimal

# Orders at or above this subtotal get free delivery.
# Defined here once so it's easy to change in one place later
# (e.g. if Obaid wants to adjust the free-delivery threshold).
#
# NOTE: these are Decimal, not float/int. MySQL DECIMAL columns come back
# from the database as Python Decimal objects (for exact money math, no
# rounding errors). Decimal can't be directly added to a float
# (e.g. Decimal('10') + 0.0 raises a TypeError), so to keep arithmetic
# consistent everywhere, these constants and the return value below are
# Decimal too.
FREE_DELIVERY_THRESHOLD = Decimal('2000.00')
STANDARD_DELIVERY_CHARGE = Decimal('100.00')


def calculate_delivery_charge(subtotal):
    """
    Returns the delivery charge (as a Decimal) for a given cart/order subtotal.
    Rs. 0 (free) if the subtotal meets the free-delivery threshold,
    otherwise a standard flat charge.
    """
    if subtotal >= FREE_DELIVERY_THRESHOLD:
        return Decimal('0.00')
    return STANDARD_DELIVERY_CHARGE