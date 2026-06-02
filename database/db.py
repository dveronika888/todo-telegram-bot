import sqlite3


DB_NAME = "tasks.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_task(user_id: int, text: str, due_date: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (user_id, text, due_date)
        VALUES (?, ?, ?)
    """, (user_id, text, due_date))

    conn.commit()
    conn.close()


def get_user_tasks(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, text, due_date, status
        FROM tasks
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at
    """, (user_id,))

    tasks = cursor.fetchall()
    conn.close()

    return tasks