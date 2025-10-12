# API Client and Authentication

## Purpose
This guide covers the API client layer, authentication mechanisms, token caching, and shared utility functions in `api_client.py`.

## Module Overview

**File**: `api_client.py` (202 lines)

**Core Responsibilities**:
- API authentication and token management
- Client list retrieval
- Workout history management with incremental caching
- Exercise database management
- Shared utility functions

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
**Location**: api_client.py:137-146

```python
def load_auth_data():
    token_cache_file = get_token_cache_file()
    if not os.path.exists(token_cache_file):
        return None, None
    data = safe_json_load(token_cache_file)
    if data:
        try:
            if datetime.fromisoformat(data.get("expires_at")) > datetime.now():
                return data.get("token"), data.get("user_id")
        except (KeyError, TypeError, ValueError):
            pass
    return None, None
```

**Cache Location**: `~/Turnkey/shared/.tokencache`

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

#### 5. Token Caching (`save_auth_data()`)
**Location**: api_client.py:131-135

```python
def save_auth_data(token, user_id):
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat()
    }
    token_cache_file = get_token_cache_file()
    safe_json_dump(auth_data, token_cache_file)
```

### Main Authentication Function

**Function**: `get_access_token()`
**Location**: api_client.py:171-201
**Returns**: `(token: str, user_id: int)` or `(None, None)`

**Complete Flow**:
```
get_access_token()
    ↓
Check token cache
    ↓ [valid]
Return cached token + user_id
    ↓ [invalid/missing]
Check stored credentials (settings.py)
    ↓ [found]
Auto-login with credentials
    ↓ [not found]
Prompt for email/password
    ↓
POST /users/tokens/sign_in
    ↓ [success]
Save token cache
Return token + user_id
    ↓ [failure]
Display error
Return (None, None)
```

## Client Management

### Fetching Client List

**Function**: `get_clients(token, user_id)`
**Location**: api_client.py:149-168
**Endpoint**: `GET /api/v1/users/{user_id}/clients`

**Purpose**: Retrieve all clients associated with the authenticated coach.

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
    "display_coach_type": "Head Coach"
  },
  ...
]
```

**Data Transformation**:
The function aggregates relationships to handle multiple coaches per client:

```python
clients_data = {}
for rel in relationships:
    client_info, coach_info = rel.get('client'), rel.get('coach')
    client_id = client_info.get('id')

    if client_id not in clients_data:
        clients_data[client_id] = {
            'id': client_id,
            'full_name': client_info.get('full_name', 'N/A'),
            'coaches': []
        }

    clients_data[client_id]['coaches'].append(
        f"{coach_info.get('full_name', 'Unknown')} ({rel.get('display_coach_type', 'Coach')})"
    )
```

**Return Format**:
```python
[
  {
    'id': 101,
    'full_name': 'John Doe',
    'coaches': ['Coach Name (Head Coach)', 'Assistant Coach (Assistant)']
  },
  ...
]
```

## Workout History Management

### Overview

The workout history system implements intelligent incremental caching to minimize API calls and provide fast offline access.

### Function: `get_workout_history()`

**Location**: api_client.py:97-128
**Signature**: `get_workout_history(token, client, force_refresh=False)`

**Parameters**:
- `token`: Authentication token
- `client`: Client dictionary with 'id' key
- `force_refresh`: If True, bypass cache and re-download all workouts

**Returns**: List of complete workout dictionaries

### Caching Strategy

#### Cache Files
1. **Workout Data**: `~/Turnkey/clients/{client_id}/workouts_user_{client_id}.json`
   - Complete workout details
   - Includes exercises, sets, comments, etc.

2. **Workout Index**: `~/Turnkey/clients/{client_id}/workouts_index.json`
   - Metadata only (workout IDs and update timestamps)
   - Used by feed_tool.py for incremental updates

#### Cache Logic Flow

```
get_workout_history(token, client, force_refresh=False)
    ↓
[force_refresh=True] → Download all workouts
    ↓
[force_refresh=False] → Check cache exists
    ↓ [no cache]
Download all workouts (full refresh)
    ↓ [cache exists]
Load existing workouts
Validate cache (has workout_date fields)
    ↓ [invalid]
Download all workouts (full refresh)
    ↓ [valid]
Find latest workout date
Calculate next_date = latest_date + 1 day
Fetch new workouts with start_date filter
    ↓ [new workouts found]
Merge: existing + new
Save to cache
    ↓ [no new workouts]
Return existing cache
```

### Implementation Details

#### Incremental Update
**Location**: api_client.py:107-126

```python
if os.path.exists(workout_cache_path):
    existing_workouts = safe_json_load(workout_cache_path, default=[])

    # Validate cache
    valid_workouts = [w for w in existing_workouts if w.get('workout_date')]
    if not valid_workouts:
        return get_workout_history(token, client, force_refresh=True)

    # Find latest date
    latest_date_str = max(w['workout_date'] for w in valid_workouts)
    start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)

    # Fetch new workouts only
    new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())

    if new_workouts:
        all_workouts = existing_workouts + new_workouts
        safe_json_dump(all_workouts, workout_cache_path, indent=4)
        return all_workouts
    else:
        return existing_workouts
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

## Exercise Database Management

### Loading Exercise Map

**Function**: `load_exercise_map()`
**Location**: api_client.py:40-53
**Returns**: `dict[str, int]` - Mapping of exercise names (lowercase) to IDs

**Purpose**: Enable exercise name lookup during workout parsing and upload.

**File Location**: `~/Turnkey/shared/exerciselist.json`

**Implementation**:
```python
def load_exercise_map():
    try:
        filepath = get_exercise_list_file()
        exercises = safe_json_load(filepath)
        if exercises is None:
            raise FileNotFoundError()
        # Create lowercase name → ID mapping
        return {ex['name'].lower(): ex['id'] for ex in exercises}
    except FileNotFoundError:
        console.print("[bold red]Error: `exerciselist.json` not found.[/bold red]")
        return None
```

**Exercise List Structure**:
```json
[
  {"id": 1, "name": "Squat"},
  {"id": 2, "name": "Bench Press"},
  {"id": 3, "name": "Deadlift"},
  ...
]
```

**Mapping Result**:
```python
{
  "squat": 1,
  "bench press": 2,
  "deadlift": 3,
  ...
}
```

### Updating Exercise List

**Function**: `update_exercise_list(token)`
**Location**: api_client.py:55-71
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
- First-time setup (prompted in coach_cli.py:294-303)
- Manual refresh via tools menu (option 'u')
- After API additions/changes to exercise database

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
1. Check cache file exists: `~/Turnkey/shared/.tokencache`
2. Verify file permissions (readable/writable)
3. Check expiry timestamp is valid ISO format
4. Delete cache file to force fresh login

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
2. Check file exists: `~/Turnkey/shared/exerciselist.json`
3. Verify file is valid JSON
4. Re-download if corrupted

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [05-Workout-Management.md](./05-Workout-Management.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
