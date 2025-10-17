# API Client and Authentication

## Purpose
This guide covers the API client layer, authentication mechanisms, token caching, and shared utility functions in `api_client.py`.

## Module Overview

**File**: `api_client.py` (618 lines)

**Core Responsibilities**:
- API authentication and token management with workspace isolation
- Client list retrieval with role grouping (Strength/Nutrition)
- Workout history management with smart sync and deletion detection
- Workout deletion operations (single and batch)
- Exercise database management with type information
- Metric catalog access
- Shared utility functions
- Headless mode support for bulk operations

## API Configuration

### Base URL
```python
API_BASE_URL = "https://app.turnkey.coach"
```

All API endpoints are prefixed with this base URL.

## Authentication System

### Token-Based Authentication

The system uses Bearer token authentication with automatic caching and refresh.

### Authentication Flow

#### 1. Token Cache Check (`load_auth_data()`)
**Location**: api_client.py:481-496

```python
def load_auth_data():
    token_cache_file = get_token_cache_file()
    # Try current workspace first
    if os.path.exists(token_cache_file):
        data = safe_json_load(token_cache_file)
        if data:
            try:
                if datetime.fromisoformat(data.get("expires_at")) > datetime.now():
                    return data.get("token"), data.get("user_id")
            except (KeyError, TypeError, ValueError):
                pass
    # Fallback: scan other known locations to ease migration/first-run
    token, user_id = _scan_for_legacy_token_cache()
    if token and user_id:
        return token, user_id
    return None, None
```

**Cache Location**: `~/Turnkey-{workspace}/shared/.tokencache` (workspace-aware)

**Cache Structure**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 12345,
  "expires_at": "2025-10-11T15:30:00.000000"
}
```

**Expiry**: 1 hour from creation

#### 2. Stored Credentials Fallback (`get_stored_credentials()`)
**Location**: settings.py:94-111

If token cache is invalid, attempt auto-login with stored credentials:
```python
email, password = get_stored_credentials()
if email and password:
    console.print("[dim]Auto-logging in with stored credentials...[/dim]")
    # Proceed with login
```

**Credentials Location**: `~/.turnkey_coach_settings.json`

**Encryption**: Fernet symmetric encryption (cryptography library)

#### 3. Manual Login Prompt
**Location**: api_client.py:171-201

If no stored credentials, prompt user:
```python
email = console.input("[bold]Enter your email:[/bold] ")
password = getpass.getpass("Enter your password: ")
```

#### 4. API Authentication Request
**Endpoint**: `POST /users/tokens/sign_in`

**Request Payload**:
```json
{
  "email": "coach@example.com",
  "password": "secret_password"
}
```

**Response**:
```json
{
  "token": "eyJhbGci...",
  "resource_owner": {
    "id": 12345,
    "full_name": "Coach Name",
    "email": "coach@example.com"
  }
}
```

#### 4a. Legacy Token Scanning (New in v1.5)
**Location**: api_client.py:457-478

**Purpose**: Scan for tokens in other workspaces to ease migration and multi-workspace setup.

```python
def _scan_for_legacy_token_cache():
    """Search common legacy/shared locations for an existing .tokencache.
    Returns the first valid (token, user_id) tuple if found, else (None, None).
    """
    import glob
    candidates = []
    # Legacy single-dir path
    candidates.append(os.path.expanduser(os.path.join('~', 'Turnkey', 'shared', '.tokencache')))
    # Workspace paths: Turnkey-*/shared/.tokencache
    workspace_glob = os.path.expanduser(os.path.join('~', 'Turnkey-*', 'shared', '.tokencache'))
    candidates.extend(glob.glob(workspace_glob))

    for path in candidates:
        try:
            data = safe_json_load(path)
            if not data:
                continue
            exp = data.get('expires_at')
            if exp and datetime.fromisoformat(exp) > datetime.now():
                return data.get('token'), data.get('resource_owner', {}).get('id') or data.get('user_id')
        except Exception:
            continue
    return None, None
