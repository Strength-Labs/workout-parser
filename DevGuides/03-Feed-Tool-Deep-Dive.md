# Feed Tool Deep Dive

## Purpose
This guide provides comprehensive documentation for the unified feed tool, the most complex module in the codebase. It covers data aggregation, caching strategies, navigation modes, and interaction patterns.

## Module Overview

**File**: `feed_tool.py` (824 lines)

**Purpose**: Unified timeline of messages and workout comments with advanced features:
- Real-time data aggregation from multiple sources
- Incremental caching for performance
- Vim-like navigation modes
- Message/comment posting
- Search functionality
- Export to text files

## Architecture

### Component Overview

```
run_feed() - Main orchestrator
    │
    ├── Cache Management
    │   ├── _load_messages_cache()
    │   ├── _refresh_messages_cache()
    │   ├── _load_workouts_index()
    │   └── _save_workouts_index()
    │
    ├── Data Aggregation
    │   ├── fetch_and_aggregate_data() [background thread]
    │   ├── _extract_comments_from_workouts()
    │   └── _update_workouts_cache_incremental()
    │
    ├── Display Layer
    │   ├── display_feed()
    │   └── nav_mode() [keyboard navigation]
    │
    ├── User Actions
    │   ├── post_message()
    │   ├── post_workout_comment()
    │   └── _export_unified_feed_text()
    │
    └── Search & Navigation
        ├── rebuild_matches()
        └── Navigation commands (j/k/space/etc.)
```

## Data Flow

### Feed Initialization Flow

```
run_feed(token, coach_user_id, client)
    ↓
Load feed cache (feed_cache.json) if exists
    ↓
Display cached data immediately (responsive UX)
    ↓
Start background thread: fetch_and_aggregate_data()
    ├── Refresh messages cache
    ├── Update workouts cache (incremental)
    ├── Extract comments from workouts
    ├── Merge messages + comments
    ├── Sort by timestamp
    ├── Assign alias IDs for comments
    └── Save to feed_cache.json
    ↓
Update display with fresh data
    ↓
Main command loop (user interaction)
```

## Caching System

### Cache Files

#### 1. Messages Cache
**File**: `~/Turnkey/clients/{client_id}/messages_cache.json`

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
        "full_name": "Coach Name"
      }
    },
    ...
  }
}
```

**Purpose**: Store conversation messages with incremental update tracking.

#### 2. Workouts Index
**File**: `~/Turnkey/clients/{client_id}/workouts_index.json`

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
    ...
  }
}
```

**Purpose**: Track workout update timestamps to enable incremental fetching.

#### 3. Feed Cache
**File**: `~/Turnkey/clients/{client_id}/feed_cache.json`

**Structure**:
```json
{
  "conversation_id": 5001,
  "alias_map": {
    "1": "Workout-5001-0",
    "2": "AssignedExercise-10001-0",
    ...
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
      "content": "Felt strong on squats today!",
      "author_id": 102,
      "author": "John Doe",
      "timestamp": "2025-10-01T15:00:00+00:00",
      "parent_id": 5001,
      "parent_type": "Workout",
      "comment_id": "Workout-5001-0",
      "alias_id": "1"
    },
    ...
  ]
}
```

**Purpose**: Aggregated feed for instant display on launch.

### Incremental Update Strategy

#### Messages Incremental Update

**Function**: `_refresh_messages_cache()`
**Location**: feed_tool.py:69-116

**Logic**:
```python
def _refresh_messages_cache(token, client_full_name, client_dir, initial_max_pages=5, per_page=100):
    cache = _load_messages_cache(client_dir)

    # Get or create conversation ID
    if not cache.get("conversation_id"):
        convo_id = _get_or_create_conversation_id(token, client_full_name)
        cache["conversation_id"] = convo_id

    last_seen_id = cache.get("last_seen_id")

    # If we have a last_seen_id, only fetch 1 page (new messages)
    # Otherwise, fetch initial_max_pages (full history)
    max_pages = 1 if last_seen_id else initial_max_pages

    for page in range(1, max_pages + 1):
        params = {"conversation_id": convo_id, "per_page": per_page, "page": page}
        resp = requests.get(f"{API_BASE_URL}/api/v1/messages", headers=headers, params=params)
        items = resp.json() or []

        new_in_page = 0
        for msg in items:
            mid = msg.get('id')
            if str(mid) not in cache['messages']:
                cache['messages'][str(mid)] = {
                    'id': mid,
                    'created_at': msg.get('created_at'),
                    'body': msg.get('body'),
                    'user': msg.get('user') or {},
                }
                new_in_page += 1

        # If we're doing incremental and found no new messages, stop
        if last_seen_id is not None and new_in_page == 0:
            break

    _save_messages_cache(client_dir, cache)
    return cache
```

