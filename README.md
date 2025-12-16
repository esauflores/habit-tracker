# 🏡 Habit Tracker

A simple, terminal-based habit tracking application built with Python and SQLite.

## ✨ Features

- **Habit Management**: Create, update, and delete habits
- **Daily Records**: Track when you complete your habits
- **Streak Tracking**: Automatically calculates your longest streak
- **Intuitive Navigation**: Arrow-key based menu system
- **Persistent Storage**: SQLite database for reliable data storage

## 📋 Requirements

- Python 3.7+
- Unix-like terminal (Linux, macOS) with `termios` support
- SQLite3 (comes with Python)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/esauflores/habit-tracker.git
cd habit-tracker
```

2. (Optional) Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Run the application:
```bash
python3 habit_tracker.py
```

## 🎮 Usage

### Navigation
- **Arrow Keys** (↑/↓): Navigate menu options
- **Enter**: Select an option
- **ESC**: Go back to previous menu

### Quick Start

1. **Add a Habit**: From the main menu, select "Add a new habit"
2. **Add Records**: Select a habit, then "Add a new record"
3. **Track Progress**: View your longest streak on the habit menu
4. **View History**: Select "View records" to see all completion dates

### Date Format
All dates must be in `YYYY-MM-DD` format (e.g., `2024-12-16`)

## 📁 Project Structure

```
habit-tracker/
├── habit_tracker.py    # Main application
├── habits.db          # SQLite database (created on first run)
├── .gitignore
└── README.md
```

## 🗄️ Database Schema

### habits
| Column | Type    | Description           |
|--------|---------|----------------------|
| id     | INTEGER | Primary key          |
| habit  | TEXT    | Habit name (unique)  |

### records
| Column   | Type    | Description                    |
|----------|---------|--------------------------------|
| id       | INTEGER | Primary key                    |
| habit_id | INTEGER | Foreign key to habits table    |
| date     | DATE    | Completion date (YYYY-MM-DD)   |