```

#### 5. Token Caching (`save_auth_data()`)
**Location**: api_client.py:449-455

```python
def save_auth_data(token, user_id):
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat()
    }
    token_cache_file = get_token_cache_file()
    # Ensure parent directory exists (first run on fresh systems)
    os.makedirs(os.path.dirname(token_cache_file), exist_ok=True)
    safe_json_dump(auth_data, token_cache_file)
```

### Main Authentication Function

**Function**: `get_access_token()`
**Location**: api_client.py:572-607
**Returns**: `(token: str, user_id: int)` or `(None, None)`

**Complete Flow (Workspace-Aware)**:
```
get_access_token()
    ↓
Check workspace-specific token cache (~/.Turnkey-{workspace}/shared/.tokencache)
    ↓ [valid]
Return cached token + user_id
    ↓ [invalid/missing]
Scan for legacy tokens in other workspaces
    ↓ [found in other workspace]
Reuse token (auto-migration)
    ↓ [no legacy tokens]
Check stored credentials for current workspace (settings.py)
    ↓ [found]
Auto-login with credentials
    ↓ [not found]
Prompt for email/password
    ↓
POST /users/tokens/sign_in
    ↓ [success]
Save token cache to workspace directory
Return token + user_id
    ↓ [failure]
Display error
Return (None, None)
```

## Client Management

### Fetching Client List

**Function**: `get_clients(token, user_id)`
**Location**: api_client.py:499-545
**Endpoint**: `GET /api/v1/users/{user_id}/clients`

**Purpose**: Retrieve all clients associated with the authenticated coach, with role grouping.

**Request**:
```python
headers = {"Authorization": f"Bearer {token}"}
url = f"{API_BASE_URL}/api/v1/users/{user_id}/clients"
response = requests.get(url, headers=headers)
```

**Response Structure**:
```json
[
  {
    "client": {
      "id": 101,
      "full_name": "John Doe",
      "email": "john@example.com"
    },
    "coach": {
      "id": 12345,
      "full_name": "Coach Name"
    },
    "display_coach_type": "Workout"
  },
  {
    "client": {
      "id": 101,
      "full_name": "John Doe",
      "email": "john@example.com"
    },
    "coach": {
      "id": 12345,
      "full_name": "Coach Name"
    },
    "display_coach_type": "Nutrition"
  },
  ...
]
```

**Data Transformation** (Groups roles by coach):
The function aggregates relationships and groups roles per coach:

```python
clients_data = {}
for rel in relationships:
    client_info, coach_info = rel.get('client'), rel.get('coach')
    client_id = client_info.get('id')

    if client_id not in clients_data:
        clients_data[client_id] = {
            'id': client_id,
            'full_name': client_info.get('full_name', 'N/A'),
            'coach_roles': {}  # Group roles by coach name
        }

    # Group roles by coach name
    coach_name = coach_info.get('full_name', 'Unknown')
    coach_type = rel.get('display_coach_type', 'Coach')
    # Replace "Workout" with "Strength" for clarity
    if coach_type == 'Workout':
        coach_type = 'Strength'

    if coach_name not in clients_data[client_id]['coach_roles']:
        clients_data[client_id]['coach_roles'][coach_name] = []
    clients_data[client_id]['coach_roles'][coach_name].append(coach_type)

# Convert coach_roles dict to coaches list with proper formatting
for client_data in clients_data.values():
    coaches_list = []
    for coach_name, roles in client_data['coach_roles'].items():
        # Sort roles for consistent display (Nutrition, Strength)
        sorted_roles = sorted(roles)
        roles_str = ', '.join(sorted_roles)
        coaches_list.append(f"{coach_name} ({roles_str})")
    client_data['coaches'] = coaches_list
    del client_data['coach_roles']
