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


def get_completed_tasks(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, text, due_date, status
        FROM tasks
        WHERE user_id = ? AND status = 'done'
        ORDER BY created_at
    """, (user_id,))

    tasks = cursor.fetchall()
    conn.close()
    return tasks


def mark_task_done(user_id: int, task_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET status = 'done'
        WHERE id = ? AND user_id = ? AND status = 'active'
    """, (task_id, user_id))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return updated


def delete_task(user_id: int, task_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM tasks
        WHERE id = ? AND user_id = ?
    """, (task_id, user_id))

    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def clear_completed_tasks(user_id: int) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM tasks
        WHERE user_id = ? AND status = 'done'
    """, (user_id,))

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()
    return deleted_count


def update_task(user_id: int, task_id: int, new_text: str, new_due_date: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET text = ?, due_date = ?
        WHERE id = ? AND user_id = ?
    """, (new_text, new_due_date, task_id, user_id))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return updated