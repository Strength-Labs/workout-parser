#!/bin/bash
# Turnkey Coach Tools - Enhanced iTerm Launcher

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

# Set up environment
export PYTHONPATH="$RESOURCES_DIR:$PYTHONPATH"

# Change to the resources directory where our Python files are
cd "$RESOURCES_DIR"

# Check if Python 3 is installed
if ! command -v python3 >/dev/null 2>&1; then
    osascript -e 'display dialog "Python 3 is required but not installed. Please install Python 3.8 or later from python.org" with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon stop'
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
    osascript -e "display dialog \"Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or later is required.\" with title \"Turnkey Coach Tools\" buttons {\"OK\"} default button 1 with icon stop"
    exit 1
fi

# Install dependencies if needed
if [ ! -f "$RESOURCES_DIR/.deps_installed" ]; then
    osascript -e 'display dialog "Installing dependencies... This may take a moment." with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon note giving up after 3'
    
    if python3 -m pip install -r "$RESOURCES_DIR/requirements.txt" --user --quiet; then
        touch "$RESOURCES_DIR/.deps_installed"
    else
        osascript -e 'display dialog "Failed to install dependencies. Please check your internet connection and try again." with title "Turnkey Coach Tools" buttons {"OK"} default button 1 with icon stop'
        exit 1
    fi
fi

# Function to launch in iTerm
launch_iterm() {
    osascript <<APPLESCRIPT
tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "cd '$RESOURCES_DIR' && python3 coach_cli.py"
        set name to "Turnkey Coach Tools"
    end tell
end tell
APPLESCRIPT
}

# Function to launch in Terminal (fallback)
launch_terminal() {
    osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    set newTab to do script "cd '$RESOURCES_DIR' && python3 coach_cli.py"
    set custom title of newTab to "Turnkey Coach Tools"
end tell
APPLESCRIPT
}

# Try to launch in iTerm first, fallback to Terminal
if /usr/bin/osascript -e 'tell application "System Events" to (name of processes) contains "iTerm2"' >/dev/null 2>&1 || command -v iTerm >/dev/null 2>&1; then
    # iTerm is available
    launch_iterm
else
    # Fallback to Terminal
    launch_terminal
fi