```

**Return Format**:
```python
[
  {
    'id': 101,
    'full_name': 'John Doe',
    'coaches': ['Coach Name (Nutrition, Strength)', 'Assistant (Strength)']
  },
  ...
]
```

**Key Changes in v1.5**:
- Replaces "Workout" with "Strength" for clarity
- Groups multiple roles per coach (e.g., one coach handles both Strength and Nutrition)
- Sorts roles alphabetically for consistency

## Workout History Management

### Overview

The workout history system implements **smart sync** with deletion detection, incremental caching, and headless mode for bulk operations.

### Primary Functions

#### 1. `get_workout_history()` - Interactive Mode
**Location**: api_client.py:170-240
**Signature**: `get_workout_history(token, client, force_refresh=False)`

**Parameters**:
- `token`: Authentication token
- `client`: Client dictionary with 'id' key
- `force_refresh`: If True, bypass cache and re-download all workouts

**Returns**: List of complete workout dictionaries

**Features**:
- Rich console status messages
- Progress indicators
- User-facing error messages
- Deletion detection and reporting

#### 2. `get_workout_history_headless()` - Silent Mode (New in v1.5)
**Location**: api_client.py:242-305
**Signature**: `get_workout_history_headless(token, client, force_refresh=False)`

**Purpose**: Silent version for bulk sync operations - no Rich console output.

**Differences from interactive mode**:
- No console.print() or console.status() calls
- No progress indicators
- Silent error handling (returns empty list on failure)
- Used by `bulk_sync.py` for parallel client syncing

### Caching Strategy

#### Cache Files
1. **Workout Data**: `~/Turnkey-{workspace}/clients/{client_id}/workouts_user_{client_id}.json`
   - Complete workout details
   - Includes exercises, sets, comments, metrics
   - Workspace-isolated

2. **Workout Index**: `~/Turnkey-{workspace}/clients/{client_id}/workouts_index.json`
   - Metadata only (workout IDs and update timestamps)
   - Used by feed_tool.py for timestamp-based incremental updates

#### Smart Sync Logic Flow (New in v1.5)

**Key Innovation**: Detects deletions by comparing server IDs with cached IDs.

```
get_workout_history(token, client, force_refresh=False)
    ↓
[force_refresh=True] → Download all workouts from API
    ↓
[force_refresh=False] → Check cache exists
    ↓ [no cache]
Full download (first-time sync)
    ↓ [cache exists]
Load existing workouts
Validate cache (has workout_date and id fields)
    ↓ [invalid]
Full download (corrupted cache)
    ↓ [valid]
**SMART SYNC** (Deletion Detection):
    ├─→ Fetch lightweight workout ID list from server (GET /api/v1/workouts)
    ├─→ Extract server_workout_ids = {1001, 1002, 1003, ...}
    ├─→ Extract cached_workout_ids = {1001, 1002, 1004, ...}
    ├─→ Detect deletions: deleted_ids = cached - server  # {1004}
    ├─→ Detect additions: missing_ids = server - cached  # {1003}
    ├─→ Remove deleted workouts from cache
    └─→ Fetch only missing/new workout details (parallel)
    ↓
[deletions detected] → Print warning, remove from cache
[new workouts detected] → Download details for new IDs only
    ↓
Merge valid_workouts + new_workouts
Save to cache
Return complete workout list
    ↓ [no changes]
Return existing cache (skip API calls)
```

**Benefits of Smart Sync**:
- Detects when workouts are deleted on the server
- Removes stale workouts from local cache
- Only fetches changed/new workouts (not full history)
- Graceful fallback on API errors (uses cached data)

### Implementation Details

#### Smart Sync with Deletion Detection
**Location**: api_client.py:199-240

```python
# Load existing cache
existing_workouts = safe_json_load(workout_cache_path, default=[])
if not existing_workouts:
    return get_workout_history(token, client, force_refresh=True)

# Filter for valid workouts
valid_workouts = [w for w in existing_workouts if w.get('workout_date') and w.get('id')]
if not valid_workouts:
    return get_workout_history(token, client, force_refresh=True)

