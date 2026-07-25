"""
SehatHub - Database Connection Configuration
This file handles connecting our Flask app to the MySQL database.
We never write database passwords directly here - they come from the .env file.
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Creates and returns a new connection to the MySQL database.
    Call this function whenever a route needs to talk to the database.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'sehathub_db')
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None
