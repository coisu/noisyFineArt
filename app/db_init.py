import sqlite3

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect("db/history.db")  # DB 파일 경로
    cursor = conn.cursor()

    # 작업 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            keywords TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # 파일 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            type TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
