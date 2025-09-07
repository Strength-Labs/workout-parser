#!/usr/bin/env python3

import json
import re
import readline
import os
import glob
import sys
from typing import Dict, List, Optional, Tuple

# Attempt to import fuzzywuzzy and provide a helpful error message if it fails
try:
    from fuzzywuzzy import process
except ImportError:
    print("Error: The 'fuzzywuzzy' library is required. Please install it by running 'pip install fuzzywuzzy python-Levenshtein'")
    sys.exit(1)

def complete(text, state):
    """Enable tab completion for file paths."""
    return (glob.glob(text + '*') + [None])[state]

readline.set_completer_delims(' ')
readline.parse_and_bind("tab: complete")

def create_exercise_mapping() -> Tuple[Optional[Dict[str, int]], Optional[List[str]]]:
    """
    Creates a mapping from exercise names to their IDs from exerciselist.json.
    If duplicate exercise names exist, prioritize the first one found.
    """
    exerciselist_path = os.path.join(os.path.dirname(__file__), 'exerciselist.json')
    try:
        with open(exerciselist_path, 'r') as f:
            exercises = json.load(f)
        
        # --- Start of modification ---
        # Build mapping carefully to avoid overwrites from duplicates.
        exercise_mapping = {}
        for exercise in exercises:
            name_lower = exercise['name'].lower()
            if name_lower not in exercise_mapping:
                exercise_mapping[name_lower] = exercise['id']
        # --- End of modification ---

        exercise_names = list(exercise_mapping.keys())
        return exercise_mapping, exercise_names
    except FileNotFoundError:
        print(f"Error: The file '{exerciselist_path}' was not found in the script's directory.")
        return None, None

def get_similar_exercises(exercise_name: str, exercise_names: List[str], limit: int = 5) -> List[str]:
    """Find similar exercise names using fuzzy matching."""
    matches = process.extract(exercise_name, exercise_names, limit=limit)
    return [match[0] for match in matches if match[1] > 80]

def parse_line(line: str) -> Optional[Dict]:
    """
    Parse a single line to determine if it's a set, comment, or plain text.
    Returns None if the line is a private coaching comment.
    """
    line = line.strip()

    # Ignore private coaching comments
    if line.startswith('>'):
        return None

    # Base dictionary that every set object must have
    base_set = {
        "priority": 0,
        "set_type": "default",
        "rep_type": "default_rep_type",
        "weight": 0.0 # Default weight to 0.0, will be overwritten if applicable.
    }

    # Pattern for "Accomplished" sets
    accomplished_match = re.match(r"Accomplished:\s*(\d+)\s*x\s*([\d\w]+)\s*@\s*([\d\.]+)", line, re.IGNORECASE)
    if accomplished_match:
        sets, reps, weight = accomplished_match.groups()
        return {
            **base_set,
            "sets": int(sets),
            "reps": int(reps) if reps.isnumeric() else 0,
            "weight": float(weight),
            "status": "accomplished"
        }

    # Pattern for bodyweight
    if "bodyweight" in line.lower():
        bw_pattern = re.compile(r"(\d+)\s*x\s*([\w\d]+)", re.IGNORECASE)
        bw_match = bw_pattern.match(line)
        if bw_match:
            sets, reps = bw_match.groups()
            assigned_set = {**base_set, "sets": int(sets), "weight_type": "bodyweight"}
            if reps.isnumeric():
                assigned_set["reps"] = int(reps)
            elif reps.upper() == "AMRAP":
                assigned_set["rep_type"] = "AMRAP"
                assigned_set["reps"] = 0
            return assigned_set

    # Pattern for RPE
    if "rpe" in line.lower():
        rpe_pattern = re.compile(r"(\d+)\s*x\s*([\w\d]+)\s*@\s*(RPE\s*\d+)", re.IGNORECASE)
        rpe_match = rpe_pattern.match(line)
        if rpe_match:
            sets, reps, rpe_val = rpe_match.groups()
            assigned_set = {**base_set, "sets": int(sets)}
            if reps.isnumeric():
                assigned_set["reps"] = int(reps)
            elif reps.upper() == "AMRAP":
                assigned_set["rep_type"] = "AMRAP"
                assigned_set["reps"] = 0
            assigned_set["weight_type"] = "RPE"
            assigned_set["weight_type_value"] = int(rpe_val.upper().replace("RPE", "").strip())
            assigned_set["weight"] = 0.0 # Add weight field for RPE sets per corrected JSON
            return assigned_set

    # Pattern for weight in lbs or percentage
    if re.search(r"@\s*[\d\.]+", line):
        lbs_pattern = re.compile(r"(\d+)\s*x\s*([\w\d]+)\s*@\s*([\d\.]+)\s*(lbs|%|kg)?", re.IGNORECASE)
        lbs_match = lbs_pattern.match(line)
        if lbs_match:
            sets, reps, weight_value, unit = lbs_match.groups()
            assigned_set = {**base_set, "sets": int(sets)}

            if reps.isnumeric():
                assigned_set["reps"] = int(reps)
            elif reps.upper() == "AMRAP":
                assigned_set["rep_type"] = "AMRAP"
                assigned_set["reps"] = 0

            if unit and unit == "%":
                assigned_set["weight_type"] = "percent"
                assigned_set["weight_type_value"] = float(weight_value)
                assigned_set["weight"] = 0.0 # Add weight field for percentage sets per corrected JSON
            else:
                assigned_set["weight"] = float(weight_value)

            return assigned_set

    # Simpler pattern for sets x reps without weight
    simple_pattern = re.compile(r"(\d+)\s*x\s*([\w\d]+)", re.IGNORECASE)
    simple_match = simple_pattern.match(line)
    if simple_match:
        sets, reps = simple_match.groups()
        assigned_set = {**base_set, "sets": int(sets)}
        if reps.isnumeric():
            assigned_set["reps"] = int(reps)
        elif reps.upper() == "AMRAP":
            assigned_set["rep_type"] = "AMRAP"
            assigned_set["reps"] = 0
        return assigned_set

    # If no pattern matches, it's a public note
    return {**base_set, "set_type": "custom", "body": line}


