# Workout Management

## Purpose
This guide covers workout-related functionality including browsing history, uploading workouts from text files, formatting workouts to markup, and AI-assisted workout planning.

## Modules Covered

1. **format_tool.py** - Workout data formatting to custom markup
2. **upload_tool.py** - Workout parsing and uploading
3. **ai_chat_tool.py** - AI-powered workout planning
4. **coach_cli.py** - Workout management UI functions

## Workout Formatting (`format_tool.py`)

**File**: `format_tool.py` (87 lines)

### Purpose
Convert workout JSON data from the API into human-readable markup format for browsing, editing, and exporting.

### Main Function

**Function**: `format_workouts_to_markup(workouts, coach_user_id)`
**Location**: format_tool.py:12-86
**Returns**: String containing formatted workout markup

**Example Transformation**:

**Input (JSON)**:
```json
{
  "workout_date": "2025-10-01",
  "title": "Intensity Day",
  "assigned_exercises": [
    {
      "exercise": {"name": "Squat"},
      "assigned_sets": [
        {
          "sets": 3,
          "reps": 5,
          "weight": 405,
          "display_label": "3x5 @ 405",
          "actual_sets": [{"sets": 1, "reps": 5, "weight": 405}]
        }
      ]
    }
  ]
}
```

Additionally, the parser initialises an empty `metrics` list for later upload. Each metric line encountered in the markup extends this list with a dictionary that includes `value`, `unit`, and `notes`; the `value` field is set to `None` when the coach leaves the entry blank to create a placeholder assignment.

**Output (Markup)**:
```
Workout Date: 2025-10-01
Intensity Day

Squat
3x5 @ 405
(1x5 @ 405)

---
```

### Formatting Rules

#### 1. Workout Header
```python
workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")
output_lines.append(f"Workout Date: {workout_date.strftime('%Y-%m-%d')}")

if workout.get('title'):
    output_lines.append(f"{workout['title']}")

output_lines.append("")  # Blank line after header
```

#### 2. Workout Comments
Comments displayed as indented blocks with author name:

```python
if 'comments' in workout and workout['comments']:
    for comment in workout['comments']:
        body = clean_text(comment['body'] or "")
        if not body:
            continue

        comment_lines = body.split('\n')
        output_lines.append(f"\t[{comment['user']['full_name']}]: {comment_lines[0]}")
        for line in comment_lines[1:]:
            output_lines.append(f"\t{line}")
    output_lines.append("")
```

**Output**:
```
    [Coach Name]: Great work on this session!
    Keep pushing for those PRs.
```

#### 3. Exercises and Sets
```python
for exercise in workout.get('assigned_exercises', []):
    output_lines.append(f"{exercise['exercise']['name']}")

    for assigned_set in exercise['assigned_sets']:
        # Check if custom note
        if assigned_set.get('set_type') == 'custom':
            note_body = clean_text(assigned_set.get('body') or "")
            if note_body:
                output_lines.append(f"\t{note_body}")
        else:
            output_lines.append(f"{assigned_set['display_label']}")

        # Add actual sets (performance)
        if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
            for actual_set in assigned_set['actual_sets']:
                reps, weight, sets = actual_set.get('reps', ''), actual_set.get('weight', ''), actual_set.get('sets', '')
                output_lines.append(f"({sets}x{reps} @ {weight})")
```

**Output**:
```
Squat
3x5 @ 405
    Focus on hitting depth
(1x5 @ 405)
(1x5 @ 405)
(1x5 @ 405)
```

#### 4. Time-Based Sets
Special formatting for time-duration sets:

```python
if (assigned_set.get('time', 0) > 0 and
    (assigned_set.get('reps') is None or assigned_set.get('reps', 0) == 0) and
    assigned_set.get('weight_type') in ['bodyweight', 'RPE']):

    sets = assigned_set.get('sets', 1)
    formatted_time = format_time(assigned_set.get('time'))

    if formatted_time:
        if assigned_set.get('weight_type') == 'RPE' and assigned_set.get('weight_type_value'):
            rpe_val = assigned_set['weight_type_value']
            display = f"{sets} x {formatted_time} @ RPE {rpe_val}"
        else:
            display = f"{sets} x {formatted_time}"
        output_lines.append(f"{display}")
```