**API Endpoint**: `GET /api/v1/messages?conversation_id={id}&per_page=100&page=1`

**Optimization**:
- First load: Fetch 5 pages (500 messages max)
- Subsequent loads: Fetch 1 page only (100 most recent)
- Stop early if no new messages found

#### Workouts Incremental Update

**Function**: `_update_workouts_cache_incremental()`
**Location**: feed_tool.py:149-189

**Logic**:
```python
def _update_workouts_cache_incremental(token, client, client_dir):
    client_id = client['id']
    index = _load_workouts_index(client_dir, client_id)
    workouts_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    existing_workouts = _load_json(workouts_path, [])
    existing_map = {w.get('id'): w for w in existing_workouts}

    # Fetch summaries (lightweight API call)
    summaries = _fetch_workouts_summary(token, client_id)

    # Identify changed workouts
    changed_ids = []
    updated_index = index.get('workouts', {})
    for summary in summaries:
        wid = summary.get('id')
        updated_at = summary.get('updated_at') or summary.get('last_activity')
        prev = updated_index.get(str(wid), {}).get('updated_at')

        # Fetch if: timestamp changed OR not in cache
        if not prev or (updated_at and updated_at != prev) or (wid not in existing_map):
            changed_ids.append(wid)

        updated_index[str(wid)] = {"updated_at": updated_at}

    # Fetch changed workout details in parallel
    if changed_ids:
        with ThreadPoolExecutor(max_workers=8) as pool:
            future_map = {pool.submit(_fetch_workout_detail, token, wid): wid for wid in changed_ids}
            for fut in as_completed(future_map):
                wid = future_map[fut]
                detail = fut.result()
                if detail:
                    existing_map[wid] = detail

        # Merge and save
        merged = list(existing_map.values())
        merged.sort(key=lambda w: w.get('workout_date') or '')
        safe_json_dump(merged, workouts_path, indent=4)

    # Update index
    index['workouts'] = updated_index
    index['last_summary_sync'] = datetime.now(timezone.utc).isoformat()
    _save_workouts_index(client_dir, index)

    return list(existing_map.values()), set(changed_ids)
```

**API Endpoints**:
1. `GET /api/v1/workouts?user_id={id}&sort=ascending&published=true` (summaries)
2. `GET /api/v1/workouts/{workout_id}` (details, only for changed workouts)

**Optimization**:
- Summaries API call is cheap (no exercise/set data)
- Parallel fetching with ThreadPoolExecutor (8 workers)
- Only fetch details for changed workouts (timestamp comparison)

### Comment Extraction

**Function**: `_extract_comments_from_workouts()`
**Location**: feed_tool.py:191-231

**Purpose**: Extract all comments from workout data structure and format for feed display.

**Implementation**:
```python
def _extract_comments_from_workouts(workouts):
    comments = []
    for workout in workouts:
        workout_id = workout.get('id')

        # Workout-level comments
        for comment in workout.get('comments', []):
            cid = comment.get('id')
            ts = _parse_ts(comment.get('updated_at'))
            user = comment.get('user') or {}
            comments.append({
                "type": "workout_comment",
                "content": comment.get('body'),
                "author_id": user.get('id'),
                "author": user.get('full_name'),
                "timestamp": ts,
                "parent_id": workout_id,
                "parent_type": "Workout",
                "comment_id": str(cid) if cid else f"Workout-{workout_id}"
            })

        # Exercise-level comments
        for exercise in workout.get('assigned_exercises', []):
            ex_id = exercise.get('id')
            for comment in exercise.get('comments', []):
                cid = comment.get('id')
                ts = _parse_ts(comment.get('updated_at'))
                user = comment.get('user') or {}
                comments.append({
                    "type": "workout_comment",
                    "content": comment.get('body'),
                    "author_id": user.get('id'),
                    "author": user.get('full_name'),
                    "timestamp": ts,
                    "parent_id": ex_id,
                    "parent_type": "AssignedExercise",
                    "comment_id": str(cid) if cid else f"AssignedExercise-{ex_id}"
                })
    return comments
```

**Comment Types**:
1. **Workout-level**: `parent_type="Workout"`, `parent_id=workout_id`
2. **Exercise-level**: `parent_type="AssignedExercise"`, `parent_id=exercise_id`

### Alias ID System

**Purpose**: Provide short, memorable IDs for replying to comments.

