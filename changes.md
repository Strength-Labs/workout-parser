# Changes to ai_chat_tool.py

- Removed automatic prompt for saving workout plans.
- Added keyword commands:
  - 'edit': Opens the last AI response in an editor in the client's directory, allows tweaking, updates the conversation history with the edited content, and optionally saves to a file.
  - 'upload': Provides options to upload either the last AI response or a selected file from the client's directory to the Turnkey API.
  - 'quit': Alias for 'exit' to quit the chat.
- Updated welcome message to reflect new commands.

This enables collaborative workout development between the coach and AI, as requested.

# October 2025 Code Review Follow-Up

- Removed the committed `.venv/` virtual environment and expanded `.gitignore` to keep caches, build outputs, and IDE metadata out of version control.
- Centralized exercise lookup logic in `api_client.py` via `get_exercise_id` and `get_exercise_type`, refactoring `upload_tool.py` and CLI call sites to rely on the helpers.
- Added metric catalog caching plus a dry-run validation mode to the upload workflow so coaches can preview parsing issues without hitting the API.
- Moved sample markup into `docs/examples/`, introduced `tests/fixtures/`, and created `tests/test_upload_tool.py` for baseline pytest coverage of nutrition and metric parsing.
- Updated developer documentation (architecture overview, workout management guide, TOC, markup references) and published a new `CONTRIBUTING.md` to capture workflow expectations.