**Function**: `format_time(seconds)`
**Location**: format_tool.py:4-10

```python
def format_time(seconds):
    """Formats raw seconds (int) to MM:SS string for markup."""
    if not seconds or seconds <= 0:
        return None
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"
```

**Examples**:
- 600 seconds → "10:00"
- 90 seconds → "01:30"
- 3665 seconds → "61:05"

#### 5. Exercise Comments
```python
if 'comments' in exercise and exercise['comments']:
    output_lines.append("")
    for comment in exercise['comments']:
        body = clean_text(comment['body'] or "")
        if not body:
            continue

        comment_lines = body.split('\n')
        output_lines.append(f"\t[{comment['user']['full_name']}]: {comment_lines[0]}")
        for line in comment_lines[1:]:
            output_lines.append(f"\t{line}")
```

#### 6. Workout Separator
```python
output_lines.append("---\n")
```

Each workout block ends with `---` separator.

### Complete Example Output

```
Workout Date: 2025-10-01
Intensity Day

    [Coach Name]: Focus on form today, not just weight.

Squat
3x5 @ 405
    Keep chest up, hit depth
(1x5 @ 405)
(1x5 @ 405)
(1x5 @ 405)

    [Athlete Name]: Felt strong on all reps
    [Coach Name]: Excellent depth!

Bench Press
2x5 @ 85%
1xAMRAP @ 200
(1x8 @ 200)

---

Workout Date: 2025-10-03

Run
1x20:00 @ RPE 7

---
```

## Browse History Function

**Function**: `browse_history(token, client, coach_user_id)`
**Location**: coach_cli.py:72-100

**Purpose**: Generate a formatted workout history file and open in editor.

**Flow**:
```
Get workout history from cache
    ↓
Filter invalid workouts (no date)
    ↓
Sort by date (ascending)
    ↓
Format to markup
    ↓
Save to client directory with timestamp
    ↓
Open in user's default editor
```

**Implementation**:
```python
def browse_history(token, client, coach_user_id):
    client_name = client['full_name']
    client_dir = get_client_dir(client['id'])
    workouts = get_workout_history(token, client)

    valid_workouts = [w for w in workouts if w.get('workout_date')]
    if not valid_workouts:
        console.input("\nCould not load workout history. Press Enter to return.")
        return

    valid_workouts.sort(key=lambda w: w['workout_date'])
    markup_content = format_workouts_to_markup(valid_workouts, coach_user_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_client_name = client_name.replace(' ', '_')
    history_filename = f"{safe_client_name}_history_{timestamp}.txt"
    history_filepath = os.path.join(client_dir, history_filename)

    with open(history_filepath, 'w', encoding='utf-8') as f:
        f.write(markup_content)

    console.print(f"\nWorkout history saved to:\n[green]{history_filepath}[/green]")

    editor_cmd = get_default_editor()
    editor_name = ' '.join(editor_cmd)
    console.print(f"\nOpening history in [bold green]{editor_name}[/bold green]...")
    console.print("[dim]Close the editor to continue...[/dim]")

    original_dir = os.getcwd()
    try:
        os.chdir(client_dir)
        subprocess.run(editor_cmd + [history_filename], shell=False, check=False)
    finally:
        os.chdir(original_dir)
```

**File Naming**: `{ClientName}_history_{YYYYmmdd_HHMMSS}.txt`

**Example**: `John_Doe_history_20251011_143000.txt`

## Workout Upload System (`upload_tool.py`)

**File**: `upload_tool.py` (188 lines)

### Purpose
Parse workout files written in custom markup format and upload to Turnkey Coach API.

### Main Parsing Function

**Function**: `parse_workouts_from_file(plain_text_path, user_id, exercise_map)`
**Location**: upload_tool.py:142-296
**Returns**: Tuple `(assignments, metrics)` where `assignments` contains workout/nutrition payloads and `metrics` captures both populated and placeholder metric entries

### Parsing Logic

#### 1. Workout Sections
Split file by "Workout Date:" delimiter:

```python
content = read_text_file(plain_text_path)
workout_sections = [s for s in re.split(r'Workout Date:\s*', content) if s.strip()]
```

