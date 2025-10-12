# Development Setup and Contribution Guide

## Purpose
This guide provides setup instructions, development workflows, testing strategies, and contribution guidelines for developers working on the Turnkey Coach Tools codebase.

## Prerequisites

### Required Software
- **Python 3.7+** (Tested on 3.9, 3.10, 3.11)
- **pip** (Python package installer)
- **Git** (Version control)
- **Text editor or IDE** (VS Code, PyCharm, vim, etc.)

### Optional Software
- **Virtual environment tool** (venv, virtualenv, conda)
- **Code formatter** (black, autopep8)
- **Linter** (pylint, flake8)

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd workout-parser
```

### 2. Set Up Virtual Environment (Recommended)

**Using venv (built-in)**:
```bash
python -m venv .venv

# Activate
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

**Using conda**:
```bash
conda create -n turnkey-coach python=3.10
conda activate turnkey-coach
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt Contents**:
```
requests==2.32.3
rapidfuzz==3.14.0
rich==13.7.1
cryptography==42.0.5
openai==2.2.0
pyreadline3; sys_platform == "win32"  # Windows only
httpx==0.24.1
```

### 4. Verify Installation
```bash
python coach_cli.py
```

Should prompt for credentials on first run.

## Project Structure

```
workout-parser/
├── .venv/                       # Virtual environment (gitignored)
├── .git/                        # Git repository
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
├── README.md                    # User documentation
├── markup.md                    # Markup language specification
│
├── coach_cli.py                 # Main entry point
├── api_client.py                # API layer
├── settings.py                  # Configuration management
├── encoding_utils.py            # UTF-8 utilities
├── directory_migration.py       # File system management
│
├── feed_tool.py                 # Unified feed
├── pr_tool.py                   # Estimated PRs
├── actual_prs_tool.py           # Actual PRs
├── upload_tool.py               # Workout uploader
├── format_tool.py               # Workout formatter
├── ai_chat_tool.py              # AI assistant
│
├── backups/                     # Backup files (if any)
├── oldstuff/                    # Deprecated code
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

## Development Workflow

### Branch Strategy

**Main Branches**:
- `main`: Production-ready code
- `develop`: Integration branch for features

**Feature Branches**:
- `feature/feature-name`: New features
- `bugfix/bug-description`: Bug fixes
- `refactor/refactor-description`: Code refactoring

**Example**:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/add-wilks-calculator
# Make changes
git add .
git commit -m "Add Wilks score calculator to PR tool"
git push origin feature/add-wilks-calculator
# Create pull request
```

### Code Style

#### Python Style Guide
Follow **PEP 8** with these conventions:
- **Indentation**: 4 spaces (no tabs)
- **Line length**: 120 characters max (flexible for readability)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private functions: `_leading_underscore`

#### Formatting Tools

**Black** (recommended):
```bash
pip install black
black coach_cli.py api_client.py
```

**autopep8**:
```bash
pip install autopep8
autopep8 --in-place --aggressive coach_cli.py
```

#### Linting Tools

**pylint**:
```bash
pip install pylint
pylint coach_cli.py
```

**flake8**:
```bash
pip install flake8
flake8 coach_cli.py --max-line-length=120
```

### Documentation Standards

#### Docstrings
Use **Google-style docstrings**:

```python
def process_workout_history(workouts, start_date=None, end_date=None):
    """Processes workout history to find the best e1RM for every exercise in a date range.

    Args:
        workouts (list): List of workout dictionaries from API
        start_date (date, optional): Filter start date. Defaults to None.
        end_date (date, optional): Filter end date. Defaults to None.

    Returns:
        dict: Mapping of exercise names to best performance data.
            Format: {exercise_name: {'e1rm': float, 'weight': float, 'reps': int, ...}}

    Example:
        >>> workouts = get_workout_history(token, client)
        >>> best = process_workout_history(workouts, start_date=date(2025, 1, 1))
        >>> print(best['squat']['e1rm'])
        450.5
    """
    ...
```

#### Inline Comments
Use inline comments sparingly, for non-obvious logic:

```python
# Fallback to assigned sets if workout completed but no actual_sets recorded
if is_completed and not actual_sets:
    weight = float(assigned_set.get("weight", 0) or 0)
