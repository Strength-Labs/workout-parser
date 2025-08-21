import json
import re
import readline
import os
import glob
import sys
from fuzzywuzzy import process
from typing import Dict, List, Optional, Tuple

def complete(text, state):
    """Enable tab completion for file paths."""
    return (glob.glob(text + '*') + [None])[state]

readline.set_completer_delims(' ')
readline.parse_and_bind("tab: complete")

def create_exercise_mapping() -> Tuple[Optional[Dict[str, int]], Optional[List[str]]]:
    """Creates a mapping from exercise names to their IDs from exerciselist.json in the script's directory."""
    exerciselist_path = os.path.join(os.path.dirname(__file__), 'exerciselist.json')
    try:
        with open(exerciselist_path, 'r') as f:
            exercises = json.load(f)
        exercise_mapping = {exercise['name'].lower(): exercise['id'] for exercise in exercises}
        exercise_names = list(exercise_mapping.keys())
        return exercise_mapping, exercise_names
    except FileNotFoundError:
        print(f"Error: The file '{exerciselist_path}' was not found in the script's directory.")
        return None, None

def get_similar_exercises(exercise_name: str, exercise_names: List[str], limit: int = 5) -> List[str]:
    """Find similar exercise names using fuzzy matching."""
    matches = process.extract(exercise_name, exercise_names, limit=limit)
    return [match[0] for match in matches if match[1] >= 80]

def prompt_for_exercise(exercise_name: str, exercise_names: List[str], line_num: int) -> Optional[str]:
    """Prompt user to select or input a valid exercise name or skip."""
    print(f"Line {line_num}: Exercise '{exercise_name}' not found in exerciselist.json.")
    similar_exercises = get_similar_exercises(exercise_name.lower(), exercise_names)
    
    if similar_exercises:
        print("Suggested exercises:")
        for i, suggestion in enumerate(similar_exercises, 1):
            print(f"{i}. {suggestion}")
        print(f"{len(similar_exercises) + 1}. Enter a different exercise name")
        print(f"{len(similar_exercises) + 2}. Skip this exercise")
        
        while True:
            try:
                choice = input(f"Select an option (1-{len(similar_exercises) + 2}): ")
                choice = int(choice)
                if 1 <= choice <= len(similar_exercises):
                    return similar_exercises[choice - 1]
                elif choice == len(similar_exercises) + 1:
                    new_name = input("Enter the correct exercise name: ").strip().lower()
                    if new_name in exercise_names:
                        return new_name
                    else:
                        print(f"'{new_name}' is not in exerciselist.json. Try again.")
                elif choice == len(similar_exercises) + 2:
                    return None
                else:
                    print(f"Invalid choice. Enter a number between 1 and {len(similar_exercises) + 2}.")
            except ValueError:
                print("Please enter a valid number.")
    else:
        print("No similar exercises found.")
        new_name = input("Enter the correct exercise name or press Enter to skip: ").strip().lower()
        return new_name if new_name in exercise_names else None

