# Understanding JSON Workout Completion Logic

## Purpose

This guide explains how to interpret the Turnkey Coach JSON API data to determine whether exercises were actually completed or skipped. This is critical for:

1. Converting JSON workout data to markup format
2. Calculating accurate estimated 1RM values
3. Feeding proper workout history context to LLMs for workout design

## The Challenge

The JSON API structure is designed for real-time athlete tracking, not historical analysis. This creates ambiguity when determining what was actually performed vs. what was prescribed. The markup language's `(skipped)` notation solves this by making completion status explicit and unambiguous.

## JSON Data Structure

Each workout contains:

```json
{
  "workout_date": "2025-09-01",
  "completed": true,  // Did athlete mark workout complete?
  "assigned_exercises": [
    {
      "exercise": {"name": "Squat"},
      "missed": false,  // Explicitly marked as skipped?
      "assigned_sets": [
        {
          "display_label": "3 x 5 @ 225 lbs",
          "actual_sets": [  // What was actually performed
            {"sets": "1", "reps": "5", "weight": "225.0"}
          ]
        }
      ]
    }
  ]
}
```

## The Three Key Fields

### 1. `workout.completed` (boolean)
- **What it means**: Whether the athlete clicked "Mark Complete" in the app
- **What it DOESN'T mean**: That all prescribed exercises were done
- **Ambiguity**: Athletes sometimes mark workouts complete even if they skipped exercises, or forget to mark complete even if they did everything

### 2. `exercise.missed` (boolean)
- **What it means**: The exercise was explicitly marked as skipped
- **Reliability**: When `true`, this is definitive - the exercise was not performed
- **Limitation**: Not all skipped exercises get explicitly marked

### 3. `actual_sets` (array)
- **What it means**: Actual performance data logged by the athlete
- **When present**: This is the ground truth of what was performed
- **When empty `[]`**: Ambiguous - could mean "skipped" OR "completed as prescribed but not logged"

## The Bulletproof Completion Logic

To resolve the ambiguity, we use a **priority-based decision tree**:

### Priority 1: Check `exercise.missed`
```python
if exercise.get('missed', False):
    # Exercise was explicitly skipped
    return SKIPPED
```

**Interpretation**: If `missed == true`, the exercise was definitively not performed, regardless of any other fields.

### Priority 2: Check `actual_sets` exists
```python
elif has_actual_sets_data:
    # Use the actual performance data
    return USE_ACTUAL_DATA
```

**Interpretation**: If `actual_sets` contains data, this takes precedence over everything else (including the `completed` flag). This handles cases where athletes do work but forget to mark the workout complete.

### Priority 3: Check `workout.completed == false`
```python
elif not workout.get('completed', False):
    # Workout not completed, no actual data = skipped
    return SKIPPED
```

**Interpretation**: If the workout wasn't marked complete AND there's no actual performance data, the exercise was skipped.

### Priority 4: Default case
```python
else:
    # workout.completed == true, no actual_sets, not missed
    return COMPLETED_AS_PRESCRIBED
```

**Interpretation**: If the workout was marked complete, there's no actual data logged, and it wasn't explicitly missed, we assume it was completed as prescribed.

## Example Scenarios

### Scenario 1: Explicitly Skipped Exercise
```json
{
  "completed": true,
  "assigned_exercises": [{
    "exercise": {"name": "Kettlebell Swing"},
    "missed": true,
    "assigned_sets": [{"display_label": "5 x 10 @ 70 lbs"}]
  }]
}
```
**Result**: `(skipped)` - Priority 1 applies

**Markup output**:
```
Kettlebell Swing
5 x 10 @ 70 lbs
(skipped)
```

### Scenario 2: Completed with Actual Data
```json
{
  "completed": true,
  "assigned_exercises": [{
    "exercise": {"name": "Squat"},
    "missed": false,
    "assigned_sets": [{
      "display_label": "3 x 5 @ 225 lbs",
      "actual_sets": [
        {"sets": "1", "reps": "5", "weight": "227.5"}
      ]
    }]
  }]
}
```
**Result**: Show actual data - Priority 2 applies

**Markup output**:
```
Squat
3 x 5 @ 225 lbs
(1x5 @ 227.5)
```

### Scenario 3: Work Done, But Not Marked Complete
```json
{
  "completed": false,
  "assigned_exercises": [{
    "exercise": {"name": "Bench Press"},
    "missed": false,
    "assigned_sets": [{
      "display_label": "3 x 5 @ 200 lbs",
      "actual_sets": [
        {"sets": "3", "reps": "5", "weight": "200.0"}
      ]
    }]
  }]
}
```
**Result**: Show actual data - Priority 2 applies (takes precedence over completed flag)

