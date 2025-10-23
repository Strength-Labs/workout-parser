"""
Tests for AI chat history logging and search functionality.
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.ai_chat_tool import create_chat_session_log, log_chat_exchange, get_first_user_prompt, search_chat_history
from src.encoding_utils import read_text_file


def test_create_session_log():
    """Test creating a new chat session log file."""
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    try:
        # Mock the client directory function
        import src.tools.ai_chat_tool as ai_chat_tool
        import src.directory_migration as dm
        original_get_client_dir = ai_chat_tool.get_client_dir
        ai_chat_tool.get_client_dir = lambda client_id: temp_dir

        # Create a session log
        log_path, session_start = create_chat_session_log(123, "Test Client")

        # Verify the file was created
        assert os.path.exists(log_path), "Log file should be created"

        # Verify it's in the ai_chats subdirectory
        assert "ai_chats" in log_path, "Log should be in ai_chats directory"

        # Verify the file has proper header
        content = read_text_file(log_path)
        assert "AI Chat Session - Test Client" in content, "Header should contain client name"
        assert "Date:" in content, "Header should contain date"
        assert "Time:" in content, "Header should contain time"

        print("✓ Session log created successfully")

        # Restore original function
        ai_chat_tool.get_client_dir = original_get_client_dir

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_log_chat_exchange():
    """Test logging a chat exchange."""
    # Create a temporary file
    temp_dir = tempfile.mkdtemp()
    log_path = os.path.join(temp_dir, "test_session.md")

    try:
        # Create initial file
        from src.encoding_utils import write_text_file
        write_text_file(log_path, "# Test Session\n\n---\n\n")

        # Log an exchange
        user_prompt = "Write a squat program for strength"
        ai_response = "Here's a squat program:\n- Week 1: 5x5 @ 80%\n- Week 2: 3x5 @ 85%"

        log_chat_exchange(log_path, user_prompt, ai_response)

        # Verify the exchange was logged
        content = read_text_file(log_path)
        assert user_prompt in content, "User prompt should be in log"
        assert ai_response in content, "AI response should be in log"
        assert "### " in content, "Should have markdown headers for exchanges"
        assert "User:" in content, "Should label user prompts"
        assert "AI Response:" in content, "Should label AI responses"

        print("✓ Chat exchange logged successfully")

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_first_user_prompt():
    """Test extracting first user prompt from a log file."""
    temp_dir = tempfile.mkdtemp()
    log_path = os.path.join(temp_dir, "test_session.md")

    try:
        # Create a test log file
        from src.encoding_utils import write_text_file
        content = """# AI Chat Session - Test Client
**Date:** 2025-10-19
**Time:** 2:30 PM

---

### [02:30 PM] User:
Create a deadlift progression for the next 4 weeks

### AI Response:
Here's your deadlift progression...

---

### [02:35 PM] User:
What about accessory work?

### AI Response:
Add Romanian deadlifts...

---

"""
        write_text_file(log_path, content)

        # Get the first prompt
        first_prompt = get_first_user_prompt(log_path)

        # Verify it extracted the correct prompt
        assert "Create a deadlift progression" in first_prompt, "Should extract first user prompt"
        assert "accessory work" not in first_prompt, "Should not include second prompt"

        print("✓ First user prompt extracted successfully")

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_search_chat_history():
    """Test searching chat history."""
    temp_dir = tempfile.mkdtemp()
    ai_chats_dir = os.path.join(temp_dir, "ai_chats")
    os.makedirs(ai_chats_dir)

    try:
        # Mock the client directory function
        import src.tools.ai_chat_tool as ai_chat_tool
        original_get_client_dir = ai_chat_tool.get_client_dir
        ai_chat_tool.get_client_dir = lambda client_id: temp_dir

        # Create test chat log files
        from src.encoding_utils import write_text_file

        # File 1 - contains "squat"
        file1 = os.path.join(ai_chats_dir, "2025-10-19_2-30pm.md")
        write_text_file(file1, """# Session 1
### User:
Create a squat program for strength

### AI Response:
Here's your squat progression...
""")

        # File 2 - contains "deadlift"
        file2 = os.path.join(ai_chats_dir, "2025-10-19_3-00pm.md")
        write_text_file(file2, """# Session 2
### User:
I need help with deadlift technique

### AI Response:
Focus on bracing and hip hinge...
""")

        # File 3 - contains "bench press"
        file3 = os.path.join(ai_chats_dir, "2025-10-19_4-15pm.md")
        write_text_file(file3, """# Session 3
### User:
Bench press accessory work?

### AI Response:
Add dumbbell presses and tricep work...
""")

        # Search for "squat"
        results = search_chat_history(123, "squat")
        assert len(results) == 1, "Should find 1 file with 'squat'"
        assert "2025-10-19_2-30pm.md" in results[0][0], "Should find the correct file"

        # Search for "deadlift"
        results = search_chat_history(123, "deadlift")
        assert len(results) == 1, "Should find 1 file with 'deadlift'"
        assert "3-00pm" in results[0][0], "Should find the correct file"

        # Search for "press" (should find bench press file)
        results = search_chat_history(123, "press")
        assert len(results) >= 1, "Should find at least 1 file with 'press'"

        # Search for term that doesn't exist
        results = search_chat_history(123, "olympic lifting")
        assert len(results) == 0, "Should find no files with 'olympic lifting'"

        print("✓ Search functionality works correctly")

        # Restore original function
        ai_chat_tool.get_client_dir = original_get_client_dir

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_long_prompt_truncation():
    """Test that long prompts are truncated in preview."""
    temp_dir = tempfile.mkdtemp()
    log_path = os.path.join(temp_dir, "test_session.md")

    try:
        # Create a test log with a very long first prompt
        from src.encoding_utils import write_text_file
        long_prompt = "A" * 100  # 100 characters
        content = f"""# AI Chat Session
---

### [02:30 PM] User:
{long_prompt}

### AI Response:
Response here
"""
        write_text_file(log_path, content)

        # Get the first prompt
        first_prompt = get_first_user_prompt(log_path)

        # Verify it's truncated
        assert len(first_prompt) <= 80, "Should truncate to 80 chars"
        assert "..." in first_prompt, "Should include ellipsis"

        print("✓ Long prompts truncated correctly")

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all chat history tests."""
    print("Running AI Chat History Tests...")
    print("=" * 60)

    test_create_session_log()
    test_log_chat_exchange()
    test_get_first_user_prompt()
    test_search_chat_history()
    test_long_prompt_truncation()

    print("=" * 60)
    print("✅ All chat history tests passed!")


if __name__ == '__main__':
    run_all_tests()
