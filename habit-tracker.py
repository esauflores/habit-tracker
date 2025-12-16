import sqlite3
from typing import List, Tuple
from contextlib import contextmanager

import os
import sys
import termios
import tty

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
                    ON DELETE CASCADE,
                UNIQUE (habit_id, date)
            )
        """)

def create_habit(habit_text: str) -> Tuple[int, str]:
    _init_db()
    
    if not habit_text or not habit_text.strip():
        raise ValueError("Habit cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO habits (habit) VALUES (?)",
                (habit_text.strip(),)
            )
            return (cursor.lastrowid, habit_text.strip())
    except sqlite3.IntegrityError:
        raise sqlite3.IntegrityError("Habit already exists")

def find_habit_by_name(habit_text: str) -> Tuple[int, str]:
    _init_db()

    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit FROM habits WHERE habit = ?",
            (habit_text.strip(),)
        )
        result = cursor.fetchone()
        if result:
            return (result['id'], result['habit'])
        else:
            raise ValueError("Habit not found")

def find_habit_by_id(habit_id: int) -> Tuple[int, str]:
    _init_db()

    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit FROM habits WHERE id = ?",
            (habit_id,)
        )
        result = cursor.fetchone()
        if result:
            return (result['id'], result['habit'])
        else:
            raise ValueError("Habit not found")

def read_habits() -> List[Tuple[int, str]]:
    _init_db()

    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit FROM habits ORDER BY habit"
        )
        return [(row['id'], row['habit']) for row in cursor.fetchall()]

def find_record_by_date(habit: Tuple[int, str], date: str) -> Tuple[int, int, str]:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit_id, date FROM records WHERE habit_id = ? AND date = ?",
            (habit[0], date.strip())
        )
        result = cursor.fetchone()
        if result:
            return (result['id'], result['habit_id'], result['date'])
        else:
            raise ValueError("Record not found")


def update_habit(habit: Tuple[int, str], new_habit: str) -> Tuple[int, str]:
    _init_db()

    if not new_habit or not new_habit.strip():
        raise ValueError("Habit cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "UPDATE habits SET habit = ? WHERE id = ? RETURNING *",
                (new_habit.strip(), habit[0])
            )
            result = cursor.fetchone()
            return (result['id'], result['habit'])
    except sqlite3.IntegrityError:
        raise sqlite3.IntegrityError("Habit already exists")


def delete_habit(habit: Tuple[int, str]) -> Tuple[int, str]:
    _init_db()

    habit = find_habit_by_id(habit[0])
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM habits WHERE id = ? RETURNING *",
            (habit[0],)
        )
        result = cursor.fetchone()
        return (result['id'], result['habit'])

def create_record(habit: Tuple[int, str], date: str) -> Tuple[int, int, str]:
    _init_db()

    if not date or not date.strip():
        raise ValueError("Date cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO records (habit_id, date) VALUES (?, ?) RETURNING *",
                (habit[0], date.strip())
            )
            result = cursor.fetchone()
            return (result['id'], result['habit_id'], result['date'])
    except sqlite3.IntegrityError:
        raise sqlite3.IntegrityError("Record already exists")

def read_records(habit: Tuple[int, str]) -> List[Tuple[int, int, str]]:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, habit_id, date FROM records WHERE habit_id = ? ORDER BY date DESC",
            (habit[0],)
        )
        return [(row['id'], row['habit_id'], row['date']) for row in cursor.fetchall()]
    
def update_record(record: Tuple[int, int, str], date: str) -> Tuple[int, int, str]:
    _init_db()
    if not date or not date.strip():
        raise ValueError("Date cannot be empty")
    
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "UPDATE records SET date = ? WHERE id = ? RETURNING *",
                (date.strip(), record[0])
            )
            result = cursor.fetchone()
            return (result['id'], result['habit_id'], result['date'])
    except sqlite3.IntegrityError:
        raise sqlite3.IntegrityError("Record already exists")

def delete_record(record: Tuple[int, int, str]) -> Tuple[int, int, str]:
    _init_db()
    with _get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM records WHERE id = ? RETURNING *",
            (record[0],)
        )
        result = cursor.fetchone()
        return (result['id'], result['habit_id'], result['date'])

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

    habit_text = input("Enter a new habit: ")
    habit = None

    try:
        habit = create_habit(habit_text)
        print("Habit added successfully")
    except sqlite3.IntegrityError:
        print("Habit already exists!")
        habit = find_habit_by_name(habit_text)
    except Exception as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")

    if habit is None:
        initial_menu()
        return
    
    habit_menu(habit)

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

    if selected_habit is None:
        initial_menu()
        return

    habit_menu(selected_habit)

def habit_menu(habit: Tuple[int, str]):
    options = [
        (1, "Add a new record"),
        (2, "View records"),
        (3, "Update habit"),
        (4, "Delete habit"),
        (6, "Back"),
    ]

    selected_index = 0
    selected_option = None
    longest_streak = check_longest_streak(habit)

    while selected_option is None:
        clear()
        
        texts = [
            f"📋 Habit: {habit[1]}",
            f"Longest streak: {longest_streak} days",
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
        select_record_menu(habit)
    elif selected_option == 3:
        update_habit_menu(habit)
    elif selected_option == 4:
        delete_habit_menu(habit)
    else:
        select_habit_menu()


def check_longest_streak(habit: Tuple[int, str]) -> int:
    records = read_records(habit)

    if len(records) == 0:
        return 0

    parsed_records = []
    for record in records:
        parsed_records.append(datetime.strptime(record[2], "%Y-%m-%d").date())

    parsed_records = sorted(parsed_records)

    longest_streak = 0
    current_streak = 1
    for i in range(1, len(parsed_records)):
        if parsed_records[i] - parsed_records[i-1] == timedelta(days=1):
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1
    
    longest_streak = max(longest_streak, current_streak)
    
    return longest_streak

def update_habit_menu(habit: Tuple[int, str]):
    clear()

    texts = [
        f"📋 Update Habit: {habit[1]}",
        "─" * WIDTH,
        " " * WIDTH,
    ]
    for textrow in texts:
        print(textrow.center(WIDTH))

    new_habit = input("Enter the new name of the habit: ")

    try:
        habit = update_habit(habit, new_habit)
        print("Habit updated successfully")
    except sqlite3.IntegrityError:
        print("Habit already exists!")
    except ValueError as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")

    habit_menu(habit)
    return

    

def delete_habit_menu(habit: Tuple[int, str]):
    try:
        delete_habit(habit)
        print("Habit deleted successfully")
    except ValueError as e:
        print(f"Error: {e}")
    input("Press Enter to continue...")

    select_habit_menu()

def add_record_menu(habit: Tuple[int, str]):
    clear()
    
    texts = [
        "📝 Add a new record",
        "─" * WIDTH,
        " " * WIDTH,
    ]

    for textrow in texts:
        print(textrow.center(WIDTH))

    record = None
    date = input("Enter the date of the record (YYYY-MM-DD): \n")

    # validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format! Please use the format YYYY-MM-DD")
        input("Press Enter to continue...")
        add_record_menu(habit)
        return

    try:
        record = create_record(habit, date)
        print("Record added successfully")
    except sqlite3.IntegrityError:
        record = find_record_by_date(habit, date)
        print("Record already exists!")
    except ValueError as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")

    if record is None:
        habit_menu(habit)
        return

    record_menu(habit, record)

def select_record_menu(habit: Tuple[int, str]):
    records = read_records(habit)

    if len(records) == 0:
        print("No records found!")
        input("Press Enter to continue...")
        habit_menu(habit)
        return
    
    pages = [records[i:i+MAX_MENU_OPTIONS] for i in range(0, len(records), MAX_MENU_OPTIONS)]
    pages_count = len(pages)

    current_page = 0
    selected_index = 0
    selected_record = None

    while selected_record is None:
        clear()

        texts = [
            f"📋 Records: {habit[1]}",
            "─" * WIDTH,
            f"Page {current_page + 1} of {pages_count}".ljust(WIDTH - len("ESC = Back | ENTER = Select")) + "ESC = Back | ENTER = Select",
            " " * WIDTH,
        ]

        for textrow in texts:
            print(textrow.center(WIDTH))

        for i in range(len(pages[current_page])):
            if i == selected_index:
                print(" >", pages[current_page][i][2])
            else:
                print(" ", pages[current_page][i][2])
        ch = get_char()

        if ch == "\x1b":  # ESC key
            break
        elif ch == "\r":  # Enter
            selected_record = pages[current_page][selected_index]
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

    if selected_record is None:
        habit_menu(habit)
        return

    record_menu(habit, selected_record)

def record_menu(habit: Tuple[int, str], record: Tuple[int, int, str]):
    options = [
        (1, "Update record"),
        (2, "Delete record"),
        (3, "Back"),
    ]

    selected_index = 0
    selected_option = None

    while selected_option is None:
        clear()

        texts = [
            f"📋 Record: {habit[1]} - {record[2]}",
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

        if ch == "\r":  # Enter
            selected_option = options[selected_index][0]
            break
        elif ch == "UP":
            selected_index = (selected_index - 1) % len(options)
        elif ch == "DOWN":
            selected_index = (selected_index + 1) % len(options)

    if selected_option == 1:
        update_record_menu(habit, record)
    elif selected_option == 2:
        delete_record_menu(habit, record)
    else:
        select_record_menu(habit)

def update_record_menu(habit: Tuple[int, str], record: Tuple[int, int, str]):
    clear()

    texts = [
        f"📋 Update Record: {habit[1]} - {record[2]}",
        "─" * WIDTH,
        " " * WIDTH,
    ]
    
    for textrow in texts:
        print(textrow.center(WIDTH))

    date = input("Enter the new date of the record (YYYY-MM-DD): \n")
    
    # validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format! Please use the format YYYY-MM-DD")
        input("Press Enter to continue...")
        update_record_menu(habit, record)
        return

    try:
        record = update_record(record, date)
        print("Record updated successfully")
    except sqlite3.IntegrityError:
        print("Record already exists!")
    except ValueError as e:
        print(f"Error: {e}")    

    input("Press Enter to continue...")


    record_menu(habit, record)  

def delete_record_menu(habit: Tuple[int, str], record: Tuple[int, int, str]):
    clear()
    texts = [
        f"📋 Delete Record: {habit[1]} - {record[2]}",
        "─" * WIDTH,
        " " * WIDTH,
    ]

    for textrow in texts:
        print(textrow.center(WIDTH))

    try:
        delete_record(record)
        print("Record deleted successfully")
    except ValueError as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")
    
    select_record_menu(habit)

if __name__ == "__main__":
    initial_menu()