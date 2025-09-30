# Turnkey Coach Tools

A comprehensive set of command-line interface (CLI) tools designed for fitness coaches using the Turnkey Coach platform. These tools streamline client management, workout analysis, and data interaction through an intuitive terminal-based application.

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Tools Overview](#tools-overview)
- [Dependencies](#dependencies)
- [API Client](#api-client)
- [Contributing](#contributing)
- [License](#license)

## Description

Turnkey Coach Tools provides coaches with powerful CLI utilities to interact with the Turnkey Coach API. The suite includes tools for viewing unified feeds, analyzing personal records, browsing workout histories, uploading workouts, and managing client data. Built with Python, it leverages modern libraries for a rich user experience and efficient data handling.

## Features

- **Client Management**: Authenticate and select from your list of clients
- **Unified Feed**: Aggregate and interact with messages and workout comments in chronological order
- **PR Analysis**: Calculate estimated 1RM using Wendler's formula and compute Wilks scores
- **Actual PRs Viewer**: Fetch and display official personal records directly from the API
- **Workout History Browser**: Save formatted workout histories to markup files for review in your editor
- **Workout Uploader**: Parse workout text files and upload to the platform with fuzzy exercise matching
- **Utilities**: Add notes, clean up directories, refresh caches, and update exercise lists
- **Caching**: Intelligent caching of workout data and messages to reduce API calls
- **Rich CLI**: Beautiful terminal interface with panels, tables, and interactive menus

## Installation

1. Ensure you have Python 3.7+ installed
2. Clone the repository containing these tools
3. Navigate to the `turnkey-coach-tools` directory
4. Install dependencies:

```bash
pip install requests rich rapidfuzz
```

Note: `rapidfuzz` is required for the workout uploader's fuzzy matching feature. If not needed, you can omit it, but the uploader will have reduced functionality.

## Usage

1. Run the main CLI application:

```bash
python coach_cli.py
```

2. Enter your Turnkey Coach email and password when prompted
3. Select a client from the displayed list
4. Choose from the available tools in the client menu

### Keyboard Shortcuts

- Use arrow keys or j/k for navigation in feeds
- Press `q` to quit menus
- Press `u` to refresh data
- In feed view: `m` to send message, `c` to reply to comments, `/` to search

## Tools Overview

### 1. Unified Feed
- Combines messages from conversations and comments from workouts
- Chronological timeline of all client interactions
- Search functionality with highlighting
- Reply to messages or workout comments directly
- Export feed to text file for archiving

### 2. Estimated 1RMs (from history)
- Analyzes workout history to find best performances
- Calculates estimated 1RM using Wendler's formula
- Supports date range filtering (3 months, 6 months, year, all time, custom)
- Wilks score calculation for powerlifting totals
- Displays main lifts (Squat, Bench Press, Deadlift, Press) prominently

### 3. Actual PRs (from API)
- Fetches official personal records stored in the platform
- Shows both actual 1RM and estimated 1RM for multi-rep sets
- Date range filtering
- Displays all lifts, not just main compound movements

### 4. Browse & Save Workout History
- Downloads and caches detailed workout data
- Formats workouts into readable markup
- Opens saved files in your default editor ($EDITOR)
- Incremental caching to avoid re-downloading unchanged data

### 5. Upload Workout from File
- Parses workout text files in custom markup format
- Fuzzy matching for exercise names using RapidFuzz
- Interactive selection for ambiguous matches
- Supports various set formats (weight/reps, RPE, percentage, time-based)
- Auto-detects weight units (lbs/kg)

### Utilities
- **Add a Quick Note**: Create timestamped notes in client directories
- **Clean Up Directory**: Remove temporary files and generated exports
- **Force Refresh Workout History**: Clear cache and re-download data
- **Update Exercise List**: Download latest exercise database from API

## Dependencies

- **requests**: HTTP library for API communication
- **rich**: Terminal styling and interactive elements
- **rapidfuzz** (optional): Fuzzy string matching for exercise names
- **Standard library**: json, datetime, os, re, etc.

## API Client

The `api_client.py` module provides shared functionality:

- Authentication with token caching
- Client list retrieval
- Workout history downloading with incremental updates
- Exercise list management
- Shared helper functions for text cleaning and caching

## File Structure

```
turnkey-coach-tools/
├── coach_cli.py          # Main CLI application
├── api_client.py         # Shared API functions
├── feed_tool.py          # Unified feed functionality
├── pr_tool.py            # Estimated PR analyzer
├── actual_prs_tool.py    # Actual PRs viewer
├── format_tool.py        # Workout markup formatter
├── upload_tool.py        # Workout uploader
├── exerciselist.json     # Exercise database (downloaded)
├── plan.txt              # Example workout plan
├── messages_cache.json   # Cached messages (generated)
├── workouts_index.json   # Workout cache index (generated)
└── feed_cache.json       # Feed cache (generated)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

Ensure code follows Python best practices and includes appropriate error handling.

## License

This project is licensed under the MIT License - see the LICENSE file in the parent directory for details.

## Support

For issues or questions:

- Check the Turnkey Coach API documentation
- Ensure all dependencies are installed
- Verify your account has appropriate permissions
- Clear caches (`messages_cache.json`, `workouts_index.json`) if experiencing issues

Last updated: 2025-09-30
