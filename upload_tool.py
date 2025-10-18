import re
import os
import json
from typing import Dict, Iterable, List, Tuple
import requests
from api_client import API_BASE_URL, console, get_exercise_id, get_exercise_type, fetch_metric_catalog
from encoding_utils import read_text_file

try:
    from rapidfuzz import process
except ImportError:
    pass

METRIC_NAME_OVERRIDES = {
    "weight": ["body_weight", "weight", "body weight"],
    "weight_kgs": ["body_weight", "weight", "body weight"],
    "weight_lbs": ["body_weight", "weight", "body weight"],
    "body_weight": ["body_weight", "body weight"],
    "body_fat": ["body_fat", "body_fat_percentage"],
    "waist": ["waist", "waist_in", "waist (in)"],
    "waist_in": ["waist", "waist (in)", "waist_in"],
    "waist_cm": ["waist", "waist (cm)", "waist_cm"],
    "chest": ["chest"],
    "arms": ["arm", "arms"],
    "thighs": ["thighs"],
    "sleep": ["sleep", "sleep_hours", "sleep hours"],
    "stress": ["stress"],
    "recovery": ["recovery"],
    "recovery_%": ["recovery"],
    "energy": ["energy"],
    "fatigue": ["fatigue"],
    "difficulty": ["difficulty", "session_difficulty"],
    "enjoyment": ["enjoyment"],
    "motivation": ["motivation"],
    "duration": ["duration", "session_duration"],
}


def normalise_metric_key(raw_value: str) -> str:
    """Create a slug-like identifier for matching metric names."""
    if not raw_value:
        return ""
    return re.sub(r'[^a-z0-9]+', '_', raw_value.strip().lower()).strip('_')

_METRIC_LOOKUP_CACHE: dict = {"loaded": False, "index": {}, "slugs": []}

def get_metric_lookup_structures(token: str, force_refresh: bool = False) -> Tuple[Dict[str, dict], List[Tuple[str, dict]]]:
    """Return cached metric lookup tables, fetching and indexing once per session."""
    global _METRIC_LOOKUP_CACHE
    if not force_refresh and _METRIC_LOOKUP_CACHE.get("loaded"):
        console.print("[dim]Using cached metric catalog index.[/dim]")
        return _METRIC_LOOKUP_CACHE["index"], _METRIC_LOOKUP_CACHE["slugs"]

    metric_catalog = fetch_metric_catalog(token)
    index, slugs = build_metric_catalog_index(metric_catalog)
    _METRIC_LOOKUP_CACHE = {"loaded": True, "index": index, "slugs": slugs}
    return index, slugs


def build_metric_catalog_index(metric_catalog: List[dict]) -> Tuple[Dict[str, dict], List[Tuple[str, dict]]]:
    """Build lookup structures for metric definition matching."""
    index: Dict[str, dict] = {}
    slug_entries: List[Tuple[str, dict]] = []
    for entry in metric_catalog or []:
        name = entry.get("name")
        if not name:
            continue
        slug = normalise_metric_key(name)
        if slug and slug not in index:
            index[slug] = entry
        if slug:
            slug_entries.append((slug, entry))
    return index, slug_entries


def _cast_metric_answer_value(value, metric_type: str):
    """Cast value to appropriate type based on metric definition."""
    if value is None:
        return None
    if metric_type in {"integer", "scale"}:
        try:
            return int(round(float(value)))
        except (ValueError, TypeError):
            return value
    if metric_type == "decimal":
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    return str(value)


