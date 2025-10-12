# Architecture Overview

## Purpose
This guide provides a high-level overview of the Turnkey Coach Tools codebase architecture, including module organization, data flow, and design patterns.

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      coach_cli.py                           │
│                   (Main Entry Point)                        │
│  - Client selection                                         │
│  - Tool menu navigation                                     │
│  - Settings management                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├──────────────────────────────┐
                              ↓                              ↓
┌──────────────────────────────────────┐    ┌────────────────────────────┐
│         api_client.py                │    │    Tool Modules            │
│  - Authentication & token caching    │    │  - feed_tool.py            │
│  - Client list retrieval             │    │  - pr_tool.py              │
│  - Workout history management        │    │  - actual_prs_tool.py      │
│  - Exercise list management          │    │  - upload_tool.py          │
│  - Shared utilities                  │    │  - ai_chat_tool.py         │
└──────────────────────────────────────┘    └────────────────────────────┘
                              │                              │
                              ├──────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Supporting Modules                             │
│  - format_tool.py (data formatting)                         │
│  - encoding_utils.py (UTF-8 handling)                       │
│  - directory_migration.py (file system management)          │
│  - settings.py (configuration)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services                              │
│  - Turnkey Coach API (app.turnkey.coach)                    │
│  - OpenAI/xAI APIs (for AI chat)                            │
└─────────────────────────────────────────────────────────────┘
```

## Module Organization

### Core Modules

#### 1. **coach_cli.py** (314 lines)
- **Purpose**: Main application entry point and UI orchestration
- **Key Functions**:
  - `main()`: Application lifecycle management
  - `select_client()`: Client selection interface
  - `show_tool_menu()`: Tool navigation
  - `adjust_settings()`: Settings configuration
- **Dependencies**: All tool modules, api_client, settings

#### 2. **api_client.py** (202 lines)
- **Purpose**: API communication layer and shared utilities
- **Key Functions**:
  - `get_access_token()`: Authentication with caching
  - `get_clients()`: Fetch coach's client list
  - `get_workout_history()`: Workout data retrieval with incremental updates
  - `load_exercise_map()`: Exercise database management
- **Dependencies**: requests, settings, directory_migration, encoding_utils

### Tool Modules

#### 3. **feed_tool.py** (824 lines)
- **Purpose**: Unified feed for messages and workout comments
- **Key Features**:
  - Incremental caching of messages and workouts
  - Real-time data aggregation
  - Navigation mode with vim-like keybindings
  - Export to text files
- **Dependencies**: api_client, directory_migration, encoding_utils

#### 4. **pr_tool.py** (238 lines)
- **Purpose**: Estimated 1RM calculator from workout history
- **Key Features**:
  - Wendler formula for e1RM calculation
  - Wilks score computation
  - Date range filtering
- **Dependencies**: api_client

#### 5. **actual_prs_tool.py** (145 lines)
- **Purpose**: Official PR viewer from API
- **Key Features**:
  - Direct PR data from platform
  - Date filtering
  - Exercise-specific records
- **Dependencies**: api_client

#### 6. **upload_tool.py** (188 lines)
- **Purpose**: Workout file parser and uploader
- **Key Features**:
  - Custom markup parsing
  - Fuzzy exercise matching (rapidfuzz)
  - Interactive exercise selection
  - Unit detection (lbs/kg)
- **Dependencies**: api_client, encoding_utils, rapidfuzz

#### 7. **ai_chat_tool.py** (302 lines)
- **Purpose**: AI-powered workout planning assistant
- **Key Features**:
  - OpenAI/xAI integration
  - Context loading from files
  - In-editor response editing
  - Direct workout upload from AI responses
- **Dependencies**: api_client, format_tool, upload_tool, settings, openai

### Supporting Modules

#### 8. **format_tool.py** (87 lines)
- **Purpose**: Workout data formatting to custom markup
- **Key Functions**:
  - `format_workouts_to_markup()`: JSON to text conversion
  - `format_time()`: Time formatting for sets
- **Dependencies**: api_client

#### 9. **encoding_utils.py** (133 lines)
- **Purpose**: Cross-platform UTF-8 file handling
- **Key Functions**:
  - `safe_open()`: UTF-8 file operations
  - `safe_json_dump()`/`safe_json_load()`: JSON with proper encoding
  - `read_text_file()`/`write_text_file()`: Text file utilities
- **Dependencies**: None (stdlib only)

#### 10. **directory_migration.py** (189 lines)
- **Purpose**: File system structure management
- **Key Functions**:
  - `get_client_dir()`: Client-specific directories
  - `get_shared_dir()`: Shared data location
  - `perform_migration()`: Legacy structure migration
- **Dependencies**: rich

#### 11. **settings.py** (142 lines)
- **Purpose**: Configuration and credentials management
- **Key Functions**:
  - `load_or_init_settings()`: First-time setup
  - `get_default_editor()`: Editor configuration
  - `get_stored_credentials()`: Encrypted credential retrieval
  - `get_llm_credentials()`: AI API key management
- **Dependencies**: cryptography, encoding_utils

## Data Flow Patterns

### Authentication Flow
```
User Launch → coach_cli.main()
    ↓
Check Token Cache (~/.turnkey/shared/.tokencache)
    ↓
[Cache Valid] → Use Cached Token
[Cache Invalid/Missing] → Get Stored Credentials from settings.py
    ↓
[Credentials Found] → Auto-login
[No Credentials] → Prompt for email/password
    ↓
