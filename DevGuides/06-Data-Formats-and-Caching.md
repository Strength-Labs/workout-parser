# Data Formats and Caching

## Purpose
This guide documents all data formats, caching strategies, file structures, and data transformation patterns used throughout the codebase.

## File System Structure

### Directory Layout
```
~/Turnkey/
├── clients/                          # Per-client data
│   └── {client_id}/
│       ├── workouts_user_{id}.json           # Complete workout cache
│       ├── workouts_index.json               # Workout metadata index
│       ├── messages_cache.json               # Conversation cache
│       ├── feed_cache.json                   # Unified feed cache
│       ├── {Client_Name}_history_{ts}.txt    # Exported histories
│       ├── Unified_Feed_{name}_{ts}.txt      # Exported feeds
│       └── note-{date}.txt                   # Coach notes
├── shared/
│   ├── exerciselist.json             # Exercise database
│   ├── .tokencache                   # Auth token
│   └── coaching_context/             # AI context files
│       └── *.md, *.txt               # Custom context documents
└── cache/                            # Reserved for future use

~/.turnkey_coach_settings.json        # User settings and credentials

{app_directory}/
├── coach_cli.py
├── api_client.py
├── ... (application files)
└── DevGuides/                        # These documentation files
```

## Data Formats

### 1. Authentication Token Cache

**File**: `~/Turnkey/shared/.tokencache`

**Format**: JSON

