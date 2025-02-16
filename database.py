import sqlite3
import os
import time
import bcrypt
import logging
import re
from typing import Dict, Union
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bcrypt.__about__ = type('obj', (object,), {'__version__': '3.2.0'})
DATABASE_NAME = os.getenv('DATABASE_PATH', '/var/lib/estateai/estateai.db')

def wait_for_database():
    """Wait for database file to become available"""
    max_attempts = 30
    attempt = 0
    while attempt < max_attempts:
        if os.path.exists(os.path.dirname(DATABASE_NAME)):
            return True
        logger.info(f"Waiting for database directory... Attempt {attempt + 1}/{max_attempts}")
        time.sleep(1)
        attempt += 1
    return False

def init_db():
    """Initialize database with retry logic"""
    if not wait_for_database():
        raise Exception("Database directory not available")

    logger.info(f"Initializing database at: {DATABASE_NAME}")
    
    try:
        os.makedirs(os.path.dirname(DATABASE_NAME), exist_ok=True)
        
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        
        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE NOT NULL,
                     email TEXT UNIQUE NOT NULL,
                     password_hash TEXT NOT NULL,
                     role TEXT DEFAULT 'user',
                     max_images INTEGER DEFAULT 100,
                     processed_images INTEGER DEFAULT 0,
                     verified INTEGER DEFAULT 0,
                     verification_code TEXT,
                     code_created_at REAL,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create reports table
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
                     report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT NOT NULL,
                     report_path TEXT NOT NULL,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
        # Verify tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        logger.info(f"Available tables: {tables}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

# Rest of the database.py code remains the same...



def save_report(username: str, report_path: str):

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''INSERT INTO reports (username, report_path)

                 VALUES (?, ?)''', (username, report_path))

    conn.commit()

    conn.close()



def get_user_reports(username: str):

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''SELECT report_path, created_at FROM reports 

                 WHERE username = ? ORDER BY created_at DESC''', (username,))

    reports = c.fetchall()

    conn.close()

    return reports

def validate_password(password: str) -> Dict[str, bool]:
    """
    Validate password against security requirements
    Returns a dictionary of validation results
    """
    return {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'number': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*]', password))
    }

def create_user(username: str, email: str, password: str, code: str) -> Union[bool, str]:
    """
    Create new user with validation
    Returns True if successful, error message string if validation fails
    """
    try:
        # Validate password requirements
        password_checks = validate_password(password)
        
        if not all(password_checks.values()):
            # Construct error message based on which requirements failed
            errors = []
            if not password_checks['length']:
                errors.append("Password must be at least 8 characters long")
            if not password_checks['uppercase']:
                errors.append("Password must contain at least one uppercase letter")
            if not password_checks['number']:
                errors.append("Password must contain at least one number")
            if not password_checks['special']:
                errors.append("Password must contain at least one special character")
            return ", ".join(errors)

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email format"

        # If all validations pass, hash and store the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed.decode('utf-8')

        with sqlite3.connect(DATABASE_NAME) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO users 
                        (username, email, password_hash, verification_code, code_created_at)
                        VALUES (?, ?, ?, ?, ?)''',
                     (username, email, hashed_str, code, time.time()))
            conn.commit()
        return True

    except sqlite3.IntegrityError:
        return "Username or email already exists"
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return "An error occurred while creating the user"


def verify_user(username: str, password: str) -> bool:
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error in verify_user: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def create_test_user():
    """Create a test user if no users exist"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create test user with bcrypt hashed password
            password = "admin123"  # Default password
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, verified)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin@example.com', hashed.decode('utf-8'), 'admin', 1))
            
            conn.commit()
            logger.info("Created test admin user")
            
    except sqlite3.Error as e:
        logger.error(f"Error creating test user: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()



def get_user_limits(username: str) -> tuple:

    """Get user's processing limits"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''SELECT processed_images, max_images 

                 FROM users WHERE username = ?''', (username,))

    result = c.fetchone()

    conn.close()

    return (result[0], result[1]) if result else (0, 100)



def increment_image_count(username: str, amount: int) -> bool:

    """Increment user's processed image count"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''UPDATE users 

                 SET processed_images = processed_images + ? 

                 WHERE username = ?''', (amount, username))

    conn.commit()

    success = c.rowcount > 0

    conn.close()

    return success



def delete_user(user_id: int) -> bool:

    """Delete a user by ID"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))

    conn.commit()

    success = c.rowcount > 0

    conn.close()

    return success



def get_all_users() -> list:

    """Get all users for admin view"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''SELECT user_id, username, email, role, max_images, processed_images 

                 FROM users''')

    users = c.fetchall()

    conn.close()

    return users



def update_user_limit(user_id: int, new_limit: int) -> bool:

    """Update user's image processing limit"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''UPDATE users 

                 SET max_images = ? 

                 WHERE user_id = ?''', (new_limit, user_id))

    conn.commit()

    success = c.rowcount > 0

    conn.close()

    return success



def is_admin(username: str) -> bool:

    """Check if user has admin role"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('SELECT role FROM users WHERE username = ?', (username,))

    result = c.fetchone()

    conn.close()

    return result[0] == 'admin' if result else False