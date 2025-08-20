# Workout Parser and Uploader

A Python suite for parsing workout plans from plain text files into JSON and uploading them to the Barbell Logic Turnkey Coach API (`POST /api/v1/workouts`). The suite includes three scripts:

- **`workout_parser.py`**: Converts plain text workout files (e.g., `john.txt`) into JSON (e.g., `john.json`) compatible with the API.
- **`workout_uploader.py`**: Authenticates with the Turnkey Coach API and uploads JSON workouts to the `POST /api/v1/workouts` endpoint.
- **`fetch_exercises.py`**: Retrieves the exercise list from the API (`GET /api/v1/exercises`) and saves it as `exerciselist.json` for use by `workout_parser.py`.

## Features

- **Parsing** (`workout_parser.py`):
  - Parses workouts in a markdown-like format with tab-indented notes.
  - Supports weight-based (e.g., `3x5 @ 400`), RPE-based (e.g., `1x1 @ RPE 10`), AMRAP (e.g., `1xAMRAP @ 135`), distance-based (e.g., `2.5 miles @ 00:20:00`), and text-based (e.g., `2x8 @ light`) sets.
  - Uses fuzzy matching to resolve unrecognized exercise names.
  - Requires `exerciselist.json` in the script’s directory for exercise ID mapping.
  - Generates JSON files (e.g., `input.txt` → `input.json`).

- **Uploading** (`workout_uploader.py`):
  - Authenticates with the Turnkey Coach API using email and password.
  - Caches access tokens in `.tokencache` for reuse within 1 hour.
  - Uploads single or multiple workout JSON objects to the API.

