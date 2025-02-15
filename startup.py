import os
import sqlite3
import logging
from database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_database():
    db_path = os.getenv('DATABASE_PATH', '/var/lib/estateai/estateai.db')
    logger.info(f"Checking database at: {db_path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.info("Database directory verified")
        
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error("Users table not found after initialization!")
            raise Exception("Database initialization failed")
        
        logger.info("Database verification complete")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    ensure_database()