# Turnkey Coach Tools

A comprehensive command-line toolkit for fitness coaches using the Turnkey Coach platform. Streamline client management, workout programming, nutrition tracking, and AI-powered coaching through an intuitive terminal interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## Quick Start for Coaches

### macOS Installation

1. **Download** the latest DMG from [Releases](https://github.com/your-org/workout-parser/releases)
2. **Install** by dragging to Applications folder
3. **Open** (right-click → Open to bypass security warning)
4. **Login** with your Turnkey Coach credentials

### Windows Installation

1. **Download** the Setup.exe from [Releases](https://github.com/your-org/workout-parser/releases)
2. **Run** the installer (click "More info" → "Run anyway" for security prompt)
3. **Launch** from Start Menu
4. **Login** with your Turnkey Coach credentials

### Linux / Developer Installation

```bash
# Clone the repository
git clone https://github.com/your-org/workout-parser.git
cd workout-parser

# Create and activate virtual environment
python3 -m venv venv                   # On Linux
python3 -m venv .venv                  # On macOS (note the dot: .venv)
python -m venv venv                    # On Windows

source venv/bin/activate               # On Linux
source .venv/bin/activate              # On macOS
venv\Scripts\activate                  # On Windows

# Install dependencies
pip install -r requirements.txt

# Install as editable package (recommended for development)
pip install -e .

# Run the application (choose one method):
coach-cli                 # If installed with pip install -e .
python -m src.coach_cli   # Alternative method
```

**Running After Installation:**

Once installed, always activate the virtual environment before running:

```bash
# In the project directory
source venv/bin/activate      # On Linux
source .venv/bin/activate     # On macOS (note the dot: .venv)
venv\Scripts\activate         # On Windows

# Then run with either:
coach-cli                     # Recommended (if installed with pip install -e .)
python -m src.coach_cli       # Alternative
```

**Note:** If you see `command not found: coach-cli`, use `python -m src.coach_cli` instead, or reinstall with `pip install -e .`

---

## Core Features

### Client Management
- **Unified Feed** - Timeline of all client interactions (messages + comments)
- **Workout History** - Browse and export formatted workout histories
- **Actual PRs** - View official personal records from the platform
- **Estimated 1RMs** - Strength analysis using Wendler's formula with Wilks scores
- **Program Metrics** - Track body composition, performance, and custom metrics

### Workout & Nutrition Programming
- **Upload Workouts** - Parse and upload training programs from text files
- **Upload Nutrition** - Create nutrition assignments with check-ins and education
- **Dual Calendar** - Mix training and nutrition in the same file
- **Markup Validation** - Dry-run parser to test files before upload

### AI-Powered Assistance
- **AI Chat** - LLM programming assistant with workout context
- **Chat History** - Automatic session logging with search and browse
- **Session Management** - View, search, and edit past AI conversations
- **Context-Aware** - Loads recent workout history for informed suggestions
- **Dual LLM Support** - Works with OpenAI GPT and xAI Grok models
- **Smart Filtering** - Date range controls to manage token costs

### Advanced Features
- **Multi-Workspace** - Manage multiple coach accounts or brands
- **Bulk Sync** - Overnight data sync for all clients
- **Delete Workouts** - Filter and remove assignments (by date, type)
- **Metrics Tracking** - Fuzzy matching for flexible metric names

---

## Documentation

### For Coaches
- [macOS Installation Guide](docs/user-guides/installation-macos.md)
- [Markup Language Reference](docs/user-guides/markup-language.md)
- [Metrics Guide](docs/user-guides/metrics-guide.md)
- [Metrics in Markup](docs/user-guides/metrics-in-markup.md)

### For Developers
- [Architecture Overview](docs/developer-guides/01-Architecture-Overview.md)
- [API Client & Authentication](docs/developer-guides/02-API-Client-and-Authentication.md)
- [Feed Tool Deep Dive](docs/developer-guides/03-Feed-Tool-Deep-Dive.md)
- [Development Setup](docs/developer-guides/07-Development-Setup.md)
- [Full Developer Guide Index](docs/developer-guides/README.md)

### Build & Distribution
- [Building Guide](docs/build-guides/building.md)
- [Distribution Guide](docs/build-guides/distribution.md)
- [Development Workflow](docs/build-guides/workflow.md)

### Project
- [Contributing](docs/project/contributing.md)
- [Changelog](CHANGELOG.md)
- [Release Notes](docs/project/releases/)

---

## Project Structure

```
workout_parser/
├── src/                      # All Python source code
│   ├── coach_cli.py          # Main application entry point
│   ├── api_client.py         # Turnkey API integration
│   ├── settings.py           # Configuration management
│   ├── workspace_manager.py  # Multi-workspace support
│   ├── tools/                # Feature modules
│   │   ├── feed_tool.py      # Client feed viewer
│   │   ├── upload_tool.py    # Workout/nutrition uploader
│   │   ├── metrics_tool.py   # Metrics tracking
│   │   ├── ai_chat_tool.py   # AI programming assistant
│   │   └── ...               # Other tools
│   └── web_interface/        # Web UI (experimental)
│
├── scripts/                  # Build and utility scripts
│   ├── build/                # PyInstaller specs & build scripts
│   ├── install/              # Installation helpers
│   └── release/              # Release preparation
│
├── docs/                     # Documentation
│   ├── user-guides/          # End-user documentation
│   ├── developer-guides/     # Developer documentation
│   ├── build-guides/         # Build/distribution docs
│   └── project/              # Project management
│
├── tests/                    # Test suite
├── assets/                   # Icons and resources
└── archive/                  # Historical code
```

---

## Quick Examples

### Training Assignment
```markdown
Workout Date: 2025-10-18

Squat
3x5 @ 225
    Focus on hitting depth, keep chest up

Bench Press
1x5 @ RPE 8

Deadlift
1x3 @ 85%
```

### Nutrition Assignment
```markdown
Nutrition Date: 2025-10-18
@weight_kgs: 85.5
@body_fat: 15.2%

Nutrition Check-In
    How are you feeling this week?
    Tell me about your energy levels.

    Fun fact: Protein needs increase 20-25% during intensive
    strength training phases!
```

### Mixed Assignment
```markdown
Workout Date: 2025-10-18
Squat
3x5 @ 225

---
Nutrition Date: 2025-10-18
@weight_kgs:
@sleep: 8 hours

Nutrition Check-In
    How did you sleep? Rate your energy 1-10.
```

---

## Security Note

The pre-built apps (DMG/EXE) will show security warnings because they aren't code-signed. This is normal and expected - code signing costs $99/year per platform, and the apps work identically with or without it.

**The apps are completely safe:**
- ✅ Open source - full transparency
- ✅ Only connects to Turnkey Coach servers
- ✅ No data collection or telemetry
- ✅ Encrypted credential storage

---

## Requirements

- **macOS**: macOS 10.15+
- **Windows**: Windows 10/11 (64-bit)
- **Linux**: Python 3.8+ (run from source)
- **API Access**: Valid Turnkey Coach account

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING](docs/project/contributing.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

**Latest Release:** v1.5.0
- Multi-workspace support
- Enhanced sync reliability
- Windows compatibility improvements

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

### Common Issues

**"No clients showing"**
- Check internet connection
- Verify login credentials
- Try logging out and back in

**"App won't open" (macOS/Windows)**
- Follow security warning workarounds above
- Right-click → Open (macOS)
- "More info" → "Run anyway" (Windows)

**"Upload failed"**
- Use "Validate Markup" tool first
- Check file format against examples
- Verify date formats (YYYY-MM-DD)

**"Slow performance"**
- First load takes time with large histories
- Consider using Bulk Sync overnight
- Subsequent loads are faster (cached)

### Getting Help

- 📖 Check the [documentation](docs/)
- 🐛 [Report bugs](https://github.com/your-org/workout-parser/issues)
- 💡 [Request features](https://github.com/your-org/workout-parser/issues)
- 📧 Contact: [your-email@example.com]

---

## Acknowledgments

- Built for coaches, by coaches
- Powered by the Turnkey Coach platform
- Uses OpenAI and xAI for AI features

---

**Version 1.5.0** • [Download Latest Release](https://github.com/your-org/workout-parser/releases) • **Built with ❤️ for the coaching community**