# Smart sync: Compare IDs to detect deletions and additions
with console.status("[dim]Checking for workout changes...[/dim]"):
    server_workout_ids = _get_workout_ids_from_api(token, client_id)
    if not server_workout_ids:  # API error - use cached data
        console.print("[yellow]Could not fetch server workout list. Using cached data.[/yellow]")
        return existing_workouts

    cached_workout_ids = {w['id'] for w in valid_workouts}

    # Detect deletions
    deleted_ids = cached_workout_ids - server_workout_ids
    if deleted_ids:
        console.print(f"[yellow]Detected {len(deleted_ids)} deleted workout(s). Removing from cache...[/yellow]")
        valid_workouts = [w for w in valid_workouts if w['id'] not in deleted_ids]

    # Detect new workouts that need to be fetched
    missing_ids = server_workout_ids - cached_workout_ids

    if missing_ids:
        console.print(f"[green]Found {len(missing_ids)} new workout(s). Downloading details...[/green]")
        # Optimize: fetch from latest date forward
        if valid_workouts:
            latest_date_str = max(w['workout_date'] for w in valid_workouts)
            start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)
            new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())
        else:
            # No cached workouts left, download everything
            new_workouts = _download_workouts_from_api(token, client_id)

        # Combine and save
        all_workouts = valid_workouts + new_workouts
        safe_json_dump(all_workouts, workout_cache_path, indent=4)
        return all_workouts
    elif deleted_ids:
        # Only deletions occurred, save the cleaned cache
        safe_json_dump(valid_workouts, workout_cache_path, indent=4)
        return valid_workouts
    else:
        # No changes detected
        console.print("[dim]Workout history is up to date.[/dim]")
        return existing_workouts
```

#### Helper: Get Workout IDs (Lightweight)
**Location**: api_client.py:110-122

**Purpose**: Fetch only workout IDs (no details) for comparison.

```python
def _get_workout_ids_from_api(token, client_id):
    """Lightweight function to get only workout IDs from server for sync comparison."""
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}

    try:
        response = requests.get(list_url, headers=headers, params=params)
        response.raise_for_status()
        workouts_summary = response.json()
        return {summary['id'] for summary in workouts_summary}  # Return set of IDs
    except requests.exceptions.RequestException:
        return set()
```

#### Download Function
**Location**: api_client.py:73-95

```python
def _download_workouts_from_api(token, client_id, start_date=None):
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {
        "user_id": client_id,
        "sort": "ascending",
        "published": True
    }
    if start_date:
        params["start_date"] = start_date

    # Fetch workout summaries
    response = requests.get(list_url, headers=headers, params=params)
    workouts_summary = response.json()

    # Fetch details for each workout
    detailed_workouts = []
    for summary in workouts_summary:
        workout_id = summary['id']
        detail_url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
        detail_response = requests.get(detail_url, headers=headers)
        if detail_response.status_code == 200:
            detailed_workouts.append(detail_response.json())

    return detailed_workouts