#### 2. Workout Initialization
```python
for section in workout_sections:
    lines = section.strip().split('\n')
    workout = {
        "user_id": user_id,
        "workout_date": lines[0].strip(),  # First line is date
        "title": None,
        "weight_type": "lbs",  # Default, may be changed
        "assigned_exercises": [],
        "published": True,
    }
```

#### 3. Optional Title Detection
```python
start_line_index = 1
if len(lines) > 1:
    potential_title = lines[1].strip()
    # If line is not an exercise name and not a set prescription, it's the title
    if potential_title and potential_title.lower() not in exercise_map and not re.match(r"^\d+\s*x", potential_title):
        workout["title"] = potential_title
        start_line_index = 2
```

#### 4. Line-by-Line Processing
```python
current_exercise = None
kg_detected = False

for line in lines[start_line_index:]:
    stripped_line = line.strip()

    # Skip empty lines, separators, and certain comments
    if not stripped_line or stripped_line == "---" or stripped_line.startswith('(') or stripped_line.startswith('['):
        continue

    # Detect inline metrics before handling exercises/sets
    parsed_metric = parse_line_as_metric(stripped_line)
    if parsed_metric:
        metric_data = {
            "user_id": user_id,
            "metric_date": workout_date,
            **parsed_metric,
        }
        metrics.append(metric_data)
        if parsed_metric.get("value") is None:
            console.print(f"[cyan]Found metric placeholder:[/cyan] {parsed_metric['metric_type']}")
        else:
            console.print(f"[cyan]Found metric:[/cyan] {parsed_metric['metric_type']} = {parsed_metric['value']} {parsed_metric['unit']}")
        continue

    is_indented = len(line) > len(line.lstrip())

    # Handle indented notes
    if is_indented:
        if stripped_line.startswith('>'):  # Private note, skip
            continue
        if current_exercise:
            # Add as custom note to current exercise
            note_set = {
                "set_type": "custom",
                "body": stripped_line,
                "priority": len(current_exercise["assigned_sets"]),
                "rep_type": "default_rep_type",
                "distance": 0.0,
                "distance_unit": None,
                "time": 0,
                "reps": None,
                "sets": None,
                "weight": None
            }
            current_exercise["assigned_sets"].append(note_set)
        continue

    # Check if line is an exercise name
    if stripped_line.lower() in exercise_map:
        if current_exercise:
            workout["assigned_exercises"].append(current_exercise)
        ex_id = exercise_map[stripped_line.lower()]
        current_exercise = {
            "exercise_id": ex_id,
            "priority": len(workout["assigned_exercises"]),
            "assigned_sets": []
        }
        continue

    # Try to parse as a set
    parsed_set = parse_line_as_set(stripped_line)
    if parsed_set and current_exercise:
        parsed_set["priority"] = len(current_exercise["assigned_sets"])
        current_exercise["assigned_sets"].append(parsed_set)
        # Check for kg units
        if parsed_set.get("parsed_units") == "kg":
            kg_detected = True
```

#### 5. Fuzzy Exercise Matching

If exercise name not found, use rapidfuzz for suggestions:

```python
def get_similar_exercises(exercise_name: str, exercise_names: list[str], limit: int = 5):
    """Finds similar exercise names using fuzzy matching."""
    matches = process.extract(exercise_name, exercise_names, limit=limit)
    return [match[0] for match in matches if match[1] > 80]  # 80% similarity threshold
```

**Interactive Selection**:
```python
similar_exercises = get_similar_exercises(stripped_line.lower(), exercise_names)
if similar_exercises:
    console.print(f"\nExercise [yellow]'{stripped_line}'[/yellow] not found. Did you mean one of these?")
    for i, name in enumerate(similar_exercises, 1):
        console.print(f"  [[bold]{i}[/bold]] {name.title()}")
    console.print("  [[bold]s[/bold]] Skip this line")

    chosen_exercise_name = None
    while True:
        choice = console.input("Enter a number or 's' to skip > ").lower()
        if choice == 's':
            break
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(similar_exercises):
                chosen_exercise_name = similar_exercises[choice_idx]
                break
        except ValueError:
            pass
        console.print("[red]Invalid input.[/red]")

    if chosen_exercise_name:
        ex_id = exercise_map[chosen_exercise_name]
        current_exercise = {
            "exercise_id": ex_id,
            "priority": len(workout["assigned_exercises"]),
            "assigned_sets": []
        }
```

