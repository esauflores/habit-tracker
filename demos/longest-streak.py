from datetime import datetime, timedelta

dates = [
    "2025-01-01", "2025-01-02", "2025-01-03",
    "2025-02-01", "2025-02-02",
    "2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04", "2025-03-05",
    "2025-04-01", "2025-04-02", "2025-04-03", "2025-04-04"
]
def longest_streak(days):
    if not days:
        return 0
    
    parsed_dates = []
    for day in days:
        try:
            parsed_dates.append(datetime.strptime(day, "%Y-%m-%d").date())
        except ValueError:
            raise ValueError(f"Invalid date format: {day}")
    
    unique_dates = sorted(set(parsed_dates))

    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(unique_dates)):
        if unique_dates[i] - unique_dates[i-1] == timedelta(days=1):
            current_streak += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1
    
    max_streak = max(max_streak, current_streak)
    
    return max_streak


if __name__ == "__main__":
    for date in dates:
        print(datetime.strptime(date, "%Y-%m-%d").date(), end=" ")
    print()
    print("Longest streak: ", longest_streak(dates))