**Structure**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "user_id": 12345,
  "expires_at": "2025-10-11T15:30:00.123456"
}
```

**Fields**:
- `token` (string): JWT bearer token for API authentication
- `user_id` (integer): Authenticated user's ID
- `expires_at` (ISO 8601 string): Token expiration timestamp (1 hour from creation)

**Lifecycle**:
- **Created**: On successful login (api_client.py:131-135)
- **Read**: On every application launch (api_client.py:137-146)
- **Invalidated**: On expiry or logout
- **Deleted**: On logout (coach_cli.py:52-56)

### 2. User Settings

**File**: `~/.turnkey_coach_settings.json`

**Format**: JSON

**Structure**:
```json
{
  "default_editor": ["code", "-w"],
  "email": "coach@example.com",
  "encrypted_password": "gAAAAABh...",
  "encryption_key": "dGVzdGtleQ==...",
  "llm_provider": "openai",
  "llm_encrypted_key": "gAAAAABh..."
}
```

**Fields**:
- `default_editor` (array of strings): Editor command and arguments
- `email` (string): User's email for auto-login
- `encrypted_password` (string): Fernet-encrypted password
- `encryption_key` (string): Base64-encoded Fernet key
- `llm_provider` (string, optional): "openai" or "xai"
- `llm_encrypted_key` (string, optional): Encrypted LLM API key

**Encryption Details**:
- Algorithm: Fernet (symmetric encryption from cryptography library)
- Key storage: Stored in same file (tradeoff for usability vs security)
- Encryption: `Fernet(key).encrypt(password.encode()).decode('utf-8')`
- Decryption: `Fernet(key).decrypt(encrypted.encode()).decode('utf-8')`

**Lifecycle**:
- **Created**: First-time setup (settings.py:15-85)
- **Read**: On every application launch
- **Updated**: Via settings menu (coach_cli.py:243-282)

### 3. Exercise List

**File**: `~/Turnkey/shared/exerciselist.json`

**Format**: JSON array

**Structure**:
```json
[
  {
    "id": 1,
    "name": "Squat",
    "description": "...",
    "muscle_groups": ["Quadriceps", "Glutes"],
    "equipment": ["Barbell"]
  },
  {
    "id": 2,
    "name": "Bench Press",
    "description": "...",
    "muscle_groups": ["Chest", "Triceps"],
    "equipment": ["Barbell"]
  },
  ...
]
```

**Fields**:
- `id` (integer): Unique exercise identifier
- `name` (string): Exercise name
- `description` (string, optional): Exercise description
- `muscle_groups` (array, optional): Target muscle groups
- `equipment` (array, optional): Required equipment

**Usage**:
- Loaded into memory as `{name.lower(): id}` mapping
- Used for exercise name lookup during parsing
- Updated via API: `GET /api/v1/exercises`

**Lifecycle**:
- **Created**: Manual download or first-time setup prompt
- **Read**: When uploader tool or AI chat loads
- **Updated**: Manual refresh via tools menu

### 4. Workout Cache

**File**: `~/Turnkey/clients/{client_id}/workouts_user_{client_id}.json`

**Format**: JSON array

**Structure**:
```json
[
  {
    "id": 5001,
    "user_id": 101,
    "workout_date": "2025-10-01",
    "title": "Intensity Day",
    "completed": true,
    "published": true,
    "weight_type": "lbs",
    "last_activity": "2025-10-01T16:30:00Z",
    "comments": [
      {
        "id": 1001,
        "body": "<p>Great work today!</p>",
        "user": {
          "id": 12345,
          "full_name": "Coach Name",
          "email": "coach@example.com"
        },
        "updated_at": "2025-10-01T14:30:00Z",
        "parent_type": "Workout",
        "parent_id": 5001
      }
    ],
    "assigned_exercises": [
      {
        "id": 10001,
        "exercise_id": 42,
        "exercise": {
          "id": 42,
          "name": "Squat"
        },
        "priority": 0,
        "assigned_sets": [
          {
            "id": 20001,
            "sets": 3,
            "reps": 5,
            "weight": 405,
            "weight_type": "default_weight_type",
            "weight_type_value": null,
            "set_type": "default",
            "rep_type": "default_rep_type",
            "distance": 0.0,
            "distance_unit": null,
            "time": 0,
            "body": null,
            "priority": 0,
            "display_label": "3x5 @ 405",
            "actual_sets": [
              {
                "sets": 1,
                "reps": 5,
                "weight": 405,
                "id": 30001
              },
              {
                "sets": 1,
                "reps": 5,
                "weight": 405,
                "id": 30002
              },
              {
                "sets": 1,
                "reps": 5,
                "weight": 405,
                "id": 30003
              }
            ]
          },
          {
            "set_type": "custom",
            "body": "Focus on hitting depth",
            "priority": 1,
            "rep_type": "default_rep_type",
            "distance": 0.0,
            "distance_unit": null,
            "time": 0,
            "reps": null,
            "sets": null,
            "weight": null
          }
        ],
        "comments": [
          {
            "id": 1002,
            "body": "Hit depth on all reps",
            "user": {
              "id": 101,
              "full_name": "John Doe"
            },
            "updated_at": "2025-10-01T13:45:00Z",
            "parent_type": "AssignedExercise",
            "parent_id": 10001
          }
        ]
      }
    ]
  },
  ...
]
```

**Key Field Descriptions**:

**Workout Level**:
- `id`: Unique workout identifier
- `workout_date`: Date in YYYY-MM-DD format
- `title`: Optional workout title
- `completed`: Whether athlete marked workout complete
- `published`: Whether workout is visible to athlete
- `weight_type`: "lbs" or "kgs" (note: API uses "kgs" not "kg")

**Exercise Level**:
- `exercise_id`: Reference to exercise in exerciselist.json
- `exercise`: Denormalized exercise object
- `priority`: Display order (0-indexed)

**Set Level**:
- `set_type`: "default" (normal set) or "custom" (note)
- `rep_type`: "default_rep_type" or "AMRAP"
- `weight_type`: "default_weight_type", "percent", "RPE", "bodyweight"
- `weight_type_value`: Percentage or RPE value if applicable
- `actual_sets`: Array of performed sets (recorded by athlete)
- `display_label`: Formatted string for display (e.g., "3x5 @ 405")

**Time-Based Sets**:
- `time`: Duration in seconds
- `distance`: Distance value
- `distance_unit`: "m", "km", "miles", "yards", "feet"

**Lifecycle**:
- **Created**: First load or force refresh (api_client.py:97-128)
- **Updated**: Incremental update on subsequent loads
- **Read**: By all tools needing workout history

### 5. Workout Index

**File**: `~/Turnkey/clients/{client_id}/workouts_index.json`

**Format**: JSON

**Structure**:
```json
{
  "client_id": 101,
  "last_summary_sync": "2025-10-11T10:30:00+00:00",
  "workouts": {
    "5001": {
      "updated_at": "2025-10-01T14:00:00Z"
    },
    "5002": {
      "updated_at": "2025-10-02T15:30:00Z"
    },
    "5003": {
      "updated_at": "2025-10-03T12:00:00Z"
    }
  }
}
```

**Fields**:
- `client_id`: Client this index belongs to
- `last_summary_sync`: Last time workout summaries were fetched
- `workouts`: Map of workout_id → metadata

**Purpose**:
- Track `updated_at` timestamps for each workout
- Enable incremental updates (only fetch changed workouts)
- Reduce API calls dramatically

**Update Logic** (feed_tool.py:149-189):
```
Fetch workout summaries (lightweight API call)
For each summary:
    Compare updated_at with index
    If changed or new:
        Add workout_id to changed_ids list