### Set Parsing Function

**Function**: `parse_line_as_set(line)`
**Location**: upload_tool.py:18-82
**Returns**: Dict with set data or None if unparseable

**Supported Formats**:

#### 1. Time-Based
**Pattern**: `{sets} x {MM:SS} [@ RPE {value}]`

**Examples**:
- `3 x 01:30` → 3 sets of 1:30 duration
- `1 x 20:00 @ RPE 7` → 1 set of 20:00 at RPE 7

**Regex**: `r"(\d+)\s*x\s*(\d{1,2}:\d{2})(?:\s*@\s*(RPE\s*\d+\.?\d*))?"`

**Parsing**:
```python
sets, duration_str, rpe_str = time_match.groups()
minutes, seconds = map(int, duration_str.split(':'))
total_seconds = (minutes * 60) + seconds

parsed = {
    **base_set,
    "sets": int(sets),
    "time": total_seconds,
    "weight": None
}

if rpe_str:
    parsed["weight_type"] = "RPE"
    parsed["weight_type_value"] = float(rpe_str.upper().replace("RPE", "").strip())
else:
    parsed["weight_type"] = "bodyweight"
```

#### 2. RPE-Based
**Pattern**: `{sets} x {reps} @ RPE {value}`

**Examples**:
- `3 x 5 @ RPE 8` → 3 sets of 5 reps at RPE 8
- `1 x AMRAP @ RPE 10` → 1 AMRAP set at RPE 10

**Regex**: `r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*RPE\s*(\d+\.?\d*)"`

**Parsing**:
```python
sets, reps, rpe = match.groups()
parsed = {
    **base_set,
    "sets": int(sets),
    "weight": None,
    "weight_type": "RPE",
    "weight_type_value": float(rpe)
}

if reps.upper() == 'AMRAP':
    parsed["rep_type"] = "AMRAP"
else:
    parsed["reps"] = int(reps)
```

#### 3. Percentage-Based
**Pattern**: `{sets} x {reps} @ {percentage}%`

**Examples**:
- `5 x 5 @ 80%` → 5 sets of 5 reps at 80% of 1RM
- `3 x 3 @ 90%` → 3 sets of 3 reps at 90%

**Regex**: `r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*(\d+\.?\d*)\s*%"`

**Parsing**:
```python
sets, reps, percent = match.groups()
parsed = {
    **base_set,
    "sets": int(sets),
    "weight": None,
    "weight_type": "percent",
    "weight_type_value": float(percent)
}

if reps.upper() == 'AMRAP':
    parsed["rep_type"] = "AMRAP"
else:
    parsed["reps"] = int(reps)
```

#### 4. Weight-Based
**Pattern**: `{sets} x {reps} @ {weight} [{lbs|kg}]`

**Examples**:
- `3 x 5 @ 405` → 3 sets of 5 reps at 405 (default unit)
- `5 x 5 @ 100 kg` → 5 sets of 5 reps at 100 kg

**Regex**: `r"(\d+)\s*x\s*([a-zA-Z0-9]+)\s*@\s*(\d+\.?\d*)(?:\s*(lbs|kg))?"`

**Parsing**:
```python
sets, reps, weight, units = match.groups()
parsed = {
    **base_set,
    "sets": int(sets),
    "weight": float(weight),
    "weight_type": "default_weight_type"
}

if reps.upper() == 'AMRAP':
    parsed["rep_type"] = "AMRAP"
else:
    parsed["reps"] = int(reps)

if units:
    parsed["parsed_units"] = units.lower()  # For kg detection
```

#### 5. Bodyweight
**Pattern**: `{sets} x {reps}` (no weight specified)

**Examples**:
- `3 x 10` → 3 sets of 10 reps bodyweight
- `5 x AMRAP` → 5 AMRAP sets bodyweight

**Regex**: `r"(\d+)\s*x\s*([a-zA-Z0-9]+)"`

**Parsing**:
```python
sets, reps = match.groups()
parsed = {
    **base_set,
    "sets": int(sets),
    "weight": None,
    "weight_type": "bodyweight"
}

if reps.upper() == 'AMRAP':
    parsed["rep_type"] = "AMRAP"
else:
    parsed["reps"] = int(reps)
```

### Unit Detection

After parsing all sets, check if kg was detected:

```python
if kg_detected:
    workout["weight_type"] = "kgs"  # API expects "kgs" not "kg"
    console.print(f"[green]Detected kg units—setting workout weight_type to 'kgs' for API compatibility.[/green]")
```

### Upload Function

**Function**: `upload_workout(token, workout_data)`
**Location**: upload_tool.py:177-188

**API Endpoint**: `POST /api/v1/workouts`

**Implementation**:
```python
def upload_workout(token, workout_data):
    url = f"{API_BASE_URL}/api/v1/workouts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        console.print(f"Uploading workout for [cyan]{workout_data['workout_date']}[/cyan]...")
        response = requests.post(url, headers=headers, json=workout_data)
        response.raise_for_status()
        console.print(f"✅ [bold green]Successfully uploaded workout![/bold green]")
    except requests.exceptions.HTTPError as e:
        console.print(f"❌ [bold red]Upload failed.[/bold red] HTTP Error: {e.response.status_code}")
        console.print(f"[dim]API Response: {e.response.text}[/dim]")
```

### Uploader UI

**Function**: `run_uploader_tool(token, client, exercise_map)`
**Location**: coach_cli.py:103-132

**Flow**:
```
Check client directory for .txt files
    ↓
Display file list
    ↓
User selects file
    ↓
Parse workouts from file
    ↓
Upload each workout sequentially
    ↓
Display success/error for each
```

## AI Chat Tool (`ai_chat_tool.py`)

**File**: `ai_chat_tool.py` (302 lines)

### Purpose
AI-powered workout planning assistant with context loading, workout history integration, and direct upload capability.

### Main Function

**Function**: `run_ai_chat(token, user_id, client, exercise_map)`
**Location**: ai_chat_tool.py:33-302

**Features**:
1. Load workout history as context
2. Load custom coaching context files
3. Interactive chat with OpenAI/xAI
4. Edit AI responses in text editor
5. Save edited plans to client directory
6. Upload AI-generated workouts directly to platform

### Context Loading

#### 1. Workout History Context
```python
workouts = get_workout_history(token, client)
valid_workouts = [w for w in workouts if w.get('workout_date')]
valid_workouts.sort(key=lambda w: w['workout_date'])
markup_content = format_workouts_to_markup(valid_workouts, user_id)
```

#### 2. Markup Guide Context
```python
try:
    markup_guide = read_text_file("markup.md")
except FileNotFoundError:
    markup_guide = "Markup guide not found. Use standard workout formatting."
```

#### 3. Custom Context Files
```python
custom_context = ""
if input("Upload custom context file? (y/n): ").lower() == 'y':
    context_dir = get_coaching_context_dir()
    files = [f for f in os.listdir(context_dir) if f.endswith(('.md', '.txt'))]

    # User selects files
    for idx in indices:
        if 0 <= idx < len(files):
            filepath = os.path.join(context_dir, files[idx])
            custom_context += read_text_file(filepath) + "\n\n"
```

**Context Directory**: `~/Turnkey/shared/coaching_context/`

#### 4. System Prompt Assembly
```python
system_prompt = f"You are an AI assistant for strength coaching. Use the following markup guide for workouts: {markup_guide}. The client's workout history is: {markup_content}"

if custom_context:
    system_prompt += f"\nAdditional context: {custom_context}"
```

### LLM Provider Configuration

**Supported Providers**:
1. **OpenAI** (`openai`)
   - Model: `gpt-5`
   - Base URL: Default OpenAI API
2. **xAI** (`xai`)
   - Model: `grok-4`
   - Base URL: `https://api.x.ai/v1`

**Setup**:
```python
provider, api_key = get_llm_credentials()

if provider == 'xai':
    client_ai = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    model = "grok-4"
elif provider == 'openai':
    client_ai = OpenAI(api_key=api_key)
    model = "gpt-5"
```

### Chat Loop

**Main Loop** (ai_chat_tool.py:154-302):

**Available Commands**:
- Normal text → Send to AI
- `exit` or `quit` → Exit chat
- `edit` → Edit last AI response in editor
- `upload` → Upload AI response or file to API

#### Edit Command