**Markup output**:
```
Bench Press
3 x 5 @ 200 lbs
(3x5 @ 200.0)
```

### Scenario 4: Skipped Workout (Not Marked Complete)
```json
{
  "completed": false,
  "assigned_exercises": [{
    "exercise": {"name": "Deadlift"},
    "missed": false,
    "assigned_sets": [{
      "display_label": "1 x 5 @ 350 lbs",
      "actual_sets": []
    }]
  }]
}
```
**Result**: `(skipped)` - Priority 3 applies

**Markup output**:
```
Deadlift
1 x 5 @ 350 lbs
(skipped)
```

### Scenario 5: Completed as Prescribed (No Logging)
```json
{
  "completed": true,
  "assigned_exercises": [{
    "exercise": {"name": "Press"},
    "missed": false,
    "assigned_sets": [{
      "display_label": "5 x 5 @ 115 lbs",
      "actual_sets": []
    }]
  }]
}
```
**Result**: Completed as prescribed - Priority 4 applies

**Markup output**:
```
Press
5 x 5 @ 115 lbs
```

## Implications for 1RM Calculations

When calculating estimated 1RM values, we can **only use exercises with actual performance data**. This means:

- ✅ Use Priority 2 cases (has `actual_sets`)
- ❌ Skip Priority 1 cases (`missed == true`)
- ❌ Skip Priority 3 cases (`completed == false`, no data)
- ❌ Skip Priority 4 cases (completed as prescribed, but no actual data to calculate from)

**Important**: We cannot assume prescribed sets for 1RM calculations. If an athlete was prescribed "3 x 5 @ 225 lbs" and completed it without logging, we have no way to know if they actually used 225 lbs or adjusted the weight.

## Why Markup is Simpler for LLMs

The markup format with `(skipped)` notation eliminates all ambiguity:

### JSON (ambiguous):
```json
{
  "completed": true,
  "assigned_exercises": [{
    "exercise": {"name": "Squat"},
    "assigned_sets": [{"display_label": "3 x 5 @ 225 lbs", "actual_sets": []}]
  }]
}
```
**Question**: Was this completed or skipped? You need to check multiple fields and apply logic.

### Markup (unambiguous):
```
Squat
3 x 5 @ 225 lbs
```
**Interpretation**: Completed as prescribed (no parenthetical notation).

```
Squat
3 x 5 @ 225 lbs
(skipped)
```
**Interpretation**: Not performed.

```
Squat
3 x 5 @ 225 lbs
(1x5 @ 227.5)
```
**Interpretation**: Performed with actual data logged.

## Code Implementation

### In `format_tool.py` (lines 172-278)

The formatter converts JSON to markup using the bulletproof logic:

```python
# Priority 1: Explicitly marked as missed
if exercise.get('missed', False):
    output_lines.append(prescribed_sets)
    output_lines.append("(skipped)")

# Priority 2: Has actual_sets data
elif has_any_actual_sets:
    output_lines.append(prescribed_sets)
    output_lines.append(actual_performance_data)

# Priority 3: Workout not completed
elif not workout.get('completed', False):
    output_lines.append(prescribed_sets)
    output_lines.append("(skipped)")

# Priority 4: Completed as prescribed
else:
    output_lines.append(prescribed_sets)
    # No parenthetical notation
```

### In `pr_tool.py` (lines 53-96)

The PR calculator only uses actual performance data:

```python
# Skip if missed
if exercise.get('missed', False):
    continue

# Skip if no actual_sets
if not has_any_actual_sets:
    continue

# Only calculate from actual performance data
for actual_set in actual_sets:
    estimated_1rm = wendler_1rm(actual_set['weight'], actual_set['reps'])
```

## Teaching an LLM

When providing workout history to an LLM for workout design, use the **markup format**, not the JSON. The LLM instructions should include:

> **Completion Status Rules:**
> - If an exercise has no parenthetical notation in workout history, it was completed as prescribed
> - `(skipped)` means the exercise was not performed
> - `(3x5 @ 225)` means the exercise was performed with actual data shown in parentheses

This simple rule set eliminates the need for the LLM to understand the complex JSON logic.

## Summary

The JSON API's `actual_sets` field is arcane because it serves two purposes:
1. **When populated**: Ground truth of actual performance
2. **When empty**: Ambiguous - requires checking `completed` and `missed` flags to interpret

The bulletproof completion logic resolves this ambiguity using a priority system, and the markup language makes the resolved interpretation explicit and simple for both humans and LLMs to understand.
