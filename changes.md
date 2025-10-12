# Changes to ai_chat_tool.py

- Removed automatic prompt for saving workout plans.
- Added keyword commands:
  - 'edit': Opens the last AI response in an editor in the client's directory, allows tweaking, updates the conversation history with the edited content, and optionally saves to a file.
  - 'upload': Provides options to upload either the last AI response or a selected file from the client's directory to the Turnkey API.
  - 'quit': Alias for 'exit' to quit the chat.
- Updated welcome message to reflect new commands.

This enables collaborative workout development between the coach and AI, as requested.