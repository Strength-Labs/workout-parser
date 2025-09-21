import json
import re
import os
import requests
from api_client import API_BASE_URL, console

def parse_line_as_set(line: str):
    """
    Tries to parse a line as a structured set. If it fails, returns None.
    """
    line = line.strip()
    base_set = {
        "set_type": "default", "rep_type": "default_rep_type", "distance": 0.0,
        "distance_unit": None, "time": 0, "body": None
    }
    
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
    match = re.match(r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*(\d+\.?\d*)", line, re.IGNORECASE)
    if match:
        sets, reps, weight = match.groups()
        parsed = {**base_set, "sets": int(sets), "weight": float(weight), "weight_type": "default_weight_type"}
        if reps.upper() == 'AMRAP': parsed["rep_type"] = "AMRAP"
        else: parsed["reps"] = int(reps)
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
    """
    Parses a text file into a list of workout dictionaries and a list of comments to be added.
    """
    with open(plain_text_path, 'r') as f: content = f.read()
    workouts = []
    workout_sections = [s for s in re.split(r'Workout Date:\s*', content) if s.strip()]

    for section in workout_sections:
        lines = section.strip().split('\n')
        workout = {
            "user_id": user_id, "workout_date": lines[0].strip(),
            "title": None, "weight_type": "lbs", "assigned_exercises": [],
            "published": True, "comments_to_add": [] # Temporary storage for comments
        }
        
        start_line_index = 1
        if len(lines) > 1:
            potential_title = lines[1].strip()
            if potential_title and potential_title.lower() not in exercise_map and not re.match(r"^\d+\s*x", potential_title):
                workout["title"] = potential_title
                start_line_index = 2

        current_exercise = None
        for line in lines[start_line_index:]:
            stripped_line = line.strip()
            if not stripped_line or stripped_line == "---" or stripped_line.startswith('('):
                continue
            
            is_indented = len(line) > len(line.lstrip())

            if is_indented:
                # Indented lines are notes. Store them for later.
                if current_exercise:
                    # Note is for the current exercise
                    note_target = {"parent_type": "AssignedExercise", "text": stripped_line}
                    current_exercise.setdefault("comments_to_add", []).append(note_target)
                else:
                    # Note is for the whole workout
                    note_target = {"parent_type": "Workout", "text": stripped_line}
                    workout.setdefault("comments_to_add", []).append(note_target)
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
            
        if current_exercise:
            workout["assigned_exercises"].append(current_exercise)
        if workout["assigned_exercises"]:
            workouts.append(workout)
            
    return workouts

def post_comment(token, parent_id, parent_type, body):
    """Posts a single comment to a workout or assigned exercise."""
    url = f"{API_BASE_URL}/api/v1/comments"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    params = {"parent_type": parent_type, "parent_id": parent_id}
    payload = {"body": body}
    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        console.print(f"[yellow]Warning: Could not post comment '{body[:30]}...': {e}[/yellow]")

def upload_workout(token, workout_data):
    """Uploads a workout and then adds any associated comments."""
    url = f"{API_BASE_URL}/api/v1/workouts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Pop our temporary comment storage before sending
    comments_to_add_to_workout = workout_data.pop("comments_to_add", [])
    
    try:
        console.print(f"Uploading workout for [cyan]{workout_data['workout_date']}[/cyan]...")
        response = requests.post(url, headers=headers, json=workout_data)
        response.raise_for_status()
        created_workout = response.json()
        console.print(f"✅ [bold green]Successfully uploaded workout![/bold green]")
        
        # --- Step 2: Add Comments ---
        # Add workout-level comments
        for comment in comments_to_add_to_workout:
            post_comment(token, created_workout['id'], "Workout", comment['text'])

        # Add exercise-level comments
        for i, created_exercise in enumerate(created_workout.get('assigned_exercises', [])):
            original_exercise = workout_data['assigned_exercises'][i]
            comments_to_add_to_exercise = original_exercise.get("comments_to_add", [])
            for comment in comments_to_add_to_exercise:
                 post_comment(token, created_exercise['id'], "AssignedExercise", comment['text'])

    except requests.exceptions.HTTPError as e:
        console.print(f"❌ [bold red]Upload failed.[/bold red] HTTP Error: {e.response.status_code}")
        console.print(f"[dim]API Response: {e.response.text}[/dim]")