Fetch details only for changed_ids (parallel)
Update index with new timestamps
Save index
```

**Lifecycle**:
- **Created**: First incremental update
- **Updated**: Every feed refresh
- **Read**: On every feed launch

### 6. Messages Cache

**File**: `~/Turnkey/clients/{client_id}/messages_cache.json`

**Format**: JSON

**Structure**:
```json
{
  "conversation_id": 5001,
  "last_seen_id": 99999,
  "messages": {
    "12345": {
      "id": 12345,
      "created_at": "2025-10-01T14:30:00Z",
      "body": "How did yesterday's workout feel?",
      "user": {
        "id": 101,
        "full_name": "Coach Name",
        "email": "coach@example.com"
      }
    },
    "12346": {
      "id": 12346,
      "created_at": "2025-10-01T15:00:00Z",
      "body": "Felt great! Squats were solid.",
      "user": {
        "id": 102,
        "full_name": "John Doe",
        "email": "john@example.com"
      }
    },
    ...
  }
}
```

**Fields**:
- `conversation_id`: 1-on-1 conversation ID with client
- `last_seen_id`: Highest message ID seen (for incremental updates)
- `messages`: Map of message_id → message object (keyed by string for JSON compatibility)

**Incremental Logic**:
```
If last_seen_id exists:
    Fetch only 1 page of messages (100 most recent)
    Stop if no new messages found
Else (first load):
    Fetch 5 pages (500 messages)
    Continue until no more pages