**Implementation** (feed_tool.py:327-333):
```python
comment_alias_map = {}
alias_counter = 1
for item in reversed(all_events):
    if item['type'] == 'workout_comment':
        item['alias_id'] = str(alias_counter)
        comment_alias_map[str(alias_counter)] = item.get('comment_id')
        alias_counter += 1
```

**Why Reversed?**:
Most recent comments get lowest alias IDs (easier to type `c 1` vs `c 9999`).

**Usage**:
```bash
# User sees in feed display:
[workout_comment] 2025-10-01 14:30 by John Doe
Reply with: c 1

# User types:
> c 1 Great job on those squats!

# System looks up:
alias_map["1"] = "Workout-5001-0"
# Finds corresponding event, posts comment to parent
```

## Background Data Refresh

### Threading Model

**Function**: `fetch_and_aggregate_data()`
**Location**: feed_tool.py:305-351

**Purpose**: Refresh all data without blocking UI.

**Thread Launch** (feed_tool.py:819-823):
```python
refresh_thread = threading.Thread(
    target=fetch_and_aggregate_data,
    args=(token, client, feed_data_lock, feed_data)
)
refresh_thread.start()
```

**Thread-Safe Data Access**:
```python
feed_data_lock = threading.Lock()

# Writer (background thread):
with feed_data_lock:
    feed_data["events"] = all_events
    feed_data["conversation_id"] = conversation_id
    feed_data["is_refreshing"] = False

# Reader (main thread):
with feed_data_lock:
    display_data = copy.deepcopy(feed_data)
```

**Benefits**:
- UI remains responsive during network operations
- Cached data displayed immediately
- Users can issue commands while refreshing
- Race conditions prevented by lock

## Display System

### Display Function

**Function**: `display_feed()`
**Location**: feed_tool.py:478-516

**Signature**:
```python
def display_feed(
    feed,                    # List of events
    coach_user_id,           # For highlighting coach messages
    search_term=None,        # For search highlighting
    is_refreshing=False,     # Show refresh indicator
    offset=0,                # Pagination offset
    page_size=20,            # Events per page
    selected_event_index=None  # Highlight selected event (search)
)
```

**Layout**:
```
┌─ Unified Feed (Refreshing...) ─────────────────────┐
│                                                     │
│  ┌─ [message] 2025-10-01 14:30 by Coach Name ────┐│
│  │ >>> How did yesterday's workout feel?          ││
│  └────────────────────────────────────────────────┘│
│                                                     │
│  ┌─ [workout_comment] 2025-10-01 15:00 by John ──┐│
│  │ Felt strong on squats today!                   ││
│  │ Reply with: c 1                                ││
│  └────────────────────────────────────────────────┘│
│                                                     │
│  Showing 1-20 of 150. Offset 0. Page size 20       │
└─────────────────────────────────────────────────────┘
```

**Styling Rules**:
1. **Coach Messages**: Blue border + ">>>" prefix
2. **Client Messages**: Default border
3. **Workout Comments**: Yellow type label + reply hint
4. **Selected Event**: Magenta border (search results)
5. **Search Highlight**: Yellow background on matched text

### Search Highlighting

**Implementation** (feed_tool.py:494-495):
```python
if search_term and search_term.lower() in cleaned_content.lower():
    display_text = re.sub(
        f'({re.escape(search_term)})',
        r'[bold yellow]\1[/bold yellow]',
        display_text,
        flags=re.IGNORECASE
    )
```

## Navigation System

### Command-Based Navigation

**Main Loop** (feed_tool.py:692-823)

**Available Commands**:

| Command | Action |
|---------|--------|
| `j` | Move down 1 event |
| `k` | Move up 1 event |
| `pgdn` | Next page |
| `pgup` | Previous page |
| `gg` | Jump to top |
| `end` | Jump to bottom |
| `v` | Enter vim-like navigation mode |
| `/query` | Search for text |
| `n` | Next search result |
| `N` | Previous search result |
| `s` | Clear search |
| `m <text>` | Send message |
| `c <id> <text>` | Reply to comment |
| `x [filename]` | Export feed to text file |
| `o [filename]` | Open exported file in editor |
| `u` | Force refresh |
| `q` | Quit |

### Vim-like Navigation Mode

**Function**: `nav_mode(events)`
**Location**: feed_tool.py:530-652

**Purpose**: Single-keystroke navigation without Enter key.

**Platform Detection**:
- **Windows**: Uses `msvcrt.getwch()`
- **Unix/Linux/macOS**: Uses `termios` and `tty` for raw mode

**Available Keys**:

