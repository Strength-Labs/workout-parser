# Architecture Overview

## Purpose
This guide provides a high-level overview of the Turnkey Coach Tools codebase architecture, including module organization, data flow, and design patterns.

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                   coach_cli.py (Main)                       │
│  - Workspace selection on startup                           │
│  - Client selection with bulk sync                          │
│  - Tool menu (8 tools + utilities)                          │
│  - Delete workouts, notes, cleanup                          │
└─────────────────────────────────────────────────────────────┘
              │                             │
              ↓                             ↓
┌─────────────────────────┐   ┌──────────────────────────────┐
│  workspace_manager.py   │   │     api_client.py            │
│  - Multi-workspace      │   │  - Auth & token caching      │
│  - Workspace switching  │   │  - Client list (roles)       │
│  - Logout per workspace │   │  - Smart workout sync        │
│  - Directory mgmt       │   │  - Deletion detection        │
└─────────────────────────┘   │  - Delete operations         │
              │               │  - Metric catalog            │
              ├───────────────┤  - Exercise map w/ types     │
              ↓               │  - Headless mode support     │
┌─────────────────────────┐   └──────────────────────────────┘
│   directory_migration   │                 │
│  - Workspace-aware dirs │                 │
│  - Legacy migration     │                 ↓
└─────────────────────────┘   ┌──────────────────────────────┐
              ↓               │     Tool Modules (8)         │
┌─────────────────────────┐   │  1. feed_tool.py             │
│      settings.py        │   │  2. pr_tool.py               │
│  - Workspace config     │   │  3. actual_prs_tool.py       │
│  - Multi-workspace creds│   │  4. upload_tool.py           │
│  - Editor, LLM keys     │   │  5. ai_chat_tool.py          │
└─────────────────────────┘   │  6. metrics_tool.py          │
                              │  7. format_tool.py           │
                              │  8. bulk_sync.py             │
                              └──────────────────────────────┘
                                            │
              ┌─────────────────────────────┼────────────┐
              ↓                             ↓            ↓
