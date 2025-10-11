"""
Minimal cross-platform encoding utilities for Turnkey Coach tools.

Provides consistent UTF-8 file I/O and JSON handling across Windows, macOS, and Linux.
Windows has particular challenges with file encoding that this module addresses.
"""

import json
import tempfile
import os
from typing import Any, Dict, Optional
from contextlib import contextmanager

# Standard encoding settings
ENCODING = 'utf-8'


def safe_open(filepath: str, mode: str = 'r', **kwargs):
    """
    Open files with UTF-8 encoding by default.
    
    Args:
        filepath: Path to file
        mode: File open mode ('r', 'w', 'a', etc.)
        **kwargs: Additional arguments passed to open()
    
    Returns:
        File object
    """
    # Set UTF-8 encoding for text modes unless explicitly specified
    if 'b' not in mode and 'encoding' not in kwargs:
        kwargs['encoding'] = ENCODING
    
    return open(filepath, mode, **kwargs)


def safe_json_dump(obj: Any, filepath: str, **kwargs) -> None:
    """
    Save JSON to file with proper Unicode handling.
    
    Args:
        obj: Object to serialize
        filepath: Path to save file
        **kwargs: Additional arguments for json.dump()
    """
    # Ensure Unicode characters are preserved
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('indent', 2)
    
    with safe_open(filepath, 'w') as f:
        json.dump(obj, f, **kwargs)


def safe_json_load(filepath: str, default: Any = None, **kwargs) -> Any:
    """
    Load JSON from file with error handling.
    
    Args:
        filepath: Path to JSON file
        default: Value to return if file doesn't exist or is invalid
        **kwargs: Additional arguments for json.load()
    
    Returns:
        Parsed JSON object or default value
    """
    try:
        with safe_open(filepath, 'r') as f:
            return json.load(f, **kwargs)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return default


@contextmanager
def safe_temp_file(mode: str = 'w+', suffix: str = '', dir: Optional[str] = None, **kwargs):
    """
    Create temporary file with UTF-8 encoding.
    
    WARNING: This context manager deletes the file when exiting.
    If you need the file to persist after the context (e.g., for external editors),
    use tempfile.NamedTemporaryFile(delete=False) manually.
    
    Args:
        mode: File mode
        suffix: File suffix (e.g., '.txt')
        dir: Directory for temp file
        **kwargs: Additional arguments for NamedTemporaryFile
    
    Yields:
        NamedTemporaryFile object (file will be deleted on context exit)
    """
    # Set UTF-8 encoding for text modes
    if 'b' not in mode and 'encoding' not in kwargs:
        kwargs['encoding'] = ENCODING
    
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, dir=dir, delete=False, **kwargs) as temp_file:
        try:
            yield temp_file
        finally:
            # Clean up
            try:
                os.unlink(temp_file.name)
            except (OSError, FileNotFoundError):
                pass


def read_text_file(filepath: str) -> str:
    """
    Read text file with UTF-8 encoding.
    
    Args:
        filepath: Path to file
    
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file cannot be decoded as UTF-8
    """
    with safe_open(filepath, 'r') as f:
        return f.read()


def write_text_file(filepath: str, content: str) -> None:
    """
    Write text to file with UTF-8 encoding.
    
    Args:
        filepath: Path to file
        content: Text content to write
    """
    with safe_open(filepath, 'w') as f:
        f.write(content)