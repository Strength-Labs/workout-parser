
# Workout Parser and Uploader

A Python suite for parsing workout plans from plain text files into JSON and uploading them to the Barbell Logic Turnkey Coach API (`POST /api/v1/workouts`). The suite includes five scripts:
* **`workout_downloader.py`**: downloads workouts from the Turnkey Coach API in JSON format
* **`json2markup.py`**: converts downloaded JSON workouts into a plain text strength workout markup format.
- **`workout_parser.py`**: Converts plain text workout files (e.g., `john.txt`) into JSON (e.g., `john.json`) compatible with the API.
- **`workout_uploader.py`**: Authenticates with the Turnkey Coach API and uploads JSON workouts to the `POST /api/v1/workouts` endpoint.
- **`fetch_exercises.py`**: Retrieves the exercise list from the API (`GET /api/v1/exercises`) and saves it as `exerciselist.json` for use by `workout_parser.py`.
* **`pr_downloader.py`**: Retrieves and sorts the PRs as stored on the Turnkey Coach servers.
* **`pr_analyzer.py`**: Outputs the highest estimated one-rep-maximums over a particular time period, using workouts in JSON format downloaded with **workout_downloader.py**.

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
  - Fetches the exercise list from the API and saves as `exerciselist.json`.
  - Uses the same authentication mechanism as `workout_uploader.py`.
  - See the [API Documentation](https://app.turnkey.coach/api-docs/index.html) for endpoint details.

## The Strength Coaching Markup Language

See [Markup Documentation](markup.md) for details. 

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
   ```
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Prepare `exerciselist.json`**: Put `exerciselist.json` in the same directory as the script.

Fetch the exercise list from the API using `fetch_exercises.py` (see "Usage: Fetching the Exercise List") or manually create it (see "Updating exerciselist.json").

## Usage

Here’s documentation for `workout_downloader.py` based on its actual code and command-line usage:

---

### Downloading Workouts with `workout_downloader.py`

This script authenticates with the Turnkey Coach API and downloads workouts for a specified user, including all comments and full workout details.

**Command-Line Usage:**

1. Make sure `workout_downloader.py` is in your working directory.

2. Run the script from the command line and provide required arguments:
   ```bash
   python workout_downloader.py --user_id <USER_ID> [--start_date YYYY-MM-DD] [--end_date YYYY-MM-DD]
   ```
   - `--user_id` (required): The client user ID to download workouts for.  
     *To find the user ID, see the calendar page URL in the Turnkey Coach web app (e.g., `https://app.turnkey.coach/calendar?id=9999#current_view=month` — use the number after `id=`).*
   - `--start_date` (optional): Filter workouts from this date (format `YYYY-MM-DD`).
   - `--end_date` (optional): Filter workouts up to this date (format `YYYY-MM-DD`).

3. When prompted, enter your Turnkey Coach API email and password.  
   - The script will use a cached token from `.tokencache` if available and valid (tokens last 1 hour).
   - If no valid token is found, authentication is performed.

4. The script fetches all workouts for the specified user (and date range, if provided), then downloads full details for each workout, including comments.

5. All retrieved workouts are saved into a file named:
   ```
   workouts_user_<USER_ID>.json
   ```
   For example: `workouts_user_9999.json`

6. You’ll see console output indicating progress and any errors.

**Example:**
```bash
python workout_downloader.py --user_id 9999 --start_date 2025-01-01 --end_date 2025-08-31
```

**Notes:**
- The script requires an internet connection and valid credentials for the Turnkey Coach API.
- The API base URL defaults to `https://app.turnkey.coach`, but can be overridden by the `API_BASE_URL` environment variable.
- If you encounter authentication errors, double-check your email and password.
- Errors and progress (such as successful downloads or failures) are printed to the console.

---

Let me know if you want this integrated into your README or need further details!

### Fetching the Exercise List with `fetch_exercises.py`

**Command-Line Usage:**
1. Ensure you are in the directory containing `fetch_exercises.py`.
2. Run the script from the command line:
   ```bash
   python fetch_exercises.py
   ```
3. You will be prompted to enter your email and password for the Turnkey Coach API.
   - The script authenticates your credentials.
   - If authentication succeeds, it fetches the list of exercises and saves it as `exerciselist.json` in the same directory.
4. **Tip:** If you need to run the script again, you can overwrite or update `exerciselist.json` as needed. Cached tokens are stored in `.tokencache` and reused for 1 hour to avoid repeated logins.

### Parsing Workouts with `workout_parser.py`

**Command-Line Usage:**
1. Make sure `workout_parser.py`, `exerciselist.json`, and your input file (e.g., `john.txt`) are in the same directory.
2. Run the script from the command line:
   ```bash
   python workout_parser.py
   ```
3. The script will prompt you for:
   - **Client User ID** (integer, e.g., `9999`):  
     To find the client user ID, go to the calendar page for the client in the Turnkey Coach web app.  
     The user ID appears in the URL, for example:  
     ```
     https://app.turnkey.coach/calendar?id=9999#current_view=month
     ```
     The number after `id=` is the client user ID you should enter when prompted.
   - **Input file path** (e.g., `john.txt`). Include the relative or absolute path if the file is not in the current directory.
4. During parsing:
   - For any exercise name not recognized, you will be prompted to:
     - Select a suggested match (fuzzy matching).
     - Enter a different exercise name (must match one from `exerciselist.json`).
     - Skip the exercise (sets `exercise_id` to `null`).
5. When parsing is complete, a JSON file (same base name as your input file, e.g., `john.json`) is created in the same directory.
6. **Tip:** If you see errors about missing files or unrecognized exercises, check that paths are correct and `exerciselist.json` is up to date.

### Uploading Workouts with `workout_uploader.py`

**Command-Line Usage:**
1. Ensure the JSON file you want to upload (e.g., `john.json`) is in the same directory as `workout_uploader.py`.
2. Run the script from the command line:
   ```bash
   python workout_uploader.py
   ```
3. You will be prompted to enter:
   - Your email and password for Turnkey Coach API authentication.
   - The path to the JSON file you wish to upload (e.g., `john.json`). You can enter `q` to quit.
4. The script authenticates, caches the token in `.tokencache`, and uploads each workout from the JSON file.
5. **Tip:** If you receive authentication errors, double-check your credentials. If you get API errors, review the API response and ensure your JSON file matches the expected format.

### Example Workflow
1. Create `john.txt`:


```
Workout Date: 2025-08-20

Deadlift
1x5 @ 360
Bench Press
1x5 @ 227.5
2x5 @ 192.5
 
---
Workout Date: 2025-08-27

Squat
1x5 @ RM
  Work up to a heavy single.
Press
1x5 @ 170
2x5 @ 145
1xAMRAP @ 135
```


2. Run `fetch_exercises.py` to generate `exerciselist.json`.
3. Run `workout_parser.py` to generate `john.json`.
4. Run `workout_uploader.py` to upload `john.json` to the API.

#### Alternate workflow.
1. Download client workouts using `workout_downloader.py`.
2. Convert JSON workouts to plain text format with `json2markup.py`.
3. Read the `.txt` file or upload it to LLM for analysis.
4. Use `pr_analyzer.py` to check the best efforts of a lifter over a period of time.
5. Use `pr_downwloader.py` to keep client PRs accessible in a console window while working.


## Input File Format (for `workout_parser.py`)

The input file uses a markdown-like structure with tab-indented notes.

### Structure
- **Workout Date**: Begins with `Workout Date:` followed by `YYYY-MM-DD`.
- **Exercises**: Non-indented lines matching names in `exerciselist.json`.
- **Sets**: Non-indented in the format `3x5@300` or `3xAMRAP@300`.
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
- **Workout Date**: `Workout Date: YYYY-MM-DD`
- **Exercises**: Non-indented, must match `exerciselist.json` (case-insensitive) or be resolved via prompts.
- **Sets**:
  - **Weight-based**: `setsxreps @ weight`
  - **RPE-based**: `setsxreps @ RPE value`
  - **AMRAP**: `setsxAMRAP @ weight`
  - **Distance-based**: `distance unit @ HH:MM:SS`
  - **Text-based**: `setsxreps @ description`
- **Notes**: Tab-indented (e.g., `    Work up to a heavy single.`).

### Notes on Indentation
- Use **tabs** (preferred) or **spaces** for notes (detected via regex `^\s+`).
- Exercises and sets must be non-indented or minimally indented.
- Consistent indentation (e.g., one tab per note) is recommended.

## Output JSON Format (from `workout_parser.py`)

The output JSON aligns with the `POST /api/v1/workouts` endpoint (see [API Documentation](https://app.turnkey.coach/api-docs/index.html)):

- **Top-level**: Array of workout objects.
- **Workout object**:
  - `user_id`: Integer (e.g., `9999`).
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
```json
[
  {
    "user_id": 9999,
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
    "user_id": 9999,
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
```json
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
requests==2.32.3
rapidfuzz==3.14.0
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

- **Exercise IDs**: Ensure `exerciselist.json` matches the API’s exercise IDs (e.g., 794 for `Squat`, 1007 for `Bench Press`). See the [API Documentation](https://app.turnkey.coach/api-docs/index.html).
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