┌─────────────────────┐   ┌───────────────────────┐   ┌──────────────┐
│  encoding_utils.py  │   │   External Services   │   │ Bulk Ops     │
│  - UTF-8 handling   │   │  - Turnkey Coach API  │   │ - Parallel   │
│  - Safe JSON ops    │   │  - OpenAI/xAI APIs    │   │ - Headless   │
└─────────────────────┘   └───────────────────────┘   └──────────────┘
```

## Module Organization

### Core Modules

#### 1. **coach_cli.py** (651 lines)
- **Purpose**: Main application entry point and UI orchestration
- **Key Functions**:
  - `main()`: Application lifecycle management with workspace selection
  - `select_client()`: Client selection interface with bulk sync option
  - `show_tool_menu()`: Tool navigation (8 tools + utilities)
  - `adjust_settings()`: Settings configuration
  - `delete_workouts_ui()`: Interactive workout deletion with filtering
  - `clean_client_directory()`: Directory cleanup utility
  - `add_note()`: Quick note-taking for clients
  - `run_bulk_sync_from_cli()`: Bulk sync launcher
- **Dependencies**: All tool modules, api_client, settings, workspace_manager

#### 2. **api_client.py** (618 lines)
- **Purpose**: API communication layer, shared utilities, and workspace-aware caching
- **Key Functions**:
  - `get_access_token()`: Authentication with caching and legacy token scanning
  - `get_clients()`: Fetch coach's client list with grouped roles
  - `get_workout_history()`: Smart workout sync with deletion detection
  - `get_workout_history_headless()`: Silent version for bulk operations
  - `delete_workout_by_id()`: Delete individual workout
  - `delete_workouts_filtered()`: Batch deletion with filtering
  - `fetch_metric_catalog()`: Canonical metric catalog lookup
  - `load_exercise_map()`: Exercise database with type information
  - `get_exercise_id()` / `get_exercise_type()`: Safe exercise lookups
- **Dependencies**: requests, settings, directory_migration, encoding_utils, workspace_manager

### Tool Modules

#### 3. **feed_tool.py** (886 lines)
- **Purpose**: Unified feed for messages and workout comments
- **Key Features**:
  - Incremental caching of messages and workouts with timestamp-based updates
  - Real-time data aggregation via background threads
  - Navigation mode with vim-like keybindings
  - Export to text files with context enrichment
  - Headless mode for bulk sync operations
- **Dependencies**: api_client, directory_migration, encoding_utils, settings

#### 4. **pr_tool.py** (237 lines)
- **Purpose**: Estimated 1RM calculator from workout history
- **Key Features**:
  - Wendler formula for e1RM calculation
  - Wilks score computation
  - Date range filtering (3m/6m/year/all/custom)
- **Dependencies**: api_client

#### 5. **actual_prs_tool.py** (144 lines)
- **Purpose**: Official PR viewer from API
- **Key Features**:
  - Direct PR data from platform
  - Date filtering with same options as estimated PRs
  - Exercise-specific records with actual vs estimated differentiation
- **Dependencies**: api_client

#### 6. **upload_tool.py** (513 lines)
- **Purpose**: Workout and nutrition file parser and uploader with dry-run validation
- **Key Features**:
  - Custom markup parsing for workouts and nutrition
  - Fuzzy exercise matching (rapidfuzz) with interactive selection
  - Unit detection (lbs/kg)
  - Nutrition calendar routing and metric line ingestion
  - Metric catalog validation and resolution
  - Dry-run mode for validation without uploading
  - Batch assignment upload (workouts + nutrition + metrics)
- **Dependencies**: api_client, encoding_utils, rapidfuzz

#### 7. **metrics_tool.py** (603 lines)
- **Purpose**: Standalone CLI for programming and uploading client metrics
- **Key Features**:
  - Single metric entry with guided prompts
  - Bulk metric entry via CSV-like input
  - View client metrics with date range filtering
  - Metric catalog lookup with friendly aliases
  - Smart type detection (integer/decimal/scale/text)
  - Unit normalization and validation
  - Placeholder metric support (empty values)
- **Dependencies**: api_client, directory_migration, encoding_utils, requests

#### 8. **ai_chat_tool.py** (451 lines)
- **Purpose**: AI-powered workout planning assistant
- **Key Features**:
  - OpenAI/xAI integration with provider selection
  - Context loading from workout history and custom files
  - In-editor response editing
  - Direct workout upload from AI responses
  - Token estimation for context management
  - Temperature control for non-reasoning models
- **Dependencies**: api_client, format_tool, upload_tool, settings, openai

#### 9. **bulk_sync.py** (316 lines)
- **Purpose**: Parallel bulk synchronization of all clients
- **Key Features**:
  - Concurrent client syncing with ThreadPoolExecutor
  - Configurable worker count (2-4 workers)
  - Test mode for limited client subset
  - Progress tracking with live updates
  - Headless API calls (no Rich console interference)
  - Error aggregation and reporting
- **Dependencies**: api_client, feed_tool, encoding_utils, concurrent.futures

### Supporting Modules

#### 10. **format_tool.py** (186 lines)
- **Purpose**: Workout and nutrition data formatting to custom markup with metrics support
- **Key Functions**:
  - `format_workouts_to_markup()`: JSON to text conversion with metrics integration
  - `format_time()`: Time formatting for sets
  - `_format_metric_line()`: Metric formatting for markup output
- **Nutrition/Metrics Support**: Emits `Nutrition Date:` blocks, nutrition catalog items, and `@metric` lines directly from API payloads
- **Dependencies**: api_client, metrics_tool

#### 11. **encoding_utils.py** (141 lines)
- **Purpose**: Cross-platform UTF-8 file handling
- **Key Functions**:
  - `safe_open()`: UTF-8 file operations
  - `safe_json_dump()`/`safe_json_load()`: JSON with proper encoding
  - `read_text_file()`/`write_text_file()`: Text file utilities
- **Dependencies**: None (stdlib only)

#### 12. **directory_migration.py** (370 lines)
- **Purpose**: File system structure management with workspace awareness
- **Key Functions**:
  - `get_client_dir()`: Workspace-aware client-specific directories
  - `get_shared_dir()`: Workspace-aware shared data location
  - `perform_migration()`: Legacy structure migration
  - Workspace path resolution and validation
- **Dependencies**: rich, settings

#### 13. **settings.py** (282 lines)
- **Purpose**: Configuration and credentials management with multi-workspace support
- **Key Functions**:
  - `load_or_init_settings()`: First-time setup
  - `get_default_editor()`: Editor configuration
  - `get_stored_credentials()`: Encrypted credential retrieval
  - `get_llm_credentials()`: AI API key management
  - `list_workspaces()`: List available workspaces
  - `get_current_workspace()`: Retrieve active workspace
  - Workspace-specific credential management
- **Dependencies**: cryptography, encoding_utils

#### 14. **workspace_manager.py** (465 lines)
- **Purpose**: Multi-workspace management for coaches handling multiple companies
- **Key Functions**:
  - `workspace_selector()`: Interactive workspace selection on startup
  - `setup_new_workspace()`: Create new workspace with credentials
  - `quick_workspace_switcher()`: Switch workspaces without restart
  - `logout_current_workspace()`: Clear workspace credentials
  - `ensure_workspace_directories()`: Create workspace directory structure
  - `get_workspace_info()`: Display current workspace details
- **Dependencies**: settings, directory_migration, api_client, rich

#### 15. **workspace_setup.py** (186 lines)
- **Purpose**: Workspace initialization and first-run setup
- **Key Functions**:
  - Interactive workspace creation wizard
  - Company name collection and validation
  - Workspace key generation
  - Credential encryption setup
- **Dependencies**: workspace_manager, settings

## Data Flow Patterns

### Workspace Selection Flow (New in v1.5)
```
User Launch → coach_cli.main()
    ↓
