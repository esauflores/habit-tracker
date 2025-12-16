import os
import sys
import termios
import tty

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
                elif ch3 == "C":  # Right arrow - ignore
                    return None
                elif ch3 == "D":  # Left arrow - ignore
                    return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

options = [
    "Running",
    "Reading",
    "Meditation",
    "Morning Run",
    "Run at Night",
    "Gym",
    "Yoga",
    "Coding"
]

def search_bar():
    query = ""
    selected_index = 0

    while True:
        clear()
        print("Habit: " + query) 

        matches = []
        for item in options:
            if query.lower() in item.lower():
                matches.append(item)

        # Limit displayed results
        display_matches = matches[:5]
        
        for i in range(len(display_matches)):
            if i == selected_index and len(display_matches) > 0:
                print(" >", display_matches[i])
            else:
                print(" ", display_matches[i])

        ch = get_char()

        if ch == "\x1b":  # ESC key
            break
        elif ch == "\x7f": # Backspace
            query = query[:-1]
            selected_index = 0
        elif ch == "\r": # Enter
            if len(display_matches) > 0:
                print(f"\nSelected: {display_matches[selected_index]}")
                break
        elif ch == "UP":
            if len(display_matches) > 0:
                selected_index = (selected_index - 1) % len(display_matches)
        elif ch == "DOWN":
            if len(display_matches) > 0:
                selected_index = (selected_index + 1) % len(display_matches)
        elif ch is None:  # Left/Right arrows - do nothing
            pass
        else:
            query += ch
            selected_index = 0

if __name__ == "__main__":
    search_bar()