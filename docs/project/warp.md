# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Alternative for specific packages
pip install requests rich rapidfuzz cryptography openai httpx pyreadline3
```

### Running the Application
```bash
# Main CLI entry point
python coach_cli.py

# Individual tool modules (for development/testing)
python feed_tool.py
python pr_tool.py
python actual_prs_tool.py
python format_tool.py
python upload_tool.py
python ai_chat_tool.py
```

### Testing Individual Components
```bash
# Test API connectivity (requires auth)
python -c "from api_client import get_access_token; print(get_access_token())"

# Test exercise list loading
python -c "from api_client import load_exercise_map; print(len(load_exercise_map()))"

# Test workout parsing
python -c "from upload_tool import parse_workouts_from_file; print('Parser loaded')"
```

### Data Management
```bash
# Clean up client directories (done via CLI menu)
# Force refresh workout caches (done via CLI menu)
# Update exercise database (done via CLI menu)

# Manual cache inspection
find ~/Turnkey -name "*.json" -type f

# View cached data
python -c "import json; print(json.load(open('~/Turnkey/shared/exerciselist.json'))[:3])"

# Run directory migration (if upgrading from old structure)
python directory_migration.py
```

## Architecture Overview

### Core Application Structure
The application is a modular Python CLI toolkit built around the Rich library for terminal UI. The main entry point (`coach_cli.py`) orchestrates authentication, client selection, and tool dispatch.

### Key Architectural Components

#### 1. Authentication & API Layer (`api_client.py`)
- Token-based authentication with automatic caching (`.tokencache`)
- Centralized API client for Turnkey Coach platform
- Incremental data synchronization with local caching
- Shared utilities for text cleaning and data processing

#### 2. Tool Modules (Separate Python files)
Each tool is a self-contained module:
- **Feed Tool** (`feed_tool.py`): Unified message/comment timeline with threading
- **PR Analyzers** (`pr_tool.py`, `actual_prs_tool.py`): Different approaches to analyzing personal records
- **Workout Browser** (`format_tool.py`): Converts workout data to readable markup
- **Workout Uploader** (`upload_tool.py`): Parses text files and uploads via fuzzy exercise matching
- **AI Chat** (`ai_chat_tool.py`): LLM integration for workout programming assistance  
- **Metrics Tool** (`metrics_tool.py`): Client metrics tracking and analysis (v1.4.0+)
- **Dual Calendar Support**: Training and nutrition assignments with comprehensive metrics (v1.4.0+)

#### 3. Data Caching Strategy
- **New directory structure** (with automatic migration from old):
  - Base directory: `~/Turnkey/` (renamed from `~/TurnkeyClients/`)
  - Client data: `~/Turnkey/clients/{client_id}/`
  - Shared data: `~/Turnkey/shared/` (exercise database, auth tokens)
  - Coaching context: `~/Turnkey/shared/coaching_context/`
- **Incremental sync**: Only downloads changed data using API timestamps
- **Cache file types**:
  - Workout data: `workouts_user_{client_id}.json`
  - Messages: `messages_cache.json` 
  - Workout index: `workouts_index.json`
  - Exercise database: `exerciselist.json` (now in shared directory)
  - Auth tokens: `.tokencache` (now in shared directory)

#### 4. Settings Management (`settings.py`)
- Encrypted credential storage using Fernet encryption
- Editor preferences and defaults
- LLM provider configuration

### Data Flow Architecture

1. **Authentication**: Token cached locally, auto-refresh on expiry
2. **Client Selection**: Fetches coach-client relationships from API
3. **Tool Execution**: Each tool manages its own data requirements
4. **Caching**: Tools use shared caching utilities from `api_client.py`
5. **File Operations**: Tools work in client-specific directories for data isolation

### Key Integration Points

#### Exercise Matching System
- Fuzzy string matching using RapidFuzz for workout uploads
- Centralized exercise database with ID mapping
- Interactive disambiguation for ambiguous matches

#### Rich UI Components
- Panels, tables, and status indicators throughout
- Keyboard navigation in feed views (j/k, q, u, m, c, /)
- Color coding for different data types and states

#### External Editor Integration
- Configurable editor support via `$EDITOR` environment variable
- Temporary file handling for AI chat editing
- Working directory management for file operations

### Important Behavioral Notes

- The application assumes a single-coach workflow (though supports multiple clients)
- **Directory migration**: Automatically migrates from old `~/TurnkeyClients/` to new `~/Turnkey/` structure
- All file operations happen in user's home directory under `Turnkey/`
- Network requests are handled with proper error handling and user feedback
- Caching is aggressive but respects API rate limits through incremental updates
- The AI chat feature supports both OpenAI and xAI (Grok) with encrypted key storage
- Auth data moved from app directory to `~/Turnkey/shared/` for better organization

### Development Patterns
- Each tool module can be run independently for testing
- Shared functionality is centralized in `api_client.py`
- Directory management abstracted through `directory_migration.py` module
- Cross-platform encoding handled by `encoding_utils.py` module
- Rich console object is passed around or recreated as needed
- Error handling focuses on graceful degradation with user feedback
- All file I/O operations use UTF-8 encoding for Windows compatibility
- Migration logic ensures backward compatibility for existing users
