# PR Analysis Tools

## Purpose
This guide covers the two PR (Personal Record) analysis tools: the estimated 1RM analyzer (pr_tool.py) and the actual PR viewer (actual_prs_tool.py). Both tools help coaches track client strength progress.

## Overview

The system provides two complementary approaches to PR analysis:

1. **Estimated PRs** (`pr_tool.py`): Calculates estimated 1RMs from workout history
2. **Actual PRs** (`actual_prs_tool.py`): Displays official PRs stored in the platform database

## Estimated PR Analyzer

**File**: `pr_tool.py` (238 lines)

### Purpose

Calculate estimated one-rep maxes from actual workout performance data using the Wendler formula. This tool is useful for:
- Tracking progress over time
- Identifying PRs from multi-rep sets
- Calculating powerlifting totals and Wilks scores
- Analyzing performance across custom date ranges

### Main Function

**Function**: `run_pr_analyzer(token, client)`
**Location**: pr_tool.py:113-237

**Flow**:
```
Load workout history
    ↓
Select date range (3m/6m/year/all/custom)
    ↓
Process workouts → find best e1RMs per exercise
    ↓
Display main lifts (Squat/Bench/Deadlift/Press)
    ↓
Options:
    - [n] New date range
    - [m] Show more lifts
    - [w] Calculate Wilks score
    - [q] Quit
```

### Wendler Formula

**Function**: `wendler_1rm(weight, reps)`
**Location**: pr_tool.py:16-20

**Formula**: `e1RM = (weight × reps × 0.0333) + weight`

**Implementation**:
```python
def wendler_1rm(weight, reps):
    """Calculates estimated 1RM using the Wendler formula."""
    if not isinstance(reps, (int, float)) or reps <= 1:
        return weight  # For 1RM, return weight directly
    return (weight * reps * 0.0333) + weight
```

**Examples**:
- 405 lbs × 1 rep = 405 lbs (no calculation needed)
- 385 lbs × 5 reps = (385 × 5 × 0.0333) + 385 = 449.1 lbs
- 315 lbs × 10 reps = (315 × 10 × 0.0333) + 315 = 419.9 lbs

### Workout History Processing

**Function**: `process_workout_history(workouts, start_date=None, end_date=None)`
**Location**: pr_tool.py:40-86

**Purpose**: Find the best estimated 1RM for every exercise within a date range.

**Algorithm**:
```python
def process_workout_history(workouts, start_date=None, end_date=None):
    best_performances = {}

    for workout in workouts:
        workout_date = datetime.strptime(workout["workout_date"], "%Y-%m-%d").date()

        # Filter by date range
        if (start_date and workout_date < start_date) or (end_date and workout_date > end_date):
            continue

        is_completed = workout.get("completed", False)

        for exercise in workout.get("assigned_exercises", []):
            lift_name = exercise.get("exercise", {}).get("name", "Unknown").lower()
            assigned_sets = exercise.get("assigned_sets", [])

            for assigned_set in assigned_sets:
                actual_sets = assigned_set.get("actual_sets", [])

                if actual_sets:
                    # Use actual performance data
                    for actual_set in actual_sets:
                        weight = float(actual_set.get("weight", 0) or 0)
                        reps = actual_set.get("reps")
                        if not reps or not weight:
                            continue

                        estimated_1rm = wendler_1rm(weight, reps)

                        # Keep track of best e1RM for this exercise
                        if lift_name not in best_performances or estimated_1rm > best_performances[lift_name]['e1rm']:
                            best_performances[lift_name] = {
                                'e1rm': estimated_1rm,
                                'weight': weight,
                                'reps': reps,
                                'unit': workout.get("weight_type", "lbs"),
                                'date': workout.get("workout_date")
                            }

                elif is_completed:
                    # Fallback: Use assigned weights if workout completed but no actual_sets recorded
                    weight = float(assigned_set.get("weight", 0) or 0)
                    reps = assigned_set.get("reps")
                    if not reps or not weight:
                        continue

                    estimated_1rm = wendler_1rm(weight, reps)

                    if lift_name not in best_performances or estimated_1rm > best_performances[lift_name]['e1rm']:
                        best_performances[lift_name] = {
                            'e1rm': estimated_1rm,
                            'weight': weight,
                            'reps': reps,
                            'unit': workout.get("weight_type", "lbs"),
                            'date': workout.get("workout_date")
                        }

    return best_performances
```