```

**API Endpoints Used**:
1. `GET /api/v1/workouts?user_id={id}&sort=ascending&published=true&start_date={date}`
   - Returns list of workout summaries
2. `GET /api/v1/workouts/{workout_id}`
   - Returns complete workout details (called for each workout)

### Workout Data Structure

**Example**:
```json
{
  "id": 5001,
  "workout_date": "2025-10-01",
  "title": "Intensity Day",
  "completed": true,
  "weight_type": "lbs",
  "user_id": 101,
  "published": true,
  "comments": [
    {
      "id": 1001,
      "body": "Great work today!",
      "user": {"id": 12345, "full_name": "Coach Name"},
      "updated_at": "2025-10-01T14:30:00Z",
      "parent_type": "Workout",
      "parent_id": 5001
    }
  ],
  "assigned_exercises": [
    {
      "id": 10001,
      "exercise": {"id": 42, "name": "Squat"},
      "priority": 0,
      "assigned_sets": [
        {
          "sets": 3,
          "reps": 5,
          "weight": 405,
          "weight_type": "default_weight_type",
          "set_type": "default",
          "rep_type": "default_rep_type",
          "priority": 0,
          "display_label": "3x5 @ 405",
          "actual_sets": [
            {"sets": 1, "reps": 5, "weight": 405}
          ]
        }
      ],
      "comments": [
        {
          "id": 1002,
          "body": "Hit depth on all reps",
          "user": {"id": 101, "full_name": "John Doe"},
          "updated_at": "2025-10-01T13:45:00Z",
          "parent_type": "AssignedExercise",
          "parent_id": 10001
        }
      ]
    }
  ]
}
```

## Workout Deletion Operations (New in v1.5)

### Overview
The system provides both single workout deletion and batch deletion with filtering.

### Function: `delete_workout_by_id()`
**Location**: api_client.py:308-336
**Signature**: `delete_workout_by_id(token, workout_id)`
**Endpoint**: `DELETE /api/v1/workouts/{workout_id}`

**Purpose**: Delete a single workout by ID.

**Returns**: `(success: bool, error_message: str or None)`

**Implementation**:
```python
def delete_workout_by_id(token, workout_id):
    url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True, None
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        if e.response.status_code == 422:
            # Parse specific error (e.g., "Cannot delete a completed workout")
            try:
                error_data = e.response.json()
                if "Cannot delete a completed workout" in str(error_data):
                    error_msg = "Cannot delete completed workout"
            except:
                pass
        return False, error_msg
```

**Error Handling**:
- **422 Unprocessable Entity**: Workout is completed (API restriction)
- **401 Unauthorized**: Not authorized to delete this workout
- **404 Not Found**: Workout doesn't exist

### Function: `delete_workouts_filtered()`
**Location**: api_client.py:339-446
**Signature**: `delete_workouts_filtered(token, client_id, start_date=None, end_date=None, workout_types=None, dry_run=False)`

**Purpose**: Batch delete workouts with date range and type filtering.

**Parameters**:
- `token`: Authentication token
- `client_id`: Client ID to delete workouts for
- `start_date`: Delete workouts on/after this date (YYYY-MM-DD) - None means no start limit
- `end_date`: Delete workouts on/before this date (YYYY-MM-DD) - None means no end limit
- `workout_types`: List of workout types ['default', 'nutrition'] - None means all types
- `dry_run`: If True, only show what would be deleted without actually deleting

**Returns**:
```python
{
    'would_delete' or 'deleted': [list of workout info],
    'skipped': [list of skipped workouts with reasons],
    'errors': [list of error info],
    'total_matched': int
}
```

**Use Cases**:
- Delete all future workouts (after today)
- Delete specific date range
- Delete only nutrition assignments or only strength workouts
- Preview deletions before committing (dry_run=True)

**Example**:
```python
# Preview deletion of all strength workouts after today
result = delete_workouts_filtered(
    token,
    client_id=101,
    start_date="2025-10-17",
    workout_types=['default'],
    dry_run=True
)

print(f"Would delete {len(result['would_delete'])} workouts")

# Actually delete them
result = delete_workouts_filtered(
    token,
    client_id=101,
    start_date="2025-10-17",
    workout_types=['default'],
    dry_run=False
)
```

## Exercise Database Management

### Loading Exercise Map (Enhanced in v1.5)

**Function**: `load_exercise_map()`
**Location**: api_client.py:41-57
**Returns**: `dict[str, dict]` - Mapping of exercise names to ID and type

**Purpose**: Enable exercise name lookup with type information during workout parsing and upload.

**File Location**: `~/Turnkey-{workspace}/shared/exerciselist.json`

**Implementation** (Updated):
```python
def load_exercise_map():
    """Loads exerciselist.json and creates a name-to-ID mapping with exercise types.

    Returns dict with structure: {exercise_name_lower: {'id': id, 'type': exercise_type}}
    """
    try:
        filepath = get_exercise_list_file()
        exercises = safe_json_load(filepath)
        if exercises is None:
            raise FileNotFoundError()
        return {
            ex['name'].lower(): {
                'id': ex['id'],
                'type': ex.get('exercise_type', 'resistance')
            }
            for ex in exercises
        }
    except FileNotFoundError:
        console.print("[bold red]Error: `exerciselist.json` not found.[/bold red]")
        return None