```

### Testing

#### Manual Testing Checklist

**Authentication**:
- [ ] First-time login with credentials
- [ ] Auto-login with stored credentials
- [ ] Token expiry and refresh
- [ ] Logout and credential clearing

**Client Selection**:
- [ ] Display client list
- [ ] Select client by number
- [ ] Handle invalid selection
- [ ] Multiple coaches per client

**Feed Tool**:
- [ ] Load cached feed instantly
- [ ] Background refresh completes
- [ ] Message posting
- [ ] Comment replying
- [ ] Search functionality
- [ ] Navigation (j/k/vim mode)
- [ ] Export to text file

**PR Tools**:
- [ ] Estimated PRs calculation
- [ ] Date range filtering
- [ ] Wilks score calculation
- [ ] Actual PRs from API
- [ ] Main vs other lifts

**Workout Management**:
- [ ] Browse history in editor
- [ ] Upload workout from file
- [ ] Fuzzy exercise matching
- [ ] Unit detection (lbs/kg)
- [ ] AI chat with context loading
- [ ] Edit AI responses

**Settings**:
- [ ] Change editor
- [ ] Change credentials
- [ ] LLM provider configuration

#### Unit Testing (Future)

**Suggested Framework**: pytest

**Example Test Structure**:
```python
# tests/test_pr_tool.py
import pytest
from pr_tool import wendler_1rm, process_workout_history

def test_wendler_1rm_actual_max():
    """Test that 1RM returns weight directly."""
    assert wendler_1rm(405, 1) == 405

def test_wendler_1rm_calculation():
    """Test Wendler formula for multi-rep sets."""
    result = wendler_1rm(385, 5)
    assert 449 < result < 450  # Approximately 449.1

def test_process_workout_history_empty():
    """Test handling of empty workout history."""
    result = process_workout_history([])
    assert result == {}
```

**Run Tests**:
```bash
pip install pytest
pytest tests/
```

#### Integration Testing

**Test API Integration**:
1. Set up test account on Turnkey Coach
2. Create test client with sample workouts
3. Run full workflow manually
4. Verify cache files created correctly

**Test Data Locations**:
- Test client directory: `~/Turnkey/clients/test_client_id/`
- Test settings: Use separate settings file for testing

### Debugging

#### Console Logging

Use `rich.console` for debugging output:

```python
from rich.console import Console
console = Console()

# Debug prints
console.print("[yellow]Debug: Processing workout...[/yellow]")
console.print(f"[dim]workout_id={workout_id}, date={workout_date}[/dim]")

# Inspect objects
import json
console.print(json.dumps(workout_data, indent=2))
```

#### Print Statement Debugging

**DON'T** use `print()` - it bypasses Rich formatting and may have encoding issues.

**DO** use `console.print()` for all output.

#### Python Debugger (pdb)

**Insert breakpoint**:
```python
import pdb; pdb.set_trace()
```

**Commands**:
- `n` (next): Execute next line
- `c` (continue): Continue execution
- `p variable`: Print variable
- `l` (list): Show code context
- `q` (quit): Exit debugger

#### VS Code Debugging

**launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Coach CLI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/coach_cli.py",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

## Common Development Tasks

### Adding a New Tool

**1. Create tool module**:
```python
# new_tool.py
from rich.console import Console
from api_client import API_BASE_URL

console = Console()

def run_new_tool(token, client):
    """Main function for new tool."""
    console.print("[bold]New Tool[/bold]")
    # Implementation...
```

**2. Import in coach_cli.py**:
```python
from new_tool import run_new_tool
```

**3. Add menu option**:
```python
def show_tool_menu(token, user_id, client, exercise_map):
    while True:
        console.print("  [bold]7.[/bold] New Tool")  # Add here
        choice = console.input("\n> ").lower()

        if choice == '7':  # Add handler
            run_new_tool(token, client)