- **Exercise List Retrieval** (`fetch_exercises.py`):
  - Fetches the exercise list from the `GET /api/v1/exercises` endpoint.
  - Saves the list as `exerciselist.json` for use by `workout_parser.py`.
  - Uses the same authentication mechanism as `workout_uploader.py`.
  - See the [API Documentation](https://app.turnkey.coach/api-docs/index.html) for endpoint details.

## Barbell Logic Context

The suite supports Barbell Logic’s training principles, including:
- RPE-based programming (e.g., `1x1 @ RPE 10`).
- AMRAP sets (e.g., `1xAMRAP @ 135`).
- Main lifts: `Squat`, `Bench Press`, `Deadlift`, `Press`.

For specific requirements or API details, refer to the [API Documentation](https://app.turnkey.coach/api-docs/index.html) or open a GitHub issue.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/strength-labs/workout-parser.git
   cd workout-parser
2. Install Dependencies
```
pip install -r requirements.txt
```


This installs `fuzzywuzzy`, `python-Levenshtein`, and `requests`.

3. **Prepare `exerciselist.json`**: put exerciselist.json in the same directory as the script. 

## Usage

### Fetching the Exercise List with `fetch_exercises.py`
Fetches the exercise list from the Turnkey Coach API (`GET /api/v1/exercises`) and saves it as `exerciselist.json`.

1. Ensure `fetch_exercises.py` is in the `workout-parser` directory.
2. Run:
   ```bash
   python fetch_exercises.py
   ```
3. Enter your email and password for the Turnkey Coach API.
4. The script authenticates, retrieves the exercise list, and saves it as `exerciselist.json`.
5. Verify `exerciselist.json` contains exercises (e.g., `Squat`, `Bench Press`) with IDs matching the API.

**Note**: Ensure your API credentials have access to `GET /api/v1/exercises`. See the [API Documentation](https://app.turnkey.coach/api-docs/index.html) for details.

### Parsing Workouts with `workout_parser.py`
Converts a plain text workout file into JSON compatible with the `POST /api/v1/workouts` endpoint.

1. Place `workout_parser.py`, `exerciselist.json`, and your input file (e.g., `john.txt`) in the same directory.
2. Run:
   ```bash
   python workout_parser.py
   ```
3. Enter the user ID (e.g., `6130`). You can see this in the URL at the top of a client workout, or look it up in the directory in the Turnkey app. 
4. Enter the input file path (e.g., `john.txt`).
5. For unrecognized exercises:
   - Select a suggested exercise from `exerciselist.json` (via fuzzy matching).
   - Enter a different exercise name (must match `exerciselist.json`).
   - Skip the exercise (sets `exercise_id` to `null`).
6. The script generates a JSON file (e.g., `john.json`).

### Uploading Workouts with `workout_uploader.py`
Uploads the generated JSON file to the Turnkey Coach API.

1. Ensure the JSON file (e.g., `john.json`) is available.
2. Run:
   ```bash
   python workout_uploader.py
   ```
3. Enter your email and password for API authentication.
4. Enter the JSON file path (e.g., `john.json`) or `q` to quit.
5. The script authenticates, caches the token in `.tokencache`, and uploads each workout.

### Example Workflow
1. Create `john.txt`:
   ```
   Workout Date: 2025-08-20

   Deadlift
     1x5 @ 360
   Bench Press
     1x5 @ 227.5
     2x5 @ 192.5

   Workout Date: 2025-08-27

   Squat
     1x5 @ 315
       Work up to a heavy single.
   Press
     1x5 @ 170
     2x5 @ 145
     1xAMRAP @ 135
   ```
2. Run `fetch_exercises.py` to generate `exerciselist.json`.
3. Run `workout_parser.py` to generate `john.json`.
4. Run `workout_uploader.py` to upload `john.json` to the API.

## Input File Format (for `workout_parser.py`)

The input file uses a markdown-like structure with tab-indented notes.

### Structure
- **Workout Date**: Begins with `Workout Date:` followed by `YYYY-MM-DD`.
- **Exercises**: Non-indented lines matching names in `exerciselist.json`.
- **Sets**: Non-indented in the format 3x5@300 or 3xAMRAP@300. 
- **Notes**: Tab-indented lines under an exercise (start with `\s+`).
- **Blank Lines**: Ignored.

### Example Input File (`john.txt`)
```
Workout Date: 2025-08-20

Deadlift
1x5 @ 360
Bench Press
1x5 @ 227.5
2x5 @ 192.5

Workout Date: 2025-08-27

Squat
1x5 @ 315
    Work up to a heavy single.

Press
1x5 @ 170
2x5 @ 145
1xAMRAP @ 135
```

### Format Details
- **Workout Date**: `Workout Date: YYYY-MM-DD` (e.g., `Workout Date: 2025-08-20`).
- **Exercises**: Non-indented, must match `exerciselist.json` (case-insensitive) or be resolved via prompts.
- **Sets**:
  - **Weight-based**: `setsxreps @ weight` (e.g., `3x5 @ 400`).
  - **RPE-based**: `setsxreps @ RPE value` (e.g., `1x1 @ RPE 10`).
  - **AMRAP**: `setsxAMRAP @ weight` (e.g., `1xAMRAP @ 135`).
  - **Distance-based**: `distance unit @ HH:MM:SS` (e.g., `2.5 miles @ 00:20:00`).
  - **Text-based**: `setsxreps @ description` (e.g., `2x8 @ light`).
- **Notes**: Tab-indented (e.g., `    Work up to a heavy single.`).

### Notes on Indentation
- Use **tabs** (preferred) or **spaces** for notes (detected via regex `^\s+`).
- Exercises and sets must be non-indented or minimally indented.
- Consistent indentation (e.g., one tab per note) is recommended.

## Output JSON Format (from `workout_parser.py`)

The output JSON aligns with the `POST /api/v1/workouts` endpoint (see [API Documentation](https://app.turnkey.coach/api-docs/index.html)):
- **Top-level**: Array of workout objects.
- **Workout object**:
  - `user_id`: Integer (e.g., `6130`).
  - `workout_date`: String (e.g., `2025-08-20`).
  - `weight_type`: String (default: `"lbs"`).
  - `assigned_exercises`: Array of exercise objects.
- **Exercise object**:
  - `exercise_id`: Integer (from `exerciselist.json` or `null` if skipped).
  - `priority`: Integer (order of exercises, starting at 0).
  - `assigned_sets`: Array of set objects.
- **Set object**:
  - `priority`: Integer (order of sets).
  - `sets`: Integer.
  - `reps`: Integer (`0` for AMRAP).
  - `weight`: Float (optional).
  - `weight_type`: String (e.g., `"default_weight_type"`, `"RPE"`).
  - `weight_type_value`: Integer (optional, for RPE).
  - `rep_type`: String (e.g., `"default_rep_type"`, `"AMRAP"`).
  - `set_type`: String (e.g., `"default"`, `"custom"`).
  - `body`: String (optional, for text-based sets or notes).
  - `distance`: Float (optional).
  - `distance_unit`: String (e.g., `"miles"`, optional).
  - `time`: Integer (seconds, optional).

### Example Output (`john.json`)
```
[
  {
    "user_id": 6130,
    "workout_date": "2025-08-20",
    "weight_type": "lbs",
    "assigned_exercises": [
      {
        "exercise_id": 1008,
        "priority": 0,
        "assigned_sets": [
          {
            "priority": 0,
            "sets": 1,
            "reps": 5,
            "weight": 360.0,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          }
        ]
      },
      {
        "exercise_id": 1007,
        "priority": 1,
        "assigned_sets": [
          {
            "priority": 0,
            "sets": 1,
            "reps": 5,
            "weight": 227.5,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          },
          {
            "priority": 1,
            "sets": 2,
            "reps": 5,
            "weight": 192.5,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          }
        ]
      }
    ]
  },
  {
    "user_id": 6130,
    "workout_date": "2025-08-27",
    "weight_type": "lbs",
    "assigned_exercises": [
      {
        "exercise_id": 794,
        "priority": 0,
        "assigned_sets": [
          {
            "priority": 0,
            "sets": 1,
            "reps": 5,
            "weight": 315.0,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          },
          {
            "priority": 1,
            "set_type": "custom",
            "body": "Work up to a heavy single."
          }
        ]
      },
      {
        "exercise_id": 1009,
        "priority": 1,
        "assigned_sets": [
          {
            "priority": 0,
            "sets": 1,
            "reps": 5,
            "weight": 170.0,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          },
          {
            "priority": 1,
            "sets": 2,
            "reps": 5,
            "weight": 145.0,
            "weight_type": "default_weight_type",
            "rep_type": "default_rep_type",
            "set_type": "default"
          },
          {
            "priority": 2,
            "sets": 1,
            "reps": 0,
            "weight": 135.0,
            "weight_type": "default_weight_type",
            "rep_type": "AMRAP",
            "set_type": "default"
          }
        ]
      }
    ]
  }
]
```

## Updating `exerciselist.json`
If you cannot fetch the exercise list via `fetch_exercises.py`, manually create `exerciselist.json` with exercises matching the API’s IDs.

Example:
```
[
  {
    "id": 794,
    "name": "Squat",
    "video_url": null,
    "exercise_type": "resistance"
  },
  {
    "id": 1007,
    "name": "Bench Press",
    "video_url": null,
    "exercise_type": "resistance"
  },
  {
    "id": 1008,
    "name": "Deadlift",
    "video_url": null,
    "exercise_type": "resistance"
  },
  {
    "id": 1009,
    "name": "Press",
    "video_url": null,
    "exercise_type": "resistance"
  }
]
```

## Requirements
Dependencies are listed in `requirements.txt`:
```
fuzzywuzzy==0.18.0
python-Levenshtein==0.25.1
requests==2.32.3
```

## Contributing
Contributions are welcome! Follow these steps:
1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push: `git push origin feature/your-feature`.
5. Open a Pull Request.

For issues or feature requests, open an issue on GitHub.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Notes
- **Exercise IDs**: Ensure `exerciselist.json` matches the API’s exercise IDs (e.g., 794 for `Squat`, 1007 for `Bench Press`). See the [API Documentation](https://app.turnkey.coach/api-docs/index.html) for details. Reconcile if different.
- **API Endpoint**: The uploader uses `https://app.turnkey.coach` by default. Set the `API_BASE_URL` environment variable to override.
- **Token Caching**: Access tokens are cached in `.tokencache` for 1 hour.
- **Bodyweight and Light Sets**: Sets like `2x8 @ light` are parsed as `set_type: "custom"`. Contact the developer for specific `weight_type` values (e.g., `weight: 0`).
- **Time-Based Sets**: For time-based sets (e.g., `2x30s @ bodyweight`), contact the developer to add support.
- **Workout ID**: The API may require a `workout_id`. Contact the developer to add mapping logic or input support.

## Troubleshooting
- **Missing `exerciselist.json`**: Run `fetch_exercises.py` or manually create it.
- **Unrecognized Exercises**: Update `exerciselist.json` or use fuzzy matching prompts.
- **Incorrect Note Parsing**: Ensure notes are tab-indented.
- **Authentication Issues**: Verify email/password and API base URL. Check the [API Documentation](https://app.turnkey.coach/api-docs/index.html).
- **API Errors**: Check the API response in the uploader’s error message. Refer to the [API Documentation](https://app.turnkey.coach/api-docs/index.html) for schema details.
- **Contact**: For issues or enhancements (e.g., RPE validation, time-based sets), open a GitHub issue.

---
