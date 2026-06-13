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
            calendar_event_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cursor.fetchall()]

    if "calendar_event_id" not in columns:
        cursor.execute("""
            ALTER TABLE tasks
            ADD COLUMN calendar_event_id TEXT
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

    task_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return task_id


def update_calendar_event_id(user_id: int, task_id: int, calendar_event_id: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET calendar_event_id = ?
        WHERE id = ? AND user_id = ?
    """, (calendar_event_id, task_id, user_id))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return updated


def get_task_by_id(user_id: int, task_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, text, due_date, status, calendar_event_id
        FROM tasks
        WHERE id = ? AND user_id = ?
    """, (task_id, user_id))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "text": row[2],
        "due_date": row[3],
        "status": row[4],
        "calendar_event_id": row[5],
    }


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


def get_completed_tasks_with_calendar_ids(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, text, due_date, status, calendar_event_id
        FROM tasks
        WHERE user_id = ? AND status = 'done'
        ORDER BY created_at
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "text": row[2],
            "due_date": row[3],
            "status": row[4],
            "calendar_event_id": row[5],
        }
        for row in rows
    ]


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