def _find_metric_definition(metric_slug: str, candidate_slugs: Iterable[str], index: Dict[str, dict], slug_entries: List[Tuple[str, dict]]):
    """Locate a metric definition matching any of the candidate slugs."""
    for candidate in candidate_slugs:
        if candidate in index:
            return index[candidate]

    # Fallback: match by slug tokens (e.g., waist -> waist_in) while avoiding substring collisions
    best_match = None
    best_slug_length = None
    for candidate in candidate_slugs:
        for slug, entry in slug_entries:
            if slug == candidate:
                return entry
            tokens = [token for token in slug.split('_') if token]
            if candidate in tokens:
                slug_length = len(slug)
                if best_match is None or slug_length < best_slug_length:
                    best_match = entry
                    best_slug_length = slug_length
    
    # Final fallback: use fuzzy matching if rapidfuzz is available
    if best_match is None and 'process' in globals():
        try:
            # Extract all available metric names for fuzzy matching
            all_metric_names = [entry.get('name', '') for _, entry in slug_entries if entry.get('name')]
            original_metric_name = candidate_slugs[0] if candidate_slugs else metric_slug
            
            # Find closest match with decent similarity threshold
            matches = process.extract(original_metric_name, all_metric_names, limit=1)
            if matches and matches[0][1] >= 70:  # 70% similarity threshold
                matched_name = matches[0][0]
                # Find the entry with this name
                for _, entry in slug_entries:
                    if entry.get('name') == matched_name:
                        console.print(f"[dim]Fuzzy matched '{original_metric_name}' → '{matched_name}' ({matches[0][1]}% similarity)[/dim]")
                        return entry
        except Exception:
            pass  # Silently fall back if fuzzy matching fails
    
    return best_match


def prepare_assigned_metrics_for_workout(workout: dict, metric_catalog_index: Dict[str, dict], slug_entries: List[Tuple[str, dict]]) -> Tuple[List[dict], List[dict]]:
    """Convert parsed metrics into API-ready assigned metric payloads for a workout."""
    pending_metrics = workout.pop("pending_metrics", [])
    assigned_metrics = []
    skipped_metrics = []

    for metric in pending_metrics:
        metric_slug = normalise_metric_key(metric.get("metric_type"))
        candidate_slugs = []
        override_candidates = METRIC_NAME_OVERRIDES.get(metric_slug, [])
        candidate_slugs.extend(normalise_metric_key(c) for c in override_candidates if c)
        candidate_slugs.append(metric_slug)
        candidate_slugs = [slug for slug in candidate_slugs if slug]

        definition = _find_metric_definition(metric_slug, candidate_slugs, metric_catalog_index, slug_entries)

        if not definition:
            console.print(f"[yellow]Warning: Could not find metric definition for '{metric.get('metric_type')}' (tried: {', '.join(candidate_slugs)})[/yellow]")
            skipped_metrics.append(metric)
            continue
        else:
            # Log successful metric mapping
            console.print(f"[dim]✓ Mapped '{metric.get('metric_type')}' → '{definition.get('name')}' (ID: {definition.get('id')})[/dim]")

        assigned_entry = {
            "metric_id": definition["id"],
            "priority": len(assigned_metrics),
        }

        notes = (metric.get("notes") or "").strip()
        if notes:
            assigned_entry["description"] = notes

        value = metric.get("value")
        cast_value = _cast_metric_answer_value(value, definition.get("metric_type"))
        if cast_value not in (None, ""):
            assigned_entry["metric_answer"] = {"value": cast_value}

        assigned_metrics.append(assigned_entry)

    workout["assigned_metrics"] = assigned_metrics
    return assigned_metrics, skipped_metrics

