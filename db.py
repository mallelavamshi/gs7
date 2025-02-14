import sqlite3

import os

import time



import bcrypt



bcrypt.__about__ = type('obj', (object,), {'__version__': '3.2.0'})

DATABASE_NAME = "estateai.db"



def init_db():

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    

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

    

    c.execute('''CREATE TABLE IF NOT EXISTS reports (

                 report_id INTEGER PRIMARY KEY AUTOINCREMENT,

                 username TEXT NOT NULL,

                 report_path TEXT NOT NULL,

                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    

    conn.commit()

    conn.close()



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



# Rest of the database functions remain the same as previous version

# (create_user, verify_user, get_user_limits, etc.)

def create_user(username: str, email: str, password: str, code: str) -> bool:

    """Create new user with verification code"""

    try:

        # Use bcrypt directly instead of passlib

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Decode to store as string

        hashed_str = hashed.decode('utf-8')  

        

        with sqlite3.connect(DATABASE_NAME) as conn:

            c = conn.cursor()

            c.execute('''INSERT INTO users 

                        (username, email, password_hash, verification_code, code_created_at)

                        VALUES (?, ?, ?, ?, ?)''',

                     (username, email, hashed_str, code, time.time()))

            conn.commit()

        return True

    except sqlite3.IntegrityError as e:

        print(f"Database error: {e}")

        return False





def verify_user(username: str, password: str) -> bool:

    """Verify user credentials"""

    conn = sqlite3.connect(DATABASE_NAME)

    c = conn.cursor()

    c.execute('''SELECT password_hash FROM users 

                 WHERE username = ?''', (username,))

    result = c.fetchone()

    conn.close()

    

    if result:

        # Use checkpw instead of verify

        return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))

    return False



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