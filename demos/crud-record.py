import sqlite3
from typing import List, Tuple
from contextlib import contextmanager

DB_PATH = "habits.db"

@contextmanager
def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _init_db():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit TEXT NOT NULL UNIQUE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date DATE NOT NULL,
                FOREIGN KEY (habit_id) 
                    REFERENCES habits (id) 
                    ON DELETE CASCADE,
                UNIQUE (habit_id, date)
            )
        """)

def create_habit(habit: str) -> int:
    _init_db()
    if not habit or not habit.strip():
        raise ValueError("Habit cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO habits (habit) VALUES (?)",
                (habit.strip(),)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Habit already exists")

def read_habits() -> List[Tuple[int, str, str]]:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit FROM habits ORDER BY habit"
        )
        return [(row['id'], row['habit']) for row in cursor.fetchall()]

def update_habit(habit_id: int, new_habit: str) -> bool:
    _init_db()
    if not new_habit or not new_habit.strip():
        raise ValueError("Habit cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "UPDATE habits SET habit = ? WHERE id = ?",
                (new_habit.strip(), habit_id)
            )
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        raise ValueError("Habit already exists")


def delete_habit(habit_id: int) -> bool:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM habits WHERE id = ?",
            (habit_id,)
        )
        return cursor.rowcount > 0

def create_record(habit_id: int, date: str) -> int:
    _init_db()
    if not date or not date.strip():
        raise ValueError("Date cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO records (habit_id, date) VALUES (?, ?)",
                (habit_id, date.strip())
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Record already exists")

def read_records(habit_id: int) -> List[Tuple[int, str]]:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, date FROM records WHERE habit_id = ? ORDER BY date DESC",
            (habit_id,)
        )
        return [(row['id'], row['date']) for row in cursor.fetchall()]
    
def update_record(record_id: int, date: str) -> bool:
    _init_db()
    if not date or not date.strip():
        raise ValueError("Date cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "UPDATE records SET date = ? WHERE id = ?",
                (date.strip(), record_id)
            )
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        raise ValueError("Record already exists")

def delete_record(record_id: int) -> bool:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,)
        )
        return cursor.rowcount > 0


if __name__ == "__main__":
    _init_db()
    print(create_habit("Running"))
    print(create_habit("Reading"))
    print(create_habit("Meditation"))
    print(create_habit("Morning Run"))
    print(create_habit("Run at Night"))
    print(create_habit("Gym"))
    print(create_habit("Yoga"))
    print(create_habit("Coding"))
    print(read_habits())

    print(create_record(1, "2025-01-01"))
    print(create_record(2, "2025-01-01"))
    print(create_record(2, "2025-01-02"))
    print(create_record(3, "2025-01-01"))
    print(create_record(3, "2025-01-02"))
    print(create_record(3, "2025-01-03"))
    print(read_records(1))
    print(read_records(2))
    print(read_records(3))