```

### Adding a New API Endpoint

**1. Add function to api_client.py**:
```python
def get_new_data(token, client_id):
    """Fetch new data from API."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/new_endpoint"
    params = {"user_id": client_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        console.print(f"[bold red]Error: {err}[/bold red]")
        return None
```

**2. Add caching if appropriate**:
```python
def get_new_data(token, client_id):
    cache_path = os.path.join(get_client_dir(client_id), "new_data_cache.json")

    # Check cache
    if os.path.exists(cache_path):
        data = safe_json_load(cache_path)
        if data:
            return data

    # Fetch from API
    data = _fetch_new_data_from_api(token, client_id)
    if data:
        safe_json_dump(data, cache_path)

    return data
```

### Extending the Markup Parser

**1. Add new set type to parse_line_as_set()**:

```python
# upload_tool.py
def parse_line_as_set(line: str):
    # ... existing patterns ...

    # New pattern: Distance-based
    match = re.match(r"(\d+)\s*x\s*(\d+\.?\d*)\s*(m|km|miles)", line, re.IGNORECASE)
    if match:
        sets, distance, unit = match.groups()
        parsed = {
            **base_set,
            "sets": int(sets),
            "distance": float(distance),
            "distance_unit": unit.lower(),
            "weight": None,
            "weight_type": "bodyweight"
        }
        return parsed

    # ... continue with other patterns ...
```

**2. Add formatting to format_workouts_to_markup()**:

```python
# format_tool.py
def format_workouts_to_markup(workouts, coach_user_id):
    # ... existing formatting ...

    for assigned_set in exercise['assigned_sets']:
        # New formatting for distance sets
        if assigned_set.get('distance', 0) > 0:
            sets = assigned_set.get('sets', 1)
            distance = assigned_set.get('distance')
            unit = assigned_set.get('distance_unit', 'm')
            display = f"{sets} x {distance} {unit}"
            output_lines.append(display)
        # ... other formatting ...
```

**3. Update markup.md documentation**:
```markdown
### Distance-Based Sets
Format: `{sets} x {distance} {unit}`

Examples:
- `5 x 400 m` - 5 sets of 400 meters
- `1 x 5 km` - 1 set of 5 kilometers
```

### Adding Configuration Options

**1. Update settings.py**:
```python
def load_or_init_settings():
    settings = safe_json_load(SETTINGS_FILE)
    if settings:
        return settings

    # ... existing setup ...

    # New setting
    new_option = console.input("New option (y/n): ").lower() == 'y'

    settings = {
        # ... existing settings ...
        'new_option': new_option
    }
    safe_json_dump(settings, SETTINGS_FILE)
    return settings
```

**2. Create getter function**:
```python
def get_new_option():
    """Retrieve new option from settings."""
    settings = load_or_init_settings()
    return settings.get('new_option', False)  # Default to False
```

**3. Use in application**:
```python
from settings import get_new_option

if get_new_option():
    # Feature enabled
    ...
```

## Contributing Guidelines

### Before Submitting

**Checklist**:
- [ ] Code follows PEP 8 style
- [ ] All functions have docstrings
- [ ] UTF-8 encoding used for all file I/O
- [ ] Error handling implemented
- [ ] Manual testing completed
- [ ] No sensitive data (credentials, tokens) in code
- [ ] Git history is clean (no temp commits like "wip", "test")

### Pull Request Process

**1. Create feature branch**:
```bash
git checkout -b feature/descriptive-name
```

**2. Commit changes**:
```bash
git add .
git commit -m "feat: Add descriptive commit message

- Detail 1
- Detail 2
- Closes #issue-number"
```

**Commit Message Format**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

**3. Push and create PR**:
```bash
git push origin feature/descriptive-name
```

Create pull request on GitHub/GitLab with:
- Clear description of changes
- Reference to related issues
- Screenshots (if UI changes)
- Testing notes

**4. Code Review**:
- Address reviewer feedback
- Update PR with requested changes
- Respond to comments

**5. Merge**:
- Squash and merge or merge commit (per project standards)
- Delete feature branch after merge

### Issue Reporting

**Bug Report Template**:
```markdown
**Description**
Clear description of the bug.

**To Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen?

**Actual Behavior**
What actually happened?

**Environment**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Python Version: [e.g., 3.10.5]
- Tool Version: [git commit hash or version number]

**Additional Context**
- Error messages (full traceback)
- Screenshots
- Relevant log output
```

**Feature Request Template**:
```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
What other approaches were considered?

**Additional Context**
- Mockups or diagrams
- Related features in other tools
```

## Performance Optimization

### Profiling

**Using cProfile**:
```bash
python -m cProfile -o profile.stats coach_cli.py
```

**Analyze results**:
```python
import pstats
from pstats import SortKey

p = pstats.Stats('profile.stats')
p.strip_dirs()
p.sort_stats(SortKey.CUMULATIVE)
p.print_stats(20)  # Top 20 functions
```

### Common Optimizations

**1. Use generators for large datasets**:
```python
# DON'T:
all_workouts = [process_workout(w) for w in workouts]

# DO:
def process_workouts(workouts):
    for w in workouts:
        yield process_workout(w)
```

**2. Batch API requests**:
```python
# Use ThreadPoolExecutor for parallel requests
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(fetch_workout, wid) for wid in workout_ids]
    results = [f.result() for f in futures]
```

**3. Cache expensive computations**:
```python
# Use functools.lru_cache
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_expensive_metric(data):
    # Expensive calculation
    ...
```

## Security Considerations

### Never Commit Sensitive Data
- **Credentials**: Use settings.py with encryption
- **Tokens**: Store in cache files (gitignored)
- **API Keys**: Use environment variables or settings

**.gitignore**:
```
.venv/
*.pyc
__pycache__/
.tokencache
exerciselist.json
*.json  # Cache files
*.txt   # Generated files
!requirements.txt
!markup.md
```

### Input Validation
Always validate user input:

```python
# DON'T:
choice = int(input("> "))  # ValueError if not a number

# DO:
try:
    choice = int(input("> "))
    if 0 <= choice < len(options):
        # Valid
    else:
        console.print("[red]Invalid choice[/red]")
except ValueError:
    console.print("[red]Please enter a number[/red]")
```

### API Security
- Always use HTTPS (enforced by API_BASE_URL)
- Token in Authorization header (never in URL)
- Validate API responses before use

## Deployment

### Creating a Release

**1. Update version number**:
```python
# coach_cli.py or __version__.py
__version__ = "1.2.0"
```

**2. Update CHANGELOG.md**:
```markdown
## [1.2.0] - 2025-10-11

### Added
- Wilks score calculator
- AI chat tool with context loading

### Fixed
- Unicode handling in workout comments
- Feed refresh race condition

### Changed
- Improved incremental caching performance
```

**3. Tag release**:
```bash
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

**4. Create GitHub release**:
- Use tag v1.2.0
- Copy CHANGELOG content
- Attach binaries if applicable

### Distribution

**PyPI Package** (future):
```bash
pip install turnkey-coach-tools
```

**Standalone Executable** (using PyInstaller):
```bash
pip install pyinstaller
pyinstaller --onefile --name turnkey-coach coach_cli.py
```

## Troubleshooting Development Issues

### Import Errors
**Symptom**: `ModuleNotFoundError`

**Solutions**:
1. Activate virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version`

### Encoding Errors
**Symptom**: `UnicodeDecodeError` or `UnicodeEncodeError`

**Solutions**:
1. Use `encoding_utils` functions exclusively
2. Set terminal encoding to UTF-8
3. On Windows: `chcp 65001` in CMD

### Git Conflicts
**Symptom**: Merge conflicts on pull

**Solutions**:
1. Stash changes: `git stash`
2. Pull latest: `git pull origin develop`
3. Apply stash: `git stash pop`
4. Resolve conflicts manually
5. Commit: `git add . && git commit -m "Resolve merge conflicts"`

### Performance Issues
**Symptom**: Slow application startup or operations

**Solutions**:
1. Profile with cProfile
2. Check cache file sizes
3. Optimize hot paths (see Performance Optimization section)
4. Consider database for large datasets

## Resources

### Documentation
- [Python Official Docs](https://docs.python.org/3/)
- [Rich Library Docs](https://rich.readthedocs.io/)
- [Requests Library Docs](https://requests.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)

### Tools
- [VS Code](https://code.visualstudio.com/)
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [Black Formatter](https://black.readthedocs.io/)
- [pytest](https://docs.pytest.org/)

### Learning Resources
- [Real Python](https://realpython.com/)
- [Python Patterns](https://python-patterns.guide/)
- [Clean Code in Python](https://github.com/zedr/clean-code-python)

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md) - System architecture
- [06-Data-Formats-and-Caching.md](./06-Data-Formats-and-Caching.md) - Data handling
- All other guides in DevGuides/ folder