API POST /users/tokens/sign_in
    ↓
Save token + expiry + user_id to cache
```

### Workout History Flow
```
Tool requests workout data
    ↓
Check cache: ~/Turnkey/clients/{client_id}/workouts_user_{client_id}.json
    ↓
[Cache exists] → Load existing + check latest date
    ↓
Fetch new workouts since latest_date (incremental)
    ↓
Merge new + existing → Save to cache
    ↓
Return complete workout list
```

### Feed Aggregation Flow
```
feed_tool.run_feed()
    ↓
Load cached feed (feed_cache.json)
    ↓
Display cached data immediately (responsive UX)
    ↓
Background thread: fetch_and_aggregate_data()
    ├── Refresh messages cache (messages_cache.json)
    ├── Update workouts cache (workouts_user_{id}.json)
    ├── Extract comments from workouts
    └── Merge + sort by timestamp
    ↓
Update display with new data
```

## Design Patterns

### 1. Incremental Caching
**Purpose**: Minimize API calls and improve performance

**Implementation**:
- Workouts: Track `updated_at` timestamps, only fetch changed workouts
- Messages: Track `last_seen_id`, fetch only new messages
- Index files: Store metadata separately from full data

**Files**:
- `workouts_index.json`: Tracks workout update timestamps
- `messages_cache.json`: Stores conversation ID and last seen message
- `feed_cache.json`: Combined feed for instant load

### 2. Thread-based Background Refresh
**Purpose**: Keep UI responsive during network operations

**Implementation** (feed_tool.py:690-823):
```python
refresh_thread = threading.Thread(
    target=fetch_and_aggregate_data,
    args=(token, client, feed_data_lock, feed_data)
)
refresh_thread.start()
# Continue displaying cached data while refreshing
```

### 3. Shared Utility Functions
**Purpose**: Code reuse and consistency

**Examples**:
- `clean_text()`: HTML/markdown stripping (api_client.py:29-37)
- `safe_json_dump()`/`safe_json_load()`: UTF-8 JSON handling
- `get_client_dir()`: Centralized path management

### 4. Settings-based Configuration
**Purpose**: Persistent user preferences

**Stored Data**:
- Default text editor (platform-aware defaults)
- Encrypted credentials (email/password for auto-login)
- LLM provider and API key (encrypted)

**Location**: `~/.turnkey_coach_settings.json`

## Directory Structure

### Runtime Directories
```
~/Turnkey/
├── clients/                     # Per-client data
│   └── {client_id}/
│       ├── workouts_user_{id}.json         # Cached workouts
│       ├── workouts_index.json             # Workout metadata index
│       ├── messages_cache.json             # Conversation cache
│       ├── feed_cache.json                 # Unified feed cache
│       ├── {client}_history_{timestamp}.txt # Exported histories
│       └── note-{date}.txt                 # Coach notes
├── shared/
│   ├── exerciselist.json        # Exercise database
│   ├── .tokencache              # Auth token
│   └── coaching_context/        # AI chat context files
│       └── *.md, *.txt          # Custom context documents
└── cache/                       # Reserved for future use
```

### Application Directory
```
workout-parser/
├── coach_cli.py                 # Main entry point
├── api_client.py                # API layer
├── feed_tool.py                 # Feed viewer
├── pr_tool.py                   # Estimated PRs
├── actual_prs_tool.py           # API PRs
├── upload_tool.py               # Workout uploader
├── ai_chat_tool.py              # AI assistant
├── format_tool.py               # Data formatting
├── encoding_utils.py            # UTF-8 utilities
├── directory_migration.py       # File system management
├── settings.py                  # Configuration
├── requirements.txt             # Dependencies
├── README.md                    # User documentation
├── markup.md                    # Markup language spec
└── DevGuides/                   # Developer documentation
```

## Error Handling Strategy

### Graceful Degradation
- **API Failures**: Display cached data, allow offline browsing
- **Missing Files**: Prompt for creation/download
- **Authentication**: Clear instructions for re-login

### User Feedback
- Rich console status messages during operations
- Error messages with actionable next steps
- Warnings for non-critical issues (yellow text)

## Performance Considerations

### Optimizations
1. **Parallel Workout Details Fetching** (feed_tool.py:169-175)
   - ThreadPoolExecutor with 8 workers
   - Reduces API round-trips for large workout sets

2. **Lazy Loading**
   - Exercise list only loaded when needed
   - Workout history cached per client

3. **Minimal Re-renders**
   - Feed navigation updates offset without full reload
   - Background refresh doesn't block UI

## Security Considerations

### Credential Storage
- Passwords encrypted with Fernet (symmetric encryption)
- Encryption key stored in settings (tradeoff for usability)
- Token cache has 1-hour expiry

### API Communication
- HTTPS only (https://app.turnkey.coach)
- Bearer token authentication
- No credentials in logs or error messages

## Extension Points

### Adding New Tools
1. Create tool module (e.g., `new_tool.py`)
2. Implement `run_new_tool(token, client, ...)` function
3. Import in `coach_cli.py`
4. Add menu option in `show_tool_menu()` (coach_cli.py:191-240)

### Custom Markup Extensions
1. Add new set type parsing in `upload_tool.py:parse_line_as_set()`
2. Add formatting in `format_tool.py:format_workouts_to_markup()`
3. Update `markup.md` specification

### New API Endpoints
1. Add function to `api_client.py`
2. Use existing error handling patterns
3. Implement caching if appropriate

## Related Guides
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
