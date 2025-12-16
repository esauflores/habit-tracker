import sqlite3
from typing import List, Tuple
from contextlib import contextmanager

import os
import sys
import termios
import tty
import select

from datetime import datetime, timedelta


# Constants

WIDTH = 50
DB_PATH = "habits.db"
MAX_MENU_OPTIONS = 5

# Database

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
                    ON DELETE CASCADE
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
        raise sqlite3.IntegrityError("Habit already exists")

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
        raise sqlite3.IntegrityError("Habit already exists")


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
        raise sqlite3.IntegrityError("Record already exists")

def delete_record(record_id: int) -> bool:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,)
        )
        return cursor.rowcount > 0

# Menu

def clear():
    os.system('clear')



def get_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

        if ch == "\x1b": # ESC key
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":  # Up arrow
                    return "UP"
                elif ch3 == "B":  # Down arrow
                    return "DOWN"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def initial_menu():
    options = [
        (1, "Add a new habit"),
        (2, "View habits"),
        (3, "Exit")
    ]


    selected_index = 0
    selected_option = None
    while selected_option is None:
        clear()
        
        texts = [
            "🏡 Habit Tracker",
            "─" * WIDTH,
            " " * WIDTH
        ]

        for textrow in texts:
            print(textrow.center(WIDTH))

    
        for i in range(len(options)):
            if i == selected_index:
                print(" >", options[i][1])
            else:
                print(" ", options[i][1])  

        ch = get_char()
        if ch == "\x1b":  # ESC key
            break
        elif ch == "\r":  # Enter
            selected_option = options[selected_index][0]
        elif ch == "UP":
            selected_index = (selected_index - 1) % len(options)
        elif ch == "DOWN":
            selected_index = (selected_index + 1) % len(options)

    if selected_option == 1:
        add_habit_menu()
    elif selected_option == 2:
        select_habit_menu()
    elif selected_option == 3:
        exit()

def add_habit_menu():
    clear()
    
    texts = [
        "📝 Add a new habit",
        "─" * WIDTH,
        " " * WIDTH,
    ]

    for textrow in texts:
        print(textrow.center(WIDTH))

    habit = input("Enter a new habit: ")
    try:
        create_habit(habit)
        print("Habit added successfully")
    except sqlite3.IntegrityError:
        print("Habit already exists!")
    except Exception as e:
        print(f"Error: {e}")
    input("Press Enter to continue...")
    initial_menu()

def select_habit_menu():
    habits = read_habits()

    if len(habits) == 0:
        print("No habits found!")
        input("Press Enter to continue...")
        initial_menu()
        return
        
    pages = [habits[i:i+MAX_MENU_OPTIONS] for i in range(0, len(habits), MAX_MENU_OPTIONS)]
    pages_count = len(pages)

    current_page = 0
    selected_index = 0
    selected_habit = None

    while selected_habit is None:
        clear()
        texts = [
            "📋 My Habits",
            "─" * WIDTH,
            f"Page {current_page + 1} of {pages_count}".ljust(WIDTH - len("ESC = Back | ENTER = Select")) + "ESC = Back | ENTER = Select",
            " " * WIDTH,
        ]

        for textrow in texts:
            print(textrow.center(WIDTH))

        for i in range(len(pages[current_page])):
            if i == selected_index:
                print(" >", pages[current_page][i][1])
            else:
                print(" ", pages[current_page][i][1])
        ch = get_char()

        if ch == "\x1b":  # ESC key
            initial_menu()
            return
        elif ch == "\r":  # Enter
            selected_habit = pages[current_page][selected_index]
            break
        elif ch == "UP":
            selected_index -= 1
            if selected_index < 0:
                current_page = (current_page - 1) % pages_count
                selected_index = len(pages[current_page]) - 1
        elif ch == "DOWN":
            selected_index += 1
            if selected_index >= len(pages[current_page]):
                current_page = (current_page + 1) % pages_count
                selected_index = 0

    habit_menu(selected_habit)

def habit_menu(habit: Tuple[int, str]):
    options = [
        (1, "Add a new record"),
        (2, "View records"),
        (3, "Delete habit"),
        (4, "Back"),
    ]

    selected_index = 0
    selected_option = None
    while selected_option is None:
        clear()
        
        texts = [
            f"📋 Habit: {habit[1]}",
            "─" * WIDTH,
            " " * WIDTH,
        ]

        for textrow in texts:
            print(textrow.center(WIDTH))

        for i in range(len(options)):
            if i == selected_index:
                print(" >", options[i][1])
            else:
                print(" ", options[i][1])
        ch = get_char()
        if ch == "\x1b":  # ESC key
            break
        elif ch == "\r":  # Enter
            selected_option = options[selected_index][0]
            break
        elif ch == "UP":
            selected_index = (selected_index - 1) % len(options)
        elif ch == "DOWN":
            selected_index = (selected_index + 1) % len(options)

    if selected_option == 1:
        add_record_menu(habit)
    elif selected_option == 2:
        record_menu(habit)
    elif selected_option == 3:
        delete_habit_menu(habit)
    elif selected_option == 4:
        select_habit_menu()
        return

def delete_habit_menu(habit: Tuple[int, str]):
    habit_id = habit[0]
    try:
        delete_habit(habit_id)
        print("Habit deleted successfully")
    except ValueError as e:
        print(f"Error: {e}")
    input("Press Enter to continue...")
    initial_menu()
    return

def add_record_menu(habit: Tuple[int, str]):
    clear()
    
    texts = [
        "📝 Add a new record",
        "─" * WIDTH,
        " " * WIDTH,
    ]

    for textrow in texts:
        print(textrow.center(WIDTH))

    date = input("Enter the date of the record: ")
    try:
        create_record(habit[0], date)
        print("Record added successfully")
    except sqlite3.IntegrityError:
        print("Record already exists!")
    except ValueError as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")

    habit_menu(habit)

# def record_menu(habit: Tuple[int, str]):


if __name__ == "__main__":
    initial_menu()