def parse_workouts(plain_text_path: str, exercise_mapping: Dict[str, int], exercise_names: List[str], user_id: int) -> List[Dict]:
    """Parses a plain text workout file and returns a list of workout dictionaries for the API."""
    if exercise_mapping is None or exercise_names is None:
        raise FileNotFoundError("Exercise list not found. Cannot parse workouts.")

    workouts = []
    current_workout = None
    current_exercise = None
    exercise_priority = 0

    with open(plain_text_path, 'r') as f:
        lines = f.readlines()
        line_num = 0

        while line_num < len(lines):
            line = lines[line_num]
            line_num += 1
            
            # Use lstrip to check for the comment syntax, regardless of leading whitespace
            stripped_line_with_indent = line.lstrip(' \t')
            stripped_line = line.strip()

            if not stripped_line:
                continue
            
            # Check for a new workout date to start a new workout
            if stripped_line.startswith("Workout Date:"):
                if current_workout:
                    if current_exercise:
                        current_workout["assigned_exercises"].append(current_exercise)
                    workouts.append(current_workout)
                
                current_workout = {
                    "user_id": user_id,
                    "workout_date": stripped_line.replace("Workout Date:", "").strip(),
                    "weight_type": "lbs",
                    "assigned_exercises": []
                }
                current_exercise = None
                exercise_priority = 0
                continue
            
            # If a workout hasn't been started, we have a malformed file
            if current_workout is None:
                raise ValueError(f"Line {line_num}: Malformed input. Expected 'Workout Date:' at the start of the file.")
            
            # Check for private coach comments (ignored)
            if stripped_line_with_indent.startswith('>'):
                continue
            
            # Check for a new exercise name or a set line
            if not (line.startswith(' ') or line.startswith('\t')):
                # This must be a new exercise
                if stripped_line.lower() in exercise_mapping:
                    if current_exercise:
                        current_workout["assigned_exercises"].append(current_exercise)
                    current_exercise = {
                        "exercise_id": exercise_mapping[stripped_line.lower()],
                        "priority": exercise_priority,
                        "assigned_sets": []
                    }
                    exercise_priority += 1
                    continue
                else:
                    # It's not an exercise and it's not indented, so it should be a set line
                    if current_exercise is None:
                        raise ValueError(f"Line {line_num}: Malformed input. Expected an exercise name, but found a set or a note: '{stripped_line}'.")

                    # Parse sets and notes
                    match_set_rep_weight = re.match(r'(\d+)x(\d+)\s*@\s*(\d+\.?\d*)', stripped_line)
                    match_set_rep_rpe = re.match(r'(\d+)x(\d+)\s*@\s*RPE\s*(\d+)', stripped_line)
                    match_set_rep_amrap = re.match(r'(\d+)xAMRAP\s*@\s*(\d+\.?\d*)', stripped_line)
                    match_set_rep_distance = re.match(r'(\d+\.?\d*)\s*(miles|kilometers|meters|yards|feet|calories)\s*@\s*(\d+):(\d+):(\d+)', stripped_line)
                    match_set_rep_text = re.match(r'(\d+)x(\d+)\s*@\s*(.*)', stripped_line)

                    if match_set_rep_weight:
                        sets, reps, weight = match_set_rep_weight.groups()
                        current_exercise["assigned_sets"].append({
                            "priority": len(current_exercise["assigned_sets"]),
                            "sets": int(sets),
                            "reps": int(reps),
                            "weight": float(weight),
                            "weight_type": "default_weight_type",
                            "rep_type": "default_rep_type",
                            "set_type": "default"
                        })
                    elif match_set_rep_rpe:
                        sets, reps, rpe = match_set_rep_rpe.groups()
                        current_exercise["assigned_sets"].append({
                            "priority": len(current_exercise["assigned_sets"]),
                            "sets": int(sets),
                            "reps": int(reps),
                            "weight_type": "RPE",
                            "weight_type_value": int(rpe),
                            "rep_type": "default_rep_type",
                            "set_type": "default"
                        })
                    elif match_set_rep_amrap:
                        sets, weight = match_set_rep_amrap.groups()
                        current_exercise["assigned_sets"].append({
                            "priority": len(current_exercise["assigned_sets"]),
                            "sets": int(sets),
                            "reps": 0,
                            "weight": float(weight),
                            "weight_type": "default_weight_type",
                            "rep_type": "AMRAP",
                            "set_type": "default"
                        })
                    elif match_set_rep_distance:
                        distance, distance_unit, hh, mm, ss = match_set_rep_distance.groups()
                        time_seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
                        current_exercise["assigned_sets"].append({
                            "priority": len(current_exercise["assigned_sets"]),
                            "distance": float(distance),
                            "distance_unit": distance_unit,
                            "time": time_seconds,
                            "set_type": "default"
                        })
                    elif match_set_rep_text:
                        sets, reps, body = match_set_rep_text.groups()
                        current_exercise["assigned_sets"].append({
                            "priority": len(current_exercise["assigned_sets"]),
                            "sets": int(sets),
                            "reps": int(reps),
                            "set_type": "custom",
                            "body": body.strip()
                        })
                    else:
                        raise ValueError(f"Line {line_num}: Unrecognized line format for a set or note: '{stripped_line}'.")
                continue

            # If we reach this point, the line must be indented.
            if current_exercise is None:
                raise ValueError(f"Line {line_num}: Indented content found without a preceding exercise name.")
            
            # Parse sets and notes for indented lines
            stripped_line_no_indent = line.lstrip(' \t')
            match_set_rep_weight = re.match(r'(\d+)x(\d+)\s*@\s*(\d+\.?\d*)', stripped_line_no_indent)
            match_set_rep_rpe = re.match(r'(\d+)x(\d+)\s*@\s*RPE\s*(\d+)', stripped_line_no_indent)
            match_set_rep_amrap = re.match(r'(\d+)xAMRAP\s*@\s*(\d+\.?\d*)', stripped_line_no_indent)
            match_set_rep_distance = re.match(r'(\d+\.?\d*)\s*(miles|kilometers|meters|yards|feet|calories)\s*@\s*(\d+):(\d+):(\d+)', stripped_line_no_indent)
            match_set_rep_text = re.match(r'(\d+)x(\d+)\s*@\s*(.*)', stripped_line_no_indent)

            if match_set_rep_weight:
                sets, reps, weight = match_set_rep_weight.groups()
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "sets": int(sets),
                    "reps": int(reps),
                    "weight": float(weight),
                    "weight_type": "default_weight_type",
                    "rep_type": "default_rep_type",
                    "set_type": "default"
                })
            elif match_set_rep_rpe:
                sets, reps, rpe = match_set_rep_rpe.groups()
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "sets": int(sets),
                    "reps": int(reps),
                    "weight_type": "RPE",
                    "weight_type_value": int(rpe),
                    "rep_type": "default_rep_type",
                    "set_type": "default"
                })
            elif match_set_rep_amrap:
                sets, weight = match_set_rep_amrap.groups()
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "sets": int(sets),
                    "reps": 0,
                    "weight": float(weight),
                    "weight_type": "default_weight_type",
                    "rep_type": "AMRAP",
                    "set_type": "default"
                })
            elif match_set_rep_distance:
                distance, distance_unit, hh, mm, ss = match_set_rep_distance.groups()
                time_seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "distance": float(distance),
                    "distance_unit": distance_unit,
                    "time": time_seconds,
                    "set_type": "default"
                })
            elif match_set_rep_text:
                sets, reps, body = match_set_rep_text.groups()
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "sets": int(sets),
                    "reps": int(reps),
                    "set_type": "custom",
                    "body": body.strip()
                })
            else:
                current_exercise["assigned_sets"].append({
                    "priority": len(current_exercise["assigned_sets"]),
                    "set_type": "custom",
                    "body": stripped_line
                })

    # Finalize the last workout
    if current_workout:
        if current_exercise:
            current_workout["assigned_exercises"].append(current_exercise)
        workouts.append(current_workout)

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

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Parsing Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    try:
        from fuzzywuzzy import process
    except ImportError:
        print("Error: The 'fuzzywuzzy' library is required. Install it using 'pip install fuzzywuzzy python-Levenshtein'")
        sys.exit(1)
    main()