```

**Exercise List Structure** (Updated):
```json
[
  {"id": 1, "name": "Squat", "exercise_type": "resistance"},
  {"id": 2, "name": "Bench Press", "exercise_type": "resistance"},
  {"id": 3, "name": "Running", "exercise_type": "cardio"},
  ...
]
```

**Mapping Result**:
```python
{
  "squat": {'id': 1, 'type': 'resistance'},
  "bench press": {'id': 2, 'type': 'resistance'},
  "running": {'id': 3, 'type': 'cardio'},
  ...
}
```

### Helper Functions

**Function**: `get_exercise_id(exercise_map, exercise_name)`
**Location**: api_client.py:59-68

```python
def get_exercise_id(exercise_map, exercise_name):
    """Safely retrieve an exercise ID from the cached exercise map."""
    if not exercise_map or not exercise_name:
        return None
    entry = exercise_map.get(exercise_name.strip().lower())
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("id")
    return entry  # Legacy format compatibility
```

**Function**: `get_exercise_type(exercise_map, exercise_name, default="resistance")`
**Location**: api_client.py:70-77

```python
def get_exercise_type(exercise_map, exercise_name, default="resistance"):
    """Safely retrieve the exercise_type for an exercise name."""
    if not exercise_map or not exercise_name:
        return default
    entry = exercise_map.get(exercise_name.strip().lower())
    if isinstance(entry, dict):
        return entry.get("type", default)
    return default
```

### Updating Exercise List

**Function**: `update_exercise_list(token)`
**Location**: api_client.py:79-95
**Returns**: `bool` - Success status

**Endpoint**: `GET /api/v1/exercises`

**Purpose**: Download the latest exercise database from the API.

**Implementation**:
```python
def update_exercise_list(token):
    url = f"{API_BASE_URL}/api/v1/exercises"
    headers = {"Authorization": f"Bearer {token}"}
    filepath = get_exercise_list_file()

    with console.status("[bold green]Downloading latest exercise list...[/bold green]"):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            exercises = response.json()
            safe_json_dump(exercises, filepath)
            console.print(f"✅ [green]Successfully saved {len(exercises)} exercises to {filepath}[/green]")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [red]Error fetching exercises: {e}[/red]")
            return False
```

**When to Update**:
- First-time setup (prompted in coach_cli.py:616-624)
- Manual refresh via tools menu (option 'u' in show_tool_menu)
- After API additions/changes to exercise database

## Metric Catalog Access (New in v1.5)

**Function**: `fetch_metric_catalog(token)`
**Location**: api_client.py:98-108
**Endpoint**: `GET /api/v1/metrics`

**Purpose**: Retrieve the global list of available metric definitions from the API.

**Implementation**:
```python
def fetch_metric_catalog(token):
    """Retrieve the global list of available metric definitions."""
    url = f"{API_BASE_URL}/api/v1/metrics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        console.print(f"[bold red]Error fetching metric catalog:[/bold red] {err}")
        return []