| Key | Action |
|-----|--------|
| `j` | Down 1 event |
| `k` | Up 1 event |
| `Space` | Next page |
| `b` | Previous page |
| `g` | Jump to top |
| `G` | Jump to bottom |
| `n` | Next search match |
| `N` | Previous search match |
| `q`, `Enter` | Exit navigation mode |
| Arrow keys | Alternative navigation |

**Implementation (Unix)**:
```python
import termios, tty

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
try:
    tty.setcbreak(fd)  # Raw mode, no echo
    while True:
        display_feed(...)
        console.print("[dim]Nav: j/k or arrows move • space/b page • g/G start/end • n/N next/prev match • q or Enter: exit[/dim]")
        ch = sys.stdin.read(1)

        if ch in ('q', '\r', '\n'):
            break
        elif ch == 'j':
            offset += 1
        # ... handle other keys
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
```

### Search System

**Function**: `rebuild_matches(events, term)`
**Location**: feed_tool.py:655-670

**Purpose**: Find all events matching search term and enable navigation between matches.

**Implementation**:
```python
def rebuild_matches(events, term):
    nonlocal search_matches, selected_match_idx, offset

    search_matches = []
    selected_match_idx = None

    if not term:
        return

    term_lower = term.lower()
    for i, ev in enumerate(events):
        content = clean_text(ev.get('content') or "").lower()
        if term_lower in content:
            search_matches.append(i)

    # Auto-select first match and scroll to it
    if search_matches:
        selected_match_idx = 0
        sel = search_matches[selected_match_idx]
        # Center selected event on screen
        offset = max(0, min(sel - page_size // 2, max(0, len(events) - page_size)))
```

**Search Flow**:
```
User: /shoulder pain
    ↓
rebuild_matches() finds 3 events: [12, 45, 98]
    ↓
selected_match_idx = 0 (event 12)
    ↓
Center event 12 on screen
    ↓
Display with event 12 highlighted (magenta border)
    ↓
User presses 'n'
    ↓
selected_match_idx = 1 (event 45)
    ↓
Re-center on event 45
```

## User Interaction

### Sending Messages

**Function**: `post_message(token, conversation_id, message_body)`
**Location**: feed_tool.py:355-368

**API Endpoint**: `POST /api/v1/messages`

**Implementation**:
```python
def post_message(token, conversation_id, message_body):
    if not conversation_id:
        console.print("\n[bold red]Cannot send message: Conversation ID is missing.[/bold red]")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}/api/v1/messages"
    payload = {
        "conversation_id": conversation_id,
        "body": message_body
    }

    try:
        requests.post(url, headers=headers, json=payload).raise_for_status()
        console.print("\n[bold green]Message sent successfully![/bold green]")
        return True
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to send message:[/bold red] {err}")
        return False
```

**Usage**:
```bash
> m Hey John, great work on yesterday's session!
```

### Posting Workout Comments

**Function**: `post_workout_comment(token, parent_id, parent_type, comment_body)`
**Location**: feed_tool.py:370-381

**API Endpoint**: `POST /api/v1/comments?parent_type={type}&parent_id={id}`

**Implementation**:
```python
def post_workout_comment(token, parent_id, parent_type, comment_body):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}/api/v1/comments"
    params = {
        "parent_type": parent_type,  # "Workout" or "AssignedExercise"
        "parent_id": parent_id
    }
    payload = {"body": comment_body}

    try:
        requests.post(url, headers=headers, params=params, json=payload).raise_for_status()
        console.print("\n[bold green]Comment posted successfully![/bold green]")
        return True
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to post comment:[/bold red] {err}")
        return False
```

**Usage**:
```bash
# User sees:
[workout_comment] 2025-10-01 15:00 by John Doe
Reply with: c 1

# User types:
> c 1 Excellent depth on those squats!

# System:
alias_map["1"] → "Workout-5001-0"
Find event with comment_id="Workout-5001-0"
Extract parent_id=5001, parent_type="Workout"
POST /api/v1/comments?parent_type=Workout&parent_id=5001
```

### Exporting Feed

**Function**: `_export_unified_feed_text()`
**Location**: feed_tool.py:385-446

**Purpose**: Generate human-readable text file of entire feed.

**Output Format**:
```
Unified Feed Export
Client: John Doe (ID 101)
Generated: 2025-10-11 10:30:00 UTC

[message] 2025-10-01 14:30 by Coach Name
 How did yesterday's workout feel?

[workout_comment] 2025-10-01 15:00 by John Doe on Workout 2025-10-01 - Intensity Day
 Felt strong on squats today!

[workout_comment] 2025-10-01 15:15 by Coach Name on Squat (Workout 2025-10-01)
 Excellent depth on all reps!

...
```