def parse_workouts(plain_text_path: str, exercise_mapping: Dict[str, int], exercise_names: List[str], user_id: int) -> List[Dict]:
    """Parses a plain text file and converts it into a structured workout format."""
    with open(plain_text_path, 'r') as f:
        content = f.read()

    workouts = []
    workout_sections = re.split(r'Workout Date:\s*', content)

    for section in workout_sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        workout_date = lines[0].strip()
        workout = {
            "user_id": user_id,
            "workout_date": workout_date,
            "weight_type": "lbs",
            "assigned_exercises": []
        }

        current_exercise = None

        for line in lines[1:]:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            # ignore the --- workout breaks. 
            if stripped_line == "---":
                continue

            # Ignore private coaching comments
            if stripped_line.startswith('>'):
                continue
            
            # Ignore conversational comments
            if re.match(r"\[.*?\]:", stripped_line):
                continue
            
            # Check if line is a known exercise name
            # Exercise names are unindented.
            indentation = len(line) - len(line.lstrip())
            if indentation == 0 and stripped_line.lower() in exercise_mapping:
                if current_exercise:
                    workout["assigned_exercises"].append(current_exercise)
                current_exercise = {
                    "exercise_id": exercise_mapping[stripped_line.lower()],
                    "priority": len(workout["assigned_exercises"])
                }
                continue

            # --- Process line as set or note ---
            if current_exercise:
                parsed_info = parse_line(stripped_line)
                if parsed_info:
                    assigned_sets_list = current_exercise.setdefault("assigned_sets", [])
                    parsed_info["priority"] = len(assigned_sets_list)
                    assigned_sets_list.append(parsed_info)
            elif indentation == 0:
                # Handle potential unknown exercises or non-note lines before first exercise
                similar_exercises = get_similar_exercises(stripped_line.lower(), exercise_names)
                if similar_exercises:
                    print(f"\nExercise '{stripped_line}' not found. Did you mean one of these?")
                    for i, name in enumerate(similar_exercises, 1):
                        print(f"{i}: {name.title()}")
                    print("m: Manually enter exercise name")
                    print("0: Skip (treat as a note/error)")

                    while True:
                        choice = input("Enter number, 'm', or 0 to skip: ")
                        if choice.isnumeric() and 0 <= int(choice) <= len(similar_exercises):
                            choice = int(choice)
                            break
                        elif choice.lower() == 'm':
                            break
                        else:
                            print("Invalid choice.")

                    if choice == 'm':
                        while True:
                            manual_exercise = input("Enter the correct exercise name: ").lower()
                            if manual_exercise in exercise_mapping:
                                chosen_exercise = manual_exercise
                                break
                            else:
                                print(f"'{manual_exercise}' not found in the exercise list. Please try again.")
                    elif choice > 0:
                        chosen_exercise = similar_exercises[choice - 1]
                    else: # Skip
                        chosen_exercise = None

                    if chosen_exercise:
                        if current_exercise:
                            workout["assigned_exercises"].append(current_exercise)
                        current_exercise = {
                            "exercise_id": exercise_mapping[chosen_exercise],
                            "priority": len(workout["assigned_exercises"])
                        }

        if current_exercise:
            workout["assigned_exercises"].append(current_exercise)

        workouts.append(workout)

    return workouts

def main():
    """Main function to run the workout parser."""
    try:
        exercise_mapping, exercise_names = create_exercise_mapping()
        if exercise_mapping is None:
            sys.exit(1)
    except Exception as e:
        print(f"Error during exercise mapping creation: {e}")
        sys.exit(1)

    while True:
        try:
            user_id = int(input("Enter the user ID: "))
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer for the user ID.")

    plain_text_path = input("Enter the path to the plain text workout file: ")

    try:
        workouts = parse_workouts(plain_text_path, exercise_mapping, exercise_names, user_id)

        output_filename = plain_text_path.rsplit('.txt', 1)[0] + '.json' if plain_text_path.endswith('.txt') else plain_text_path + '.json'
        with open(output_filename, 'w') as f:
            json.dump(workouts, f, indent=2)

        print(f"Successfully converted workout to {output_filename}")

    except FileNotFoundError:
        print(f"Error: The file '{plain_text_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