**Key Features**:
1. **Actual vs Assigned Sets**: Prioritizes `actual_sets` (recorded performance), falls back to `assigned_sets` if workout marked complete
2. **Best Performance Tracking**: Keeps only the highest e1RM for each exercise
3. **Date Filtering**: Supports custom date ranges for progress tracking
4. **Unit Preservation**: Stores weight unit (lbs/kg) from workout data

### Main Lifts Configuration

**Location**: pr_tool.py:10

```python
MAIN_LIFTS = ["squat", "bench press", "deadlift", "press"]
```

These lifts are:
- Displayed prominently in the main view
- Used for Wilks score calculation (minus press)
- Separated from "other lifts" for clarity

### Display Function

**Function**: `display_prs(main_lifts, other_lifts, date_range_str, show_other=False)`
**Location**: pr_tool.py:88-111

**Output Format**:
```
--- Best Lift Performances ---
---  Date Range: Last 6 Months  ---

--- Main Lifts ---
Squat            449.1 lbs on 2025-09-15 (from 385 lbs x 5)
Bench Press      330.2 lbs on 2025-09-20 (from 285 lbs x 6)
Deadlift         518.3 lbs on 2025-09-10 (from 455 lbs x 4)
Press            No performance found

--- Other Lifts ---  (if show_other=True)
Front Squat                   325.0 lbs on 2025-08-01 (from 325 lbs x 1)
Romanian Deadlift             380.2 lbs on 2025-09-05 (from 335 lbs x 5)
...
```

**Styling**:
- Lift names: Left-aligned, 15 chars wide
- e1RM values: Bold green
- Date and source data: Dimmed text
- Missing lifts: Dimmed "No performance found"

### Wilks Score Calculation

**Function**: `calculate_wilks(total_kg, bodyweight_kg, gender)`
**Location**: pr_tool.py:22-37

**Purpose**: Calculate Wilks coefficient for powerlifting total comparison across bodyweights.

**Formula**:
```
Wilks = Total (kg) × (500 / denominator)

Where denominator = a + (b×BW) + (c×BW²) + (d×BW³) + (e×BW⁴) + (f×BW⁵)
```

**Coefficients**:
```python
# Male coefficients
if gender.lower() == 'male':
    a, b, c, d, e, f = (
        -216.0475144,
        16.2606339,
        -0.002388645,
        -0.00113732,
        7.01863E-06,
        -1.291E-08
    )

# Female coefficients
elif gender.lower() == 'female':
    a, b, c, d, e, f = (
        594.31747775582,
        -27.23842536447,
        0.82112226871,
        -0.00930733913,
        4.731582E-05,
        -9.054E-08
    )
```

**User Flow** (pr_tool.py:190-234):
```
User presses 'w' (Wilks score)
    ↓
Validate all 3 lifts have PRs (squat/bench/deadlift)
    ↓
[Missing lift] → Error message, return
    ↓
[Gender not cached] → Prompt for gender (m/f)
    ↓
Prompt for bodyweight (e.g., "180 lbs" or "82 kg")
    ↓
Parse bodyweight, detect unit
    ↓
Convert total to kg (if needed)
    ↓
Calculate Wilks score
    ↓
Display:
    - Bodyweight (lbs and kg)
    - e1RM Total (lbs and kg)
    - Gender
    - Estimated Wilks score
```

**Example Output**:
```
--- Estimated Wilks Score ---
Bodyweight:      180.0 lbs (81.6 kg)
e1RM Total:      1297.6 lbs (588.5 kg)
Client Gender:   Male
Estimated Wilks: 423.15
```

### Date Range Options

**Implementation** (pr_tool.py:126-164):

| Option | Description | Calculation |
|--------|-------------|-------------|
| `a` | All Time | No date filters |
| `3` | Last 3 Months | `today - 90 days` |
| `6` | Last 6 Months | `today - 180 days` |
| `y` | Last Year | `today - 365 days` |
| `c` | Custom Range | User inputs start and end dates (YYYY-MM-DD) |

**Custom Range Input**:
```python
try:
    start_str = console.input("Enter start date (YYYY-MM-DD): ")
    end_str = console.input("Enter end date   (YYYY-MM-DD): ")
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    date_range_str = f"Custom ({start_date} to {end_date})"
except ValueError:
    console.input("\n[red]Invalid date format. Press Enter to try again.[/red]")
```