```

**Lifecycle**:
- **Created**: First feed load
- **Updated**: Every feed refresh
- **Read**: On feed launch

### 7. Feed Cache

**File**: `~/Turnkey/clients/{client_id}/feed_cache.json`

**Format**: JSON

**Structure**:
```json
{
  "conversation_id": 5001,
  "alias_map": {
    "1": "Workout-5001-0",
    "2": "AssignedExercise-10001-0",
    "3": "Workout-5002-1"
  },
  "events": [
    {
      "type": "message",
      "content": "How did yesterday's workout feel?",
      "author_id": 101,
      "author": "Coach Name",
      "timestamp": "2025-10-01T14:30:00+00:00"
    },
    {
      "type": "workout_comment",
      "content": "Hit depth on all reps",
      "author_id": 102,
      "author": "John Doe",
      "timestamp": "2025-10-01T15:00:00+00:00",
      "parent_id": 10001,
      "parent_type": "AssignedExercise",
      "comment_id": "AssignedExercise-10001-0",
      "alias_id": "1"
    },
    ...
  ]
}
```

**Event Types**:

**Message Event**:
- `type`: "message"
- `content`: Message body (HTML stripped)
- `author_id`: Sender's user ID
- `author`: Sender's full name
- `timestamp`: ISO 8601 datetime

**Workout Comment Event**:
- `type`: "workout_comment"
- `content`: Comment body (HTML stripped)
- `author_id`: Commenter's user ID
- `author`: Commenter's full name
- `timestamp`: ISO 8601 datetime
- `parent_id`: Workout or AssignedExercise ID
- `parent_type`: "Workout" or "AssignedExercise"
- `comment_id`: Unique identifier for this comment
- `alias_id`: Short numeric alias (for user convenience)

**Alias Map**:
- Maps short IDs (1, 2, 3) to full comment IDs
- Enables easy replying: `c 1 Great job!`
- Generated in reverse order (newest comments get lowest numbers)

**Lifecycle**:
- **Created**: After first aggregation
- **Updated**: After each background refresh
- **Read**: On feed launch (immediate display)

## Caching Strategies

### 1. Token Caching (Time-Based)

**Strategy**: Cache valid token for 1 hour

**Implementation**:
```python
# Save (api_client.py:131-135)
expires_at = datetime.now() + timedelta(hours=1)
auth_data = {"token": token, "user_id": user_id, "expires_at": expires_at.isoformat()}
safe_json_dump(auth_data, token_cache_file)

# Load (api_client.py:137-146)
data = safe_json_load(token_cache_file)
if datetime.fromisoformat(data.get("expires_at")) > datetime.now():
    return data.get("token"), data.get("user_id")
return None, None  # Expired or invalid
```

**Invalidation**:
- Automatic: After 1 hour
- Manual: Logout action

### 2. Workout Caching (Date-Based Incremental)

**Strategy**: Cache all workouts, fetch only new since last date

**Implementation** (api_client.py:107-126):
```python
if os.path.exists(workout_cache_path):
    existing_workouts = safe_json_load(workout_cache_path, default=[])
    valid_workouts = [w for w in existing_workouts if w.get('workout_date')]

    # Find latest date
    latest_date_str = max(w['workout_date'] for w in valid_workouts)
    start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)

    # Fetch only new workouts
    new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())

    if new_workouts:
        all_workouts = existing_workouts + new_workouts
        safe_json_dump(all_workouts, workout_cache_path, indent=4)
        return all_workouts
    else:
        return existing_workouts  # No new data
```

**Invalidation**:
- Manual: Force refresh option

### 3. Workout Index Caching (Timestamp-Based Incremental)

**Strategy**: Track `updated_at` for each workout, fetch only changed

**Implementation** (feed_tool.py:149-189):
```python
# Load existing index
index = _load_workouts_index(client_dir, client_id)
updated_index = index.get('workouts', {})

# Fetch summaries
summaries = _fetch_workouts_summary(token, client_id)

# Identify changed workouts
changed_ids = []
for summary in summaries:
    wid = summary.get('id')
    updated_at = summary.get('updated_at')
    prev = updated_index.get(str(wid), {}).get('updated_at')

    if not prev or (updated_at and updated_at != prev) or (wid not in existing_map):
        changed_ids.append(wid)

    updated_index[str(wid)] = {"updated_at": updated_at}

# Fetch only changed workouts (in parallel)
if changed_ids:
    with ThreadPoolExecutor(max_workers=8) as pool:
        # Fetch details for changed workouts only
        ...
```

**Benefits**:
- Minimal API calls (summaries are lightweight)
- Parallel fetching of changed workouts
- Handles edits, additions, and deletions

### 4. Message Caching (ID-Based Incremental)

**Strategy**: Track highest message ID, fetch only newer messages

**Implementation** (feed_tool.py:69-116):
```python
cache = _load_messages_cache(client_dir)
last_seen_id = cache.get("last_seen_id")