```python
if user_input.lower() == 'edit':
    last_response = messages[-1]["content"]

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', dir=client_dir, encoding='utf-8') as temp_file:
        temp_file.write(last_response)
        temp_path = temp_file.name

    # Open in editor
    editor_cmd = get_default_editor()
    subprocess.run(editor_cmd + [temp_path], check=False)

    # Read edited content
    edited_content = read_text_file(temp_path).strip()
    messages[-1]["content"] = edited_content

    # Optionally save
    save_name = input("Save edited plan to client directory? Enter filename (or blank to skip): ").strip()
    if save_name:
        save_path = os.path.join(client_dir, save_name)
        write_text_file(save_path, edited_content)

    # Clean up temp file
    os.remove(temp_path)
```

#### Upload Command

**Upload Options**:
1. Upload previous AI response
2. Select file from client directory

```python
if choice == '1':
    # Upload previous AI response
    content = messages[-1]["content"]
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        workouts_parsed = parse_workouts_from_file(temp_path, client['id'], exercise_map)
        for workout in workouts_parsed:
            upload_workout(token, workout)
    finally:
        os.remove(temp_path)

elif choice == '2':
    # Select and upload file
    files = [f for f in os.listdir(client_dir) if f.endswith('.txt') or f.endswith('.md')]
    # Display file list, user selects, then upload
```

### Token Estimation

**Function**: `estimate_token_count(text)`
**Location**: ai_chat_tool.py:20-22

```python
def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (approximately 4 characters per token for English text)."""
    return len(text) // 4
```

**Display**:
```
Context loaded: ~12,450 tokens
```

Helps coaches understand how much context they're using.

### API Call Configuration

```python
extra_params = {}

# Only add temperature for non-reasoning models
if not model.startswith(("gpt-5", "o1-")):
    extra_params["temperature"] = 0.7

    # Use correct parameter based on provider
    if provider == 'openai':
        extra_params['max_completion_tokens'] = 1500
    else:
        extra_params['max_tokens'] = 1500

response = client_ai.chat.completions.create(
    model=model,
    messages=messages,
    **extra_params
)
```

## Best Practices for Developers

### 1. Always Use UTF-8 Encoding
```python
from encoding_utils import safe_open, read_text_file, write_text_file

# Use these instead of built-in open()
content = read_text_file(filepath)
write_text_file(filepath, content)
```

### 2. Validate Exercise Names
```python
if exercise_name.lower() not in exercise_map:
    # Use fuzzy matching
    similar = get_similar_exercises(exercise_name, exercise_names)
    # Prompt user to select correct match
```

### 3. Handle Temp Files Carefully
```python
temp_file = tempfile.NamedTemporaryFile(delete=False, ...)
try:
    # Use temp file
    subprocess.run(editor_cmd + [temp_file.name])
    content = read_text_file(temp_file.name)
finally:
    # Always clean up
    try:
        os.remove(temp_file.name)
    except OSError:
        pass
```

### 4. Preserve Directory Context
```python
original_dir = os.getcwd()
try:
    os.chdir(client_dir)
    subprocess.run(editor_cmd + [filename])
finally:
    os.chdir(original_dir)  # Always restore
```

### 5. Validate Parsed Data
```python
if not reps or not weight:
    continue  # Skip invalid sets

if not workout["assigned_exercises"]:
    # Don't add empty workouts
```

## Troubleshooting

### Exercise Name Not Found
**Symptom**: Parser cannot find exercise, fuzzy matching returns no results

**Solutions**:
1. Update exercise list (option 'u' in tools menu)
2. Check spelling in text file
3. Use `id: {exercise_id}` format as failsafe
4. Verify exercise exists in platform

### Upload Fails
**Symptom**: "Upload failed" HTTP error

**Solutions**:
1. Check JSON structure matches API expectations
2. Verify token is valid
3. Review API response text for specific error
4. Validate date format (YYYY-MM-DD)
5. Ensure all required fields present

### AI Context Too Large
**Symptom**: API error about context length

**Solutions**:
1. Reduce number of workouts in history
2. Use shorter custom context files
3. Summarize workout history before passing to AI
4. Use smaller date range for history

### Editor Not Opening
**Symptom**: Subprocess error or no editor appears

**Solutions**:
1. Verify editor command in settings
2. Test editor command in terminal
3. Use absolute path for editor
4. Check editor is installed
5. Try different editor (e.g., notepad, nano)

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