## Actual PR Viewer

**File**: `actual_prs_tool.py` (145 lines)

### Purpose

Display official PRs stored in the Turnkey Coach platform. These are PRs manually recorded by coaches or automatically tracked by the platform.

### Main Function

**Function**: `run_actual_prs_viewer(token, client)`
**Location**: actual_prs_tool.py:88-145

**Flow**:
```
Fetch PRs from API
    ↓
Process PRs → find best PR per exercise
    ↓
Display main lifts
    ↓
Options:
    - [a] All time
    - [3] Last 3 months
    - [6] Last 6 months
    - [y] Last year
    - [m] Show more PRs (other lifts)
    - [q] Quit
```

### API Integration

**Function**: `get_client_prs(token, client_id, start_date=None, end_date=None)`
**Location**: actual_prs_tool.py:23-40

**API Endpoint**: `GET /api/v1/prs?user_id={id}&start_date={date}&end_date={date}`

**Implementation**:
```python
def get_client_prs(token, client_id, start_date=None, end_date=None):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": client_id}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    url = f"{API_BASE_URL}/api/v1/prs"
    with console.status("Fetching PRs from API..."):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            console.print(f"\n[bold red]Could not fetch PRs for client {client_id}: {err}[/bold red]")
            return []
```

**Response Structure**:
```json
[
  {
    "exercise": {"id": 1, "name": "Squat"},
    "weight": 405,
    "reps": 1,
    "date": "2025-10-01",
    "weight_type": "lbs"
  },
  {
    "exercise": {"id": 1, "name": "Squat"},
    "weight": 385,
    "reps": 5,
    "date": "2025-09-15",
    "weight_type": "lbs"
  },
  ...
]
```

### PR Processing

**Function**: `process_prs(all_prs)`
**Location**: actual_prs_tool.py:42-62

**Purpose**: For each exercise, find the single best PR (prioritize actual 1RM over estimated).

**Algorithm**:
```python
def process_prs(all_prs):
    best_lifts = {}
    prs_by_exercise = {}

    # Group PRs by exercise
    for pr in all_prs:
        lift_name = pr.get("exercise", {}).get("name", "Unknown").lower()
        if lift_name not in prs_by_exercise:
            prs_by_exercise[lift_name] = []
        prs_by_exercise[lift_name].append(pr)

    # Find best PR for each exercise
    for lift_name, pr_list in prs_by_exercise.items():
        # Prefer actual 1-rep maxes
        actual_1rms = [p for p in pr_list if p.get("reps") == 1]

        if actual_1rms:
            # Best actual 1RM
            best_pr_for_lift = max(actual_1rms, key=lambda p: float(p.get("weight", 0) or 0))
        else:
            # Best estimated 1RM (using Wendler formula)
            best_pr_for_lift = max(
                pr_list,
                key=lambda p: wendler_1rm(float(p.get("weight", 0) or 0), p.get("reps"))
            )

        best_lifts[lift_name] = best_pr_for_lift

    return best_lifts
```

**Priority Logic**:
1. **Actual 1RM** (reps=1): Use highest weight directly
2. **Estimated 1RM** (reps>1): Calculate e1RM, use highest

### Display Function

**Function**: `display_prs(client_name, best_lifts, date_range_str)`
**Location**: actual_prs_tool.py:64-86

**Output Format**:
```
--- Official Personal Records for John Doe ---
---      Date Range: Last 6 Months      ---

Squat            405.0 lbs on 2025-10-01
Bench Press      303.3 lbs on 2025-09-20 (estimated from 285 lbs x 3)
Deadlift         495.0 lbs on 2025-09-10
Press            No PR found
```

**Styling Difference from Estimated PRs**:
- Actual 1RMs: Bold green (official PR)
- Estimated 1RMs: Bold yellow (calculated from multi-rep)

### More PRs Display

**Implementation** (actual_prs_tool.py:127-144):

When user presses 'm', display all other lifts (non-main):

```
--- Other Lifts ---
Front Squat                   325.0 lbs on 2025-08-01
Romanian Deadlift             335.0 lbs on 2025-09-05 (estimated from 335 lbs x 5)
Overhead Press                155.0 lbs on 2025-09-12
...
```

## Comparison: Estimated vs Actual PRs