# Determine fetch scope
max_pages = 1 if last_seen_id else initial_max_pages  # 1 or 5

for page in range(1, max_pages + 1):
    resp = requests.get(messages_url, params={"page": page, "per_page": 100})
    items = resp.json()

    new_in_page = 0
    for msg in items:
        mid = msg.get('id')
        if str(mid) not in cache['messages']:
            cache['messages'][str(mid)] = msg
            new_in_page += 1
            if mid > max_id_seen:
                max_id_seen = mid

    # Early exit if no new messages
    if last_seen_id is not None and new_in_page == 0:
        break

cache['last_seen_id'] = max_id_seen
_save_messages_cache(client_dir, cache)
```

**Benefits**:
- Efficient incremental updates
- Early exit when no new data
- Handles pagination gracefully

### 5. Feed Cache (Aggregate Cache)

**Strategy**: Cache entire aggregated feed for instant display

**Implementation** (feed_tool.py:672-689):
```python
# Load cache immediately on startup
if os.path.exists(cache_path):
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            feed_data["events"] = cached_data.get("events", [])
            # Parse timestamp strings back to datetime
            for event in feed_data["events"]:
                event['timestamp'] = datetime.fromisoformat(event['timestamp'])
            feed_data["conversation_id"] = cached_data.get("conversation_id")
            feed_data["alias_map"] = cached_data.get("alias_map", {})
    except Exception:
        pass  # Ignore cache errors, will refresh

# Display immediately
display_feed(feed_data["events"], ...)

# Refresh in background
refresh_thread = threading.Thread(target=fetch_and_aggregate_data, args=(...))
refresh_thread.start()
```

**Benefits**:
- Instant UI response (no loading screen)
- Background refresh doesn't block interaction
- Offline browsing capability

## Data Transformation Patterns

### 1. API → Cache (Workout Download)

```
API Response (JSON)
    ↓
[{id, workout_date, title, assigned_exercises: [...], comments: [...]}]
    ↓
Save to workouts_user_{id}.json
    ↓
Load into memory as-is
```

No transformation needed - API format is cache format.

### 2. Cache → Markup (Workout Export)

```
Workout JSON
    ↓
format_workouts_to_markup()
    ↓
Text Format:
    Workout Date: YYYY-MM-DD
    Title

    Exercise Name
    Set prescription
        (Actual set)

    ---
```

See [05-Workout-Management.md](./05-Workout-Management.md) for details.

### 3. Markup → JSON (Workout Upload)

```
Text File
    ↓
parse_workouts_from_file()
    ↓
[{
    user_id, workout_date, title,
    weight_type, published,
    assigned_exercises: [{
        exercise_id, priority,
        assigned_sets: [{sets, reps, weight, ...}]
    }]
}]
    ↓
upload_workout() for each
```

See [05-Workout-Management.md](./05-Workout-Management.md) for parsing details.

### 4. Messages + Comments → Feed Events

```
Messages Cache + Workouts Cache
    ↓
Extract messages → {type: "message", content, author, timestamp}
Extract comments → {type: "workout_comment", content, author, timestamp, parent_id, parent_type}
    ↓
Merge arrays
    ↓
Sort by timestamp (ascending)
    ↓
Assign alias IDs to comments (reverse order)
    ↓
Save to feed_cache.json
```

See [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md) for details.

## UTF-8 Handling

### Encoding Utilities Module

**File**: `encoding_utils.py` (133 lines)

**Purpose**: Ensure consistent UTF-8 handling across all platforms (especially Windows).

### Key Functions

#### safe_open()
```python
def safe_open(filepath: str, mode: str = 'r', **kwargs):
    if 'b' not in mode and 'encoding' not in kwargs:
        kwargs['encoding'] = 'utf-8'
    return open(filepath, mode, **kwargs)