workspace_manager.workspace_selector()
    ↓
List available workspaces from settings
    ↓
[No workspaces] → Create first workspace
[1 workspace] → Auto-select
[Multiple] → Show selection menu
    ↓
Set active workspace in environment
    ↓
Resolve workspace-aware directories
    ↓
Proceed to authentication
```

### Authentication Flow
```
Workspace Selected → main_with_workspace_selected()
    ↓
Check Token Cache (~/Turnkey-{workspace}/shared/.tokencache)
    ↓
[Cache Valid] → Use Cached Token
[Cache Invalid/Missing] → Scan for legacy tokens in other workspaces
    ↓
[Legacy Token Found] → Reuse token
[No Legacy Token] → Get Stored Credentials from workspace settings
    ↓
[Credentials Found] → Auto-login
[No Credentials] → Prompt for email/password
    ↓
API POST /users/tokens/sign_in
    ↓
Save token + expiry + user_id to workspace cache
```

### Workout History Flow (Smart Sync with Deletion Detection)
```
Tool requests workout data
    ↓
Check cache: ~/Turnkey-{workspace}/clients/{client_id}/workouts_user_{client_id}.json
    ↓
[Force Refresh] → Download all from API
[Cache exists] → Smart Sync:
    ├── Fetch lightweight workout ID list from API
    ├── Compare cached IDs vs server IDs
    ├── Detect deletions (in cache but not on server)
    ├── Detect additions (on server but not in cache)
    ├── Remove deleted workouts from cache
    └── Fetch only new/missing workouts
    ↓
Merge + sort → Save to cache
    ↓
Return complete workout list
```

### Bulk Sync Flow (New Feature)
```
User selects Bulk Sync → run_bulk_sync_from_cli()
    ↓
Choose sync mode (2 workers / 4 workers / test mode)
    ↓
Fetch complete client list
    ↓
Create ThreadPoolExecutor with N workers
    ↓
For each client in parallel:
    ├── get_workout_history_headless() → Smart sync (silent)
    ├── fetch_and_aggregate_data_headless() → Feed sync (silent)
    └── Track progress (success/error/skipped)
    ↓
Aggregate results across all clients
    ↓
Display summary (X succeeded, Y errors)
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

### Nutrition & Metrics Flow
```
Coach edits markup block
    ↓
upload_tool.parse_markup()
    ↓
Split blocks by header → Workout vs Nutrition
    ↓
Resolve exercises + nutrition catalog names
    ↓
Collect @metric lines → map to metric catalog entries
    ↓
POST assignments to /api/v1/workouts (workout_type = default|nutrition)
POST metrics to /api/v1/metrics
    ↓
Summaries logged in CLI + cached locally
```

[Further Reading: `METRICS_GUIDE.md`](../METRICS_GUIDE.md) describes the canonical metric catalog and API payloads, while [`METRICS_IN_MARKUP.md`](../METRICS_IN_MARKUP.md) documents how those metrics map to markup syntax.

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
**Purpose**: Persistent user preferences with multi-workspace support

**Stored Data**:
- Default text editor (platform-aware defaults)
- Encrypted credentials (email/password for auto-login) per workspace
- LLM provider and API key (encrypted) per workspace
- Workspace registry with active workspace tracking

**Location**: `~/.turnkey_coach_settings.json`

**Structure**:
```json
{
  "default_editor": ["code", "-w"],
  "active_workspace": "default",
  "workspaces": {
    "default": {
      "company_name": "My Company",
      "email": "coach@example.com",
      "encrypted_password": "gAAAAABh...",
      "encryption_key": "dGVzdGtleQ==..."
    },
    "acme-fitness": {
      "company_name": "ACME Fitness",
      "email": "coach@acmefitness.com",
      ...
    }
  }
}
```

### 5. Headless Mode Pattern (New in v1.5)
**Purpose**: Enable silent bulk operations without Rich console output

**Implementation**:
- Duplicate functions with `_headless` suffix (e.g., `get_workout_history_headless()`)
- Remove all Rich console status messages and prints
- Return structured data instead of displaying to user
- Used by `bulk_sync.py` for parallel operations