**Context Enrichment**:
- Workout comments include workout date + title
- Exercise comments include exercise name + workout date
- Empty content marked as "(no text)"

**File Naming**:
```python
timestamp = datetime.now(timezone.utc).astimezone().strftime('%Y%m%d_%H%M%S')
safe_client = client_name.replace(' ', '_')
filename = f"Unified_Feed_{safe_client}_{timestamp}.txt"
```

**Example**: `Unified_Feed_John_Doe_20251011_103000.txt`

### Opening in Editor

**Function**: `_open_in_editor(path)`
**Location**: feed_tool.py:458-474

**Purpose**: Open exported file in user's configured editor.

**Implementation**:
```python
def _open_in_editor(path):
    editor_cmd = get_default_editor()
    editor_name = ' '.join(editor_cmd)

    console.print(f"\nOpening [cyan]{os.path.basename(path)}[/cyan] in [bold green]{editor_name}[/bold green]...")
    console.print("[dim]Close the editor to continue...[/dim]")

    original_dir = os.getcwd()
    try:
        file_dir = os.path.dirname(os.path.abspath(path))
        os.chdir(file_dir)  # Change to file's directory
        filename = os.path.basename(path)
        subprocess.run(editor_cmd + [filename], shell=False, check=False)
    finally:
        os.chdir(original_dir)  # Always restore original directory
```

**Why Change Directory?**:
- Relative path references in editor work correctly
- Editor may create temp files in same directory

**Usage**:
```bash
> x                  # Export to auto-named file
> o                  # Open most recent export
> x custom_name.txt  # Export to specific filename
> o custom_name.txt  # Open specific file
```

## Performance Optimizations

### 1. Instant Display
Load and display cached feed immediately, refresh in background.

### 2. Parallel Workout Fetching
ThreadPoolExecutor with 8 workers for concurrent API calls.

### 3. Incremental Everything
- Messages: Fetch only new since `last_seen_id`
- Workouts: Fetch only changed since last `updated_at`
- Comments: Extract from cached workouts, no separate API calls

### 4. Smart Pagination
- Initial messages fetch: 5 pages (500 messages)
- Subsequent fetches: 1 page (100 most recent)
- Stop early if no new messages found

### 5. Efficient Search
- Build search index only when needed
- Cache match indices
- Re-center viewport on selected match

## Troubleshooting

### Feed Not Refreshing
**Symptom**: Stale data displayed

**Solutions**:
1. Press `u` to force refresh
2. Delete cache files:
   - `feed_cache.json`
   - `messages_cache.json`
   - `workouts_index.json`
3. Check network connectivity
4. Verify token hasn't expired

### Comments Not Posting
**Symptom**: "Failed to post comment" error

**Solutions**:
1. Verify workout/exercise still exists (may have been deleted)
2. Check token is valid (re-login if needed)
3. Ensure API endpoint is reachable
4. Review error message for specific HTTP status

### Navigation Mode Not Working
**Symptom**: Keys don't respond in vim mode

**Solutions**:
1. Terminal may not support raw mode
2. Use command-based navigation instead (j/k with Enter)
3. On Windows, ensure console encoding is set correctly
4. Try a different terminal emulator

### Search Not Finding Text
**Symptom**: No matches for known content

**Solutions**:
1. Search is case-insensitive but requires exact substring
2. Check for extra whitespace in search query
3. HTML entities in content may differ from display (use simple terms)
4. Try rebuilding search after refresh (`u` then `/query` again)

## Best Practices for Developers

### 1. Always Use Background Refresh
Don't block UI thread for network operations:
```python
refresh_thread = threading.Thread(target=long_operation, args=(...))
refresh_thread.start()
# Continue with UI
```

### 2. Protect Shared Data with Locks
```python
with feed_data_lock:
    # Read or modify feed_data safely
    data_copy = copy.deepcopy(feed_data)
```

### 3. Graceful Degradation
Display cached data even if refresh fails:
```python
# Always load cache first
if os.path.exists(cache_path):
    feed_data["events"] = load_cache()

# Display immediately
display_feed(feed_data["events"])

# Then refresh in background
```

### 4. Validate Event Structure
Ensure all events have required fields:
```python
all_events = [e for e in all_events if e.get('timestamp') is not None]
```

### 5. Handle Platform Differences
```python
if os.name == 'nt':
    import msvcrt
    # Windows-specific code
else:
    import termios, tty
    # Unix-specific code
```

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
