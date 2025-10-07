import json
import re
import os
import requests
from api_client import API_BASE_URL, console

try:
    from rapidfuzz import process
except ImportError:
    pass

def get_similar_exercises(exercise_name: str, exercise_names: list[str], limit: int = 5):
    """Finds similar exercise names using fuzzy matching."""
    matches = process.extract(exercise_name, exercise_names, limit=limit)
    return [match[0] for match in matches if match[1] > 80]

def parse_line_as_set(line: str):
    """
    Tries to parse a line as a structured set. If it fails, returns None.
    """
    line = line.strip()
    base_set = {
        "set_type": "default", "rep_type": "default_rep_type", "distance": 0.0,
        "distance_unit": None, "time": 0, "body": None, "reps": None
    }
    
    # Time-based format
    time_match = re.match(r"(\d+)\s*x\s*(\d{1,2}:\d{2})(?:\s*@\s*(RPE\s*\d+\.?\d*))?", line, re.IGNORECASE)
    if time_match:
        sets, duration_str, rpe_str = time_match.groups()
        try:
            minutes, seconds = map(int, duration_str.split(':'))
            total_seconds = (minutes * 60) + seconds
        except ValueError: return None
        parsed = {**base_set, "sets": int(sets), "time": total_seconds, "weight": None}
        if rpe_str:
            parsed["weight_type"] = "RPE"
            parsed["weight_type_value"] = float(rpe_str.upper().replace("RPE", "").strip())
        else:
            parsed["weight_type"] = "bodyweight"
        return parsed
    
    # RPE-based
    match = re.match(r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*RPE\s*(\d+\.?\d*)", line, re.IGNORECASE)
    if match:
        sets, reps, rpe = match.groups()
        parsed = {**base_set, "sets": int(sets), "weight": None, "weight_type": "RPE", "weight_type_value": float(rpe)}
        if reps.upper() == 'AMRAP': parsed["rep_type"] = "AMRAP"
        else: parsed["reps"] = int(reps)
        return parsed

    # Percentage-based
    match = re.match(r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*(\d+\.?\d*)\s*%", line, re.IGNORECASE)
    if match:
        sets, reps, percent = match.groups()
        parsed = {**base_set, "sets": int(sets), "weight": None, "weight_type": "percent", "weight_type_value": float(percent)}
        if reps.upper() == 'AMRAP': parsed["rep_type"] = "AMRAP"
        else: parsed["reps"] = int(reps)
        return parsed

    # Weight-based
    match = re.match(r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*(\d+\.?\d*)(?:\s*(lbs|kg))?", line, re.IGNORECASE)
    if match:
        sets, reps, weight, units = match.groups()
        parsed = {**base_set, "sets": int(sets), "weight": float(weight), "weight_type": "default_weight_type"}
        if reps.upper() == 'AMRAP': parsed["rep_type"] = "AMRAP"
        else: parsed["reps"] = int(reps)
        if units:  # Store parsed units for workout-level detection
            parsed["parsed_units"] = units.lower()
        return parsed

    # No weight
    match = re.match(r"(\d+)\s*x\s*([a-zA-Z0-9]+)", line, re.IGNORECASE)
    if match:
        sets, reps = match.groups()
        parsed = {**base_set, "sets": int(sets), "weight": None, "weight_type": "bodyweight"}
        if reps.upper() == 'AMRAP': parsed["rep_type"] = "AMRAP"
        else: parsed["reps"] = int(reps)
        return parsed

    return None

def parse_workouts_from_file(plain_text_path: str, user_id: int, exercise_map: dict):
    """Parses a text file into a list of workout dictionaries, with interactive fuzzy matching."""
    with open(plain_text_path, 'r') as f: content = f.read()
    workouts = []
    workout_sections = [s for s in re.split(r'Workout Date:\s*', content) if s.strip()]
    exercise_names = list(exercise_map.keys())

    for section in workout_sections:
        lines = section.strip().split('\n')
        workout = {
            "user_id": user_id, "workout_date": lines[0].strip(),
            "title": None, "weight_type": "lbs", "assigned_exercises": [],
            "published": True,
        }
        
        start_line_index = 1
        if len(lines) > 1:
            potential_title = lines[1].strip()
            if potential_title and potential_title.lower() not in exercise_map and not re.match(r"^\d+\s*x", potential_title):
                workout["title"] = potential_title
                start_line_index = 2

        current_exercise = None
        kg_detected = False
        for line in lines[start_line_index:]:
            stripped_line = line.strip()
            if not stripped_line or stripped_line == "---" or stripped_line.startswith('(') or stripped_line.startswith('['):
                continue
            
            is_indented = len(line) > len(line.lstrip())

            if is_indented:
                if stripped_line.startswith('>'): continue
                if current_exercise:
                    note_set = {
                        "set_type": "custom", "body": stripped_line, "priority": len(current_exercise["assigned_sets"]),
                        "rep_type": "default_rep_type", "distance": 0.0, "distance_unit": None, "time": 0, "reps": None, "sets": None, "weight": None
                    }
                    current_exercise["assigned_sets"].append(note_set)
                else:
                    console.print(f"[yellow]Warning: Found indented note with no preceding exercise: '{stripped_line}'[/yellow]")
                continue

            if stripped_line.lower() in exercise_map:
                if current_exercise: workout["assigned_exercises"].append(current_exercise)
                ex_id = exercise_map[stripped_line.lower()]
                current_exercise = {"exercise_id": ex_id, "priority": len(workout["assigned_exercises"]), "assigned_sets": []}
                continue

            parsed_set = parse_line_as_set(stripped_line)
            if parsed_set and current_exercise:
                parsed_set["priority"] = len(current_exercise["assigned_sets"])
                current_exercise["assigned_sets"].append(parsed_set)
                if parsed_set.get("parsed_units") == "kg":
                    kg_detected = True
            elif parsed_set:
                 console.print(f"[yellow]Warning: Found a set with no preceding exercise: '{stripped_line}'[/yellow]")
            else:
                similar_exercises = get_similar_exercises(stripped_line.lower(), exercise_names)
                if similar_exercises:
                    console.print(f"\nExercise [yellow]'{stripped_line}'[/yellow] not found. Did you mean one of these?")
                    for i, name in enumerate(similar_exercises, 1): console.print(f"  [[bold]{i}[/bold]] {name.title()}")
                    console.print("  [[bold]s[/bold]] Skip this line")

                    chosen_exercise_name = None
                    while True:
                        choice = console.input("Enter a number or 's' to skip > ").lower()
                        if choice == 's': break
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(similar_exercises):
                                chosen_exercise_name = similar_exercises[choice_idx]
                                break
                        except ValueError: pass
                        console.print("[red]Invalid input.[/red]")
                    
                    if chosen_exercise_name:
                        if current_exercise: workout["assigned_exercises"].append(current_exercise)
                        ex_id = exercise_map[chosen_exercise_name]
                        current_exercise = {"exercise_id": ex_id, "priority": len(workout["assigned_exercises"]), "assigned_sets": []}
                else:
                    console.print(f"[yellow]Warning: Could not parse or find match for line: '{stripped_line}'[/yellow]")

        if current_exercise:
            workout["assigned_exercises"].append(current_exercise)
        if workout["assigned_exercises"]:
            if kg_detected:
                workout["weight_type"] = "kgs"
                console.print(f"[green]Detected kg units—setting workout weight_type to 'kgs' for API compatibility.[/green]")
            workouts.append(workout)
            
    return workouts

def upload_workout(token, workout_data):
    """Uploads a single workout to the API."""
    url = f"{API_BASE_URL}/api/v1/workouts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        console.print(f"Uploading workout for [cyan]{workout_data['workout_date']}[/cyan]...")
        response = requests.post(url, headers=headers, json=workout_data)
        response.raise_for_status()
        console.print(f"✅ [bold green]Successfully uploaded workout![/bold green]")
    except requests.exceptions.HTTPError as e:
        console.print(f"❌ [bold red]Upload failed.[/bold red] HTTP Error: {e.response.status_code}")
        console.print(f"[dim]API Response: {e.response.text}[/dim]")