**Examples**:
- `api_client.get_workout_history()` → User-facing with progress
- `api_client.get_workout_history_headless()` → Silent for bulk sync
- `feed_tool.fetch_and_aggregate_data()` → Interactive
- `feed_tool.fetch_and_aggregate_data_headless()` → Background

### 6. Workspace Isolation Pattern (New in v1.5)
**Purpose**: Separate data for coaches working with multiple companies

**Implementation**:
- Each workspace has isolated:
  - Client directories
  - Exercise lists
  - Token caches
  - Credentials
- Workspace key used in directory paths: `~/Turnkey-{workspace_key}/`
- Settings file contains workspace registry
- Active workspace tracked in environment/settings

**Benefits**:
- Clean separation of business entities
- No credential mixing
- Easy switching without re-auth
- Legacy single-workspace still supported

## Directory Structure

### Runtime Directories (Workspace-Aware)
```
~/Turnkey-{workspace_key}/       # Multi-workspace support (v1.5+)
├── clients/                     # Per-client data
│   └── {client_id}/
│       ├── workouts_user_{id}.json         # Cached workouts
│       ├── workouts_index.json             # Workout metadata index
│       ├── messages_cache.json             # Conversation cache
│       ├── feed_cache.json                 # Unified feed cache
│       ├── {client}_history_{timestamp}.txt # Exported histories
│       ├── Unified_Feed_{client}_{ts}.txt  # Exported feeds
│       └── note-{date}.txt                 # Coach notes
├── shared/
│   ├── exerciselist.json        # Exercise database
│   ├── .tokencache              # Auth token (workspace-specific)
│   └── coaching_context/        # AI chat context files
│       └── *.md, *.txt          # Custom context documents
└── cache/                       # Reserved for future use

~/.turnkey_coach_settings.json   # Global settings + workspace registry
```

**Workspace Examples**:
- `~/Turnkey-default/` - Default workspace (legacy single-company setup)
- `~/Turnkey-acme-fitness/` - ACME Fitness company workspace
- `~/Turnkey-powerhouse/` - Powerhouse Gym workspace

### Application Directory
```
workout-parser/
├── coach_cli.py                 # Main entry point (651 lines)
├── api_client.py                # API layer (618 lines)
├── workspace_manager.py         # Workspace management (465 lines)
├── workspace_setup.py           # Workspace init (186 lines)
├── bulk_sync.py                 # Bulk sync utility (316 lines)
├── feed_tool.py                 # Feed viewer (886 lines)
├── pr_tool.py                   # Estimated PRs (237 lines)
├── actual_prs_tool.py           # API PRs (144 lines)
├── upload_tool.py               # Workout uploader (513 lines)
├── ai_chat_tool.py              # AI assistant (451 lines)
├── metrics_tool.py              # Metrics tool (603 lines)
├── format_tool.py               # Data formatting (186 lines)
├── encoding_utils.py            # UTF-8 utilities (141 lines)
├── directory_migration.py       # File system mgmt (370 lines)
├── settings.py                  # Configuration (282 lines)
├── requirements.txt             # Dependencies
├── README.md                    # User documentation
├── markup.md                    # Markup language spec
└── DevGuides/                   # Developer documentation
    ├── TOC.md
    ├── 01-Architecture-Overview.md
    ├── 02-API-Client-and-Authentication.md
    ├── 03-Feed-Tool-Deep-Dive.md
    ├── 04-PR-Analysis-Tools.md
    ├── 05-Workout-Management.md
    ├── 06-Data-Formats-and-Caching.md
    └── 07-Development-Setup.md
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
4. Add menu option in `show_tool_menu()` (coach_cli.py:498-557)
5. Update DevGuides documentation with tool details

### Custom Markup Extensions
1. Add new set type parsing in `upload_tool.py:parse_line_as_set()`
2. Add formatting in `format_tool.py:format_workouts_to_markup()`
3. Update `markup.md` specification

### New API Endpoints
1. Add function to `api_client.py`
2. Use existing error handling patterns
3. Implement caching if appropriate
4. Consider headless version for bulk operations
5. Update workspace-aware path resolution if needed

### Adding New Workspaces
1. User selects "Create New Workspace" from client list
2. `workspace_manager.setup_new_workspace()` launches wizard
3. Collect company name and credentials
4. Generate workspace key from company name
5. Create workspace directory: `~/Turnkey-{workspace_key}/`
6. Save workspace config to settings
7. User can switch between workspaces via [ws] option or restart

## Related Guides
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [03-Feed-Tool-Deep-Dive.md](./03-Feed-Tool-Deep-Dive.md)
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md)