```

**Return Structure**:
```json
[
  {
    "id": 1,
    "name": "Body Weight",
    "metric_type": "decimal",
    "unit": "lbs",
    "description": "Client body weight"
  },
  {
    "id": 2,
    "name": "Body Fat %",
    "metric_type": "decimal",
    "unit": "%"
  },
  ...
]
```

**Usage**:
- Used by `upload_tool.py` to resolve metric placeholders (e.g., `@weight 180 lbs`)
- Used by `metrics_tool.py` for metric entry validation
- Cached locally per workspace for performance

## Shared Utility Functions

### Text Cleaning

**Function**: `clean_text(raw_html)`
**Location**: api_client.py:29-37

**Purpose**: Strip HTML tags and normalize whitespace from API responses.

**Implementation**:
```python
def clean_text(raw_html):
    if not raw_html:
        return ""
    # Convert <br> to newlines
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    # Convert closing tags to newlines
    text = re.sub(r'</p>|</div>', '\n', text, flags=re.IGNORECASE)
    # Decode HTML entities
    text = html.unescape(text)
    # Remove all remaining tags
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    # Normalize multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text
```

**Use Cases**:
- Workout comments
- Messages from conversations
- Any user-generated content from API

### Screen Clearing

**Function**: `clear_screen()`
**Location**: api_client.py:26-27

```python
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
```

**Platform Support**:
- Windows: Uses `cls` command
- Unix/Linux/macOS: Uses `clear` command

## Error Handling Patterns

### API Request Error Handling

**Pattern**:
```python
try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx
    data = response.json()
    # Process data...
except requests.exceptions.RequestException as err:
    console.print(f"[bold red]Error message: {err}[/bold red]")
    return default_value
```

**Exception Types**:
- `requests.exceptions.HTTPError`: Bad status code (4xx, 5xx)
- `requests.exceptions.ConnectionError`: Network issue
- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.RequestException`: Base class (catches all)

### File Loading Error Handling

**Pattern**:
```python
try:
    data = safe_json_load(filepath)
    if data is None:
        raise FileNotFoundError()
    # Process data...
except FileNotFoundError:
    console.print("[bold red]File not found[/bold red]")
    return None
except Exception as e:
    console.print(f"[bold red]Error: {e}[/bold red]")
    return None
```

## Best Practices for Developers

### 1. Always Use Token Authentication
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url, headers=headers)
```

### 2. Handle Token Expiry Gracefully
```python
# If API returns 401 Unauthorized
if response.status_code == 401:
    # Invalidate cache and prompt re-login
    token, user_id = get_access_token()
```

### 3. Use Caching for Expensive Operations
- Check cache existence before API call
- Implement incremental updates when possible
- Use `force_refresh` parameter for manual cache invalidation

### 4. Validate API Responses
```python
data = response.json()
if not data or not isinstance(data, list):
    return []  # Return safe default
```

### 5. Use Encoding Utilities for File I/O
```python
# Don't use open() directly
from encoding_utils import safe_json_dump, safe_json_load

# Use these instead
data = safe_json_load(filepath, default=[])
safe_json_dump(data, filepath, indent=4)
```

## Troubleshooting

### Token Cache Issues
**Symptom**: Repeated login prompts

**Solution**:
1. Check cache file exists: `~/Turnkey-{workspace}/shared/.tokencache`
2. Verify workspace is correctly set (check `~/.turnkey_coach_settings.json`)
3. Verify file permissions (readable/writable)
4. Check expiry timestamp is valid ISO format
5. Delete cache file to force fresh login
6. System will scan for tokens in other workspaces as fallback

### API Connection Failures
**Symptom**: RequestException errors

**Solution**:
1. Verify network connectivity
2. Check API base URL is correct
3. Test API endpoint in browser/Postman
4. Review API authentication headers

### Exercise List Not Loading
**Symptom**: `exerciselist.json not found` error

**Solution**:
1. Run update exercise list utility (option 'u' in tools menu)
2. Check file exists: `~/Turnkey-{workspace}/shared/exerciselist.json`
3. Verify file is valid JSON
4. Re-download if corrupted
5. Ensure workspace directories are properly initialized

### Workout Deletion Failures
**Symptom**: Cannot delete workout, 422 error

**Solutions**:
1. Check if workout is completed (API prevents deletion of completed workouts)
2. Verify authentication token is valid
3. Confirm user has permission to delete this client's workouts
4. Use dry_run=True first to preview before actual deletion

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [05-Workout-Management.md](./05-Workout-Management.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