def parse_line_as_metric(line: str):
    """
    Tries to parse a line as a metric entry.
    Format: @metric_name: value unit [notes]
    Examples:
        @weight: 185.5 lbs
        @body_fat: 15.2%
        @sleep: 7.5 hours feeling rested

    Returns metric dict or None if not a metric line.
    """
    line = line.strip()

    # Check if line starts with @
    if not line.startswith('@'):
        return None

    # Remove @ and split by colon
    if ':' not in line:
        return None

    metric_part, value_part = line[1:].split(':', 1)
    metric_type = metric_part.strip().lower()
    value_part = value_part.strip()

    if not value_part:
        # Allow blank metrics so coaches can assign placeholders
        return {
            'metric_type': metric_type,
            'value': None,
            'unit': '',
            'notes': ''
        }

    # Parse value part: "value unit optional notes"
    # Try to extract numeric value first
    value_match = re.match(r'([\d.]+)\s*(%|lbs|kg|inches|cm|hours|bpm|ms|/10)?(.*)$', value_part, re.IGNORECASE)

    if value_match:
        value_str, unit, notes = value_match.groups()

        try:
            value = float(value_str)
        except ValueError:
            value = None

        if value is not None:
            # Clean up unit
            if unit:
                unit = unit.strip()
                # Normalize units
                if unit == '/10':
                    unit = '1-10'
            else:
                unit = ''

            # Clean up notes
            notes = notes.strip() if notes else ''

            return {
                'metric_type': metric_type,
                'value': value,
                'unit': unit,
                'notes': notes
            }

    # Fallback for non-numeric values: treat as placeholder with optional notes
    return {
        'metric_type': metric_type,
        'value': None,
        'unit': '',
        'notes': value_part.strip()
    }

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
    """Parses a text file into a list of workout/nutrition dictionaries with interactive fuzzy matching.

    Supports both "Workout Date:" (training calendar) and "Nutrition Date:" (nutrition calendar) entries.
    Both types can be mixed in the same file.

    Returns:
        list: Workout/nutrition assignments ready for upload
    """
    content = read_text_file(plain_text_path)
    workouts = []

    # Split by both "Workout Date:" and "Nutrition Date:"
    # Use a regex that captures the header type and preserves it
    sections = re.split(r'(Workout Date|Nutrition Date):\s*', content)

    # sections will be like: ['', 'Workout Date', '2025-10-01\nSquat...', 'Nutrition Date', '2025-10-01\nMeal Pictures...']
    # Process in pairs (header, content)
    exercise_names = list(exercise_map.keys())

    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            break

        date_type = sections[i]  # Either "Workout Date" or "Nutrition Date"
        section = sections[i + 1]  # The content after the date header

        if not section.strip():
            continue

        # Determine workout_type based on date header
        workout_type_value = "nutrition" if date_type == "Nutrition Date" else "default"

        lines = section.strip().split('\n')
        workout_date = lines[0].strip()

        # Log what type of assignment we're parsing
        assignment_type_label = "nutrition assignment" if workout_type_value == "nutrition" else "workout"
        console.print(f"[dim]Parsing {assignment_type_label} for {workout_date}...[/dim]")

        workout = {
            "user_id": user_id, "workout_date": workout_date,
            "title": None, "weight_type": "lbs", "assigned_exercises": [],
            "published": True, "workout_type": workout_type_value,
        }

        start_line_index = 1
        if len(lines) > 1:
            potential_title = lines[1].strip()
            if potential_title and get_exercise_id(exercise_map, potential_title) is None and not re.match(r"^\d+\s*x", potential_title) and not potential_title.startswith('@'):
                workout["title"] = potential_title
                start_line_index = 2

        current_exercise = None
        kg_detected = False
        for line in lines[start_line_index:]:
            stripped_line = line.strip()
            if not stripped_line or stripped_line == "---" or stripped_line.startswith('(') or stripped_line.startswith('['):
                continue

            # Check if line is a metric
            parsed_metric = parse_line_as_metric(stripped_line)
            if parsed_metric:

                workout_metric = {
                    "metric_type": parsed_metric["metric_type"],
                    "value": parsed_metric.get("value"),
                    "unit": parsed_metric.get("unit"),
                    "notes": parsed_metric.get("notes"),
                    "metric_date": workout_date,
                }
                workout.setdefault("pending_metrics", []).append(workout_metric)

                if parsed_metric.get('value') is None:
                    note_display = f" (notes: {parsed_metric.get('notes')})" if parsed_metric.get('notes') else ""
                    console.print(f"[cyan]Found metric placeholder:[/cyan] {parsed_metric['metric_type']}{note_display}")
                else:
                    console.print(f"[cyan]Found metric:[/cyan] {parsed_metric['metric_type']} = {parsed_metric['value']} {parsed_metric['unit']}")
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

            exercise_id = get_exercise_id(exercise_map, stripped_line)
            if exercise_id is not None:
                ex_type = get_exercise_type(exercise_map, stripped_line)

                # Validate exercise type matches workout type
                if workout_type_value == "nutrition" and ex_type != "nutrition":
                    console.print(f"[yellow]Warning: '{stripped_line}' is a {ex_type} exercise, not a nutrition item. Skipping.[/yellow]")
                    continue
                elif workout_type_value == "default" and ex_type == "nutrition":
                    console.print(f"[yellow]Warning: '{stripped_line}' is a nutrition item, not a training exercise. Skipping.[/yellow]")
                    continue

                if current_exercise: workout["assigned_exercises"].append(current_exercise)
                current_exercise = {"exercise_id": exercise_id, "priority": len(workout["assigned_exercises"]), "assigned_sets": []}
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
                # Filter exercise names by type for fuzzy matching
                if workout_type_value == "nutrition":
                    filtered_names = [name for name in exercise_names if get_exercise_type(exercise_map, name) == 'nutrition']
                else:
                    filtered_names = [name for name in exercise_names if get_exercise_type(exercise_map, name) != 'nutrition']

                similar_exercises = get_similar_exercises(stripped_line.lower(), filtered_names)
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
                        chosen_exercise_id = get_exercise_id(exercise_map, chosen_exercise_name)
                        if chosen_exercise_id is not None:
                            current_exercise = {"exercise_id": chosen_exercise_id, "priority": len(workout["assigned_exercises"]), "assigned_sets": []}
                        else:
                            console.print(f"[yellow]Warning: Could not resolve exercise '{chosen_exercise_name}'.[/yellow]")
                else:
                    console.print(f"[yellow]Warning: Could not parse or find match for line: '{stripped_line}'[/yellow]")

        # After processing all lines, append any remaining current_exercise
        if current_exercise:
            workout["assigned_exercises"].append(current_exercise)
            
        # Include workouts that have either exercises OR metrics
        has_exercises = bool(workout["assigned_exercises"])
        has_metrics = bool(workout.get("pending_metrics"))
        
        if has_exercises or has_metrics:
            if kg_detected:
                workout["weight_type"] = "kgs"
                console.print(f"[green]Detected kg units—setting workout weight_type to 'kgs' for API compatibility.[/green]")
            workouts.append(workout)
            
            # Log what type of assignment was added
            assignment_type = "nutrition assignment" if workout.get('workout_type') == "nutrition" else "workout"
            if has_exercises and has_metrics:
                console.print(f"[dim]Added {assignment_type} with {len(workout['assigned_exercises'])} exercises and {len(workout.get('pending_metrics', []))} metrics[/dim]")
            elif has_exercises:
                console.print(f"[dim]Added {assignment_type} with {len(workout['assigned_exercises'])} exercises[/dim]")
            elif has_metrics:
                console.print(f"[dim]Added {assignment_type} with {len(workout.get('pending_metrics', []))} metrics only[/dim]")

    return workouts

def upload_workout(token, workout_data):
    """Uploads a single workout or nutrition assignment to the API."""
    url = f"{API_BASE_URL}/api/v1/workouts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        assignment_type = "nutrition assignment" if workout_data.get('workout_type') == "nutrition" else "workout"
        console.print(f"Uploading {assignment_type} for [cyan]{workout_data['workout_date']}[/cyan]...")

        # Debug: Print exercise IDs being uploaded
        if workout_data.get('assigned_exercises'):
            console.print("[dim]DEBUG: Exercise IDs in upload payload:[/dim]")
            for ex in workout_data['assigned_exercises']:
                console.print(f"[dim]  - exercise_id: {ex.get('exercise_id')}[/dim]")

        response = requests.post(url, headers=headers, json=workout_data)
        response.raise_for_status()
        console.print(f"✅ [bold green]Successfully uploaded {assignment_type}![/bold green]")
    except requests.exceptions.HTTPError as e:
        console.print(f"❌ [bold red]Upload failed.[/bold red] HTTP Error: {e.response.status_code}")
        console.print(f"[dim]API Response: {e.response.text}[/dim]")
