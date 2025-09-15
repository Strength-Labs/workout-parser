#!/usr/bin/env python3
# A script to analyze a local JSON file of a client's workout history
# to find their best performances (estimated 1RMs) within a given time period.

import json
import os
import sys
from datetime import datetime, timedelta, date

# Libraries for Tab Completion
import readline
import glob

# --- Tab Completion Setup ---
def json_completer(text, state):
    """A completer function for JSON files."""
    # Add a wildcard to the text to match files
    pattern = text + '*.json'
    # Use glob to find all matching files
    files = glob.glob(pattern)
    # Return the file at the given state index, or None if out of bounds
    return files[state] if state < len(files) else None

# Register the completer function
readline.set_completer(json_completer)
# Use the tab key for completion
readline.parse_and_bind('tab: complete')
# Note for Windows users: You may need to install pyreadline3
# pip install pyreadline3

# --- Configuration ---
MAIN_LIFTS = ["squat", "bench press", "deadlift", "press"]

def clear_screen():
    """Clears the terminal screen for a cleaner interface."""
    os.system('cls' if os.name == 'nt' else 'clear')

def wendler_1rm(weight, reps):
    """Calculates estimated 1RM using the Wendler formula."""
    reps_val = reps if reps is not None else 1
    if not isinstance(reps_val, (int, float)) or reps_val <= 1:
        return weight
    return (weight * reps_val * 0.0333) + weight

def load_workout_data(filepath):
    """Loads and returns workout data from a local JSON file."""
    if not os.path.exists(filepath):
        print(f"\n[ERROR] File not found at path: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} workouts from {filepath}. 👍")
        return data
    except json.JSONDecodeError:
        print(f"\n[ERROR] Could not decode JSON. The file might be corrupt: {filepath}")
        return None
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred while reading the file: {e}")
        return None

def process_workout_history(workouts, start_date=None, end_date=None):
    """
    Processes workout history to find the best e1RM for every exercise in a date range.
    """
    best_performances = {}
    for workout in workouts:
        workout_date_str = workout.get("workout_date")
        if not workout_date_str:
            continue
        workout_date = datetime.strptime(workout_date_str, "%Y-%m-%d").date()
        if start_date and workout_date < start_date:
            continue
        if end_date and workout_date > end_date:
            continue
        for exercise in workout.get("assigned_exercises", []):
            lift_name = exercise.get("exercise", {}).get("name", "Unknown").lower()
            for assigned_set in exercise.get("assigned_sets", []):
                for actual_set in assigned_set.get("actual_sets", []):
                    weight = float(actual_set.get("weight", 0) or 0)
                    reps = actual_set.get("reps")
                    unit = workout.get("weight_type", "units")
                    if not reps or not weight:
                        continue
                    estimated_1rm = wendler_1rm(weight, reps)
                    if lift_name not in best_performances or estimated_1rm > best_performances[lift_name]['e1rm']:
                        best_performances[lift_name] = {
                            'e1rm': estimated_1rm,
                            'weight': weight,
                            'reps': reps,
                            'unit': unit,
                            'date': workout_date_str
                        }
    return best_performances

def display_results(best_performances, date_range_str):
    """Displays the formatted best performances."""
    main_lift_performances = {k: v for k, v in best_performances.items() if k in MAIN_LIFTS}
    other_lift_performances = {k: v for k, v in best_performances.items() if k not in MAIN_LIFTS}
    
    clear_screen()
    print(f"--- Best Lift Performances ---")
    print(f"---  Date Range: {date_range_str}  ---\n")

    print("--- Main Lifts ---")
    for lift in MAIN_LIFTS:
        perf = main_lift_performances.get(lift)
        lift_display_name = lift.replace(" press", " Press").title()
        if perf:
            print(f"{lift_display_name:<15} {perf['e1rm']:.1f} {perf['unit']} on {perf['date']} (from {perf['weight']} {perf['unit']} x {perf['reps']})")
        else:
            print(f"{lift_display_name:<15} No performance found")

    print("\n" + "-"*50)
    choice = input("\nPress Enter to choose a new date range, or 'm' for more lifts... ")
    
    if choice.lower() == 'm':
        print("\n--- Other Lifts ---")
        if not other_lift_performances:
            print("No other lift performances found in this period.")
        else:
            for lift_name in sorted(other_lift_performances.keys()):
                perf = other_lift_performances[lift_name]
                display_name = lift_name.title()
                print(f"{display_name:<25} {perf['e1rm']:.1f} {perf['unit']} on {perf['date']} (from {perf['weight']} {perf['unit']} x {perf['reps']})")
        input("\nPress Enter to return to the date menu...")

def main():
    """Main analysis loop."""
    clear_screen()
    print("--- Local Workout History Analyzer ---")
    print("Start typing a filename and press <Tab> to autocomplete.")
    filepath = input("Enter the path to the workout history JSON file: ")
    
    workouts = load_workout_data(filepath)
    if not workouts:
        sys.exit(1)

    while True:
        clear_screen()
        print(f"Analyzing: {os.path.basename(filepath)}")
        print("\n--- Select a Date Range ---")
        print(" [3] Last 3 Months")
        print(" [6] Last 6 Months")
        print(" [Y] Last Year")
        print(" [A] All Time")
        print(" [C] Custom Range")
        print(" [Q] Quit")
        choice = input("> ").lower()

        start_date, end_date = None, None
        today = date.today()
        date_range_str = "All Time"

        if choice == 'q':
            break
        elif choice == 'a':
            pass
        elif choice == '3':
            start_date = today - timedelta(days=90)
            date_range_str = "Last 3 Months"
        elif choice == '6':
            start_date = today - timedelta(days=180)
            date_range_str = "Last 6 Months"
        elif choice == 'y':
            start_date = today - timedelta(days=365)
            date_range_str = "Last Year"
        elif choice == 'c':
            try:
                start_str = input("Enter start date (YYYY-MM-DD): ")
                end_str = input("Enter end date   (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                date_range_str = f"Custom ({start_date} to {end_date})"
            except ValueError:
                input("\n[ERROR] Invalid date format. Press Enter to try again.")
                continue
        else:
            input("Invalid option. Press Enter to try again.")
            continue

        best_performances = process_workout_history(workouts, start_date, end_date)
        display_results(best_performances, date_range_str)

if __name__ == "__main__":
    main()
    print("\nExiting. Goodbye!")
