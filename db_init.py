import sqlite3
import os

# Database path
DB_PATH = "db/history.db"

# Initialize the database
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create 'jobs' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        keywords TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)

    # Create 'files' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        path TEXT NOT NULL,
        type TEXT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    # Create 'analyzed_features' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyzed_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        features TEXT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    )
    """)

    conn.commit()
    conn.close()

# Main execution
if __name__ == "__main__":
    # Ensure 'db' directory exists
    if not os.path.exists("db"):
        os.makedirs("db")
    
    # Initialize database
    initialize_database()
    print("Database initialized successfully.")