```

**Usage**: Replace all `open()` calls with `safe_open()`.

#### safe_json_dump()
```python
def safe_json_dump(obj: Any, filepath: str, **kwargs) -> None:
    kwargs.setdefault('ensure_ascii', False)  # Preserve Unicode
    kwargs.setdefault('indent', 2)
    with safe_open(filepath, 'w') as f:
        json.dump(obj, f, **kwargs)
```

**Key Setting**: `ensure_ascii=False` preserves Unicode characters (emojis, accents, etc.).

#### safe_json_load()
```python
def safe_json_load(filepath: str, default: Any = None, **kwargs) -> Any:
    try:
        with safe_open(filepath, 'r') as f:
            return json.load(f, **kwargs)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default
```

**Error Handling**: Returns default value on any error (file not found, invalid JSON, encoding issues).

#### read_text_file() / write_text_file()
```python
def read_text_file(filepath: str) -> str:
    with safe_open(filepath, 'r') as f:
        return f.read()

def write_text_file(filepath: str, content: str) -> None:
    with safe_open(filepath, 'w') as f:
        f.write(content)
```

**Usage**: Simple text file I/O with guaranteed UTF-8 encoding.

### Why UTF-8 Handling Matters

**Problem**: Python's `open()` uses platform default encoding:
- Windows: Often cp1252 or cp1250
- macOS/Linux: Usually UTF-8

**Issues**:
- Athlete names with accents (José, François, etc.)
- Emojis in comments
- International characters

**Solution**: Always specify UTF-8 explicitly via `encoding_utils`.

## Best Practices for Developers

### 1. Always Use Encoding Utilities
```python
# DON'T:
with open(filepath, 'w') as f:
    json.dump(data, f)

# DO:
from encoding_utils import safe_json_dump
safe_json_dump(data, filepath)
```

### 2. Validate Cache Before Use
```python
data = safe_json_load(cache_path, default=[])
if not data or not isinstance(data, list):
    # Refetch from API
    return force_refresh()
```

### 3. Handle Timestamp Formats Consistently
```python
# Parsing (flexible)
def _parse_ts(ts_str):
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        try:
            return datetime.fromisoformat(ts_str)
        except Exception:
            return None

# Saving (consistent)
timestamp = datetime.now(timezone.utc).isoformat()
```

### 4. Use Incremental Caching When Possible
```python
# Fetch summaries (cheap)
summaries = fetch_summaries()

# Identify changes
changed_ids = [s['id'] for s in summaries if is_changed(s)]

# Fetch only changed details (expensive)
for wid in changed_ids:
    detail = fetch_detail(wid)
    cache[wid] = detail
```

### 5. Provide Default Values
```python
# DON'T:
workouts = json.load(f)
for w in workouts:
    date = w['workout_date']  # KeyError if missing

# DO:
workouts = safe_json_load(path, default=[])
valid = [w for w in workouts if w.get('workout_date')]
```

## Troubleshooting

### Cache Corruption
**Symptom**: JSON decode errors, missing fields, invalid data

**Solutions**:
1. Delete corrupted cache file
2. Use force refresh to rebuild
3. Check disk space (corruption can occur when disk full)
4. Verify file permissions (writable?)

### Unicode Errors
**Symptom**: `UnicodeDecodeError` or garbled text

**Solutions**:
1. Verify using `encoding_utils` functions
2. Check file was created with UTF-8 encoding
3. On Windows, ensure console encoding supports UTF-8
4. Re-download data using UTF-8 utilities

### Missing Incremental Updates
**Symptom**: New workouts/messages not appearing

**Solutions**:
1. Check timestamp comparison logic
2. Verify API returned correct `updated_at` fields
3. Try force refresh to resync
4. Check index file has correct structure

### Large Cache Files
**Symptom**: Slow load times, large file sizes

**Solutions**:
1. Implement cache trimming (e.g., keep last N months)
2. Compress old data (gzip)
3. Move to database (SQLite) for large datasets
4. Archive old client directories

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md)
- [05-Workout-Management.md](./05-Workout-Management.md)