| Feature | Estimated PRs (pr_tool.py) | Actual PRs (actual_prs_tool.py) |
|---------|----------------------------|----------------------------------|
| **Data Source** | Workout history cache | API endpoint `/api/v1/prs` |
| **Calculation** | Always uses Wendler formula | Uses actual 1RM if available |
| **Exercise Coverage** | All exercises in workout history | Only exercises with recorded PRs |
| **Wilks Score** | ✓ Supported | ✗ Not supported |
| **Offline Access** | ✓ Uses cache | ✗ Requires API |
| **Data Freshness** | Depends on workout cache | Always current from API |
| **Use Case** | Historical analysis, progress tracking | Official records, competition prep |

## Use Cases

### Estimated PR Tool
**Best for**:
- Analyzing progress over time
- Finding PRs from training logs (not just official tests)
- Calculating powerlifting totals and Wilks scores
- Comparing performance across custom date ranges

**Example Workflow**:
```
Coach wants to see if athlete has improved in last 3 months:
1. Select "Last 3 Months" date range
2. View main lift e1RMs
3. Compare to previous 3-month period
4. Calculate Wilks score for meet prep
```

### Actual PR Tool
**Best for**:
- Viewing official PRs recorded in platform
- Quick reference for competition planning
- Checking platform-validated records
- Coaches who manually log PR attempts

**Example Workflow**:
```
Coach wants to verify athlete's competition PRs:
1. Select "All Time" to see best ever
2. Review actual 1RMs vs estimated
3. Check dates of PRs for recency
```

## Best Practices for Developers

### 1. Always Validate Workout Data
```python
weight = float(actual_set.get("weight", 0) or 0)
reps = actual_set.get("reps")
if not reps or not weight:
    continue  # Skip invalid data
```

### 2. Handle Missing Data Gracefully
```python
if lift_name not in best_performances:
    console.print(f"{lift_display_name:<15} [dim]No performance found[/dim]")
```

### 3. Use Wendler Formula Correctly
```python
# Don't calculate e1RM for 1-rep sets
if reps <= 1:
    return weight  # Already a 1RM
```

### 4. Preserve Units
```python
# Store unit with performance data
'unit': workout.get("weight_type", "lbs")
```

### 5. Date Range Validation
```python
try:
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
except ValueError:
    console.input("\n[red]Invalid date format. Press Enter to try again.[/red]")
    continue  # Return to menu, don't crash
```

## Troubleshooting

### No PRs Found
**Symptom**: "No performance found" for all lifts

**Solutions (Estimated PRs)**:
1. Check workout history has been downloaded
2. Verify workouts have `actual_sets` or are marked `completed`
3. Try "All Time" date range
4. Ensure exercise names match exactly

**Solutions (Actual PRs)**:
1. Verify PRs have been recorded in platform
2. Check API endpoint is accessible
3. Try broader date range
4. Confirm client has PRs in system

### Wilks Calculation Error
**Symptom**: "Cannot calculate Wilks. Missing performance..."

**Solutions**:
1. Ensure all 3 lifts (squat, bench, deadlift) have PRs in selected date range
2. Try broader date range (e.g., "All Time")
3. Check workout history is complete

### Units Incorrect
**Symptom**: PRs showing in wrong units (lbs vs kg)

**Solutions**:
1. Check `weight_type` field in workout data
2. Verify API is returning correct units
3. For Actual PRs, check platform PR records

## Extension Ideas

### Add New PR Formulas
Currently uses Wendler formula. Could add:
- Brzycki: `weight / (1.0278 - 0.0278 × reps)`
- Epley: `weight × (1 + reps/30)`
- Allow user to select formula in settings

### Track PR Progression Over Time
Generate charts showing e1RM trends:
```python
def get_pr_history(workouts, exercise_name):
    """Return list of (date, e1RM) tuples for graphing."""
    ...
```

### Comparison Tool
Compare two time periods:
```python
def compare_periods(workouts, period1_dates, period2_dates):
    """Show improvement between two date ranges."""
    ...
```

### Export PR Report
Generate formatted PR report for coaches:
```python
def export_pr_report(client, best_lifts, date_range):
    """Create PDF or markdown report of PRs."""
    ...
```

## Related Guides
- [01-Architecture-Overview.md](./01-Architecture-Overview.md)
- [02-API-Client-and-Authentication.md](./02-API-Client-and-Authentication.md)
- [05-Workout-Management.md](./05-Workout-Management.md)
