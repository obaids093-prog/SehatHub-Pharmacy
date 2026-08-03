"""
Audit logging utility for tracking critical actions in SehatHub.
"""

from config.database import get_db_connection

def log_audit_action(user_id, action_type, description):
    """
    Logs an action to the audit_logs table.
    
    Args:
        user_id (int): The ID of the user performing the action.
        action_type (str): Short code for the action (e.g., 'UPDATE_PRICE', 'DELETE_MEDICINE').
        description (str): Detailed description of what was changed (old value vs new value).
    """
    connection = get_db_connection()
    if not connection:
        print("Audit Log Failed: Could not connect to database.")
        return
        
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO audit_logs (user_id, action_type, description)
               VALUES (%s, %s, %s)""",
            (user_id, action_type, description)
        )
        connection.commit()
    except Exception as e:
        print(f"Error saving audit log: {e}")
    finally:
        cursor.close()
        connection.close()
