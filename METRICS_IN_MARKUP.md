# Programming Metrics in Workout Files

## Overview

Metrics (body weight, body fat percentage, measurements, recovery scores, etc.) can be included directly in your workout markup files and will be uploaded to the Turnkey Coach platform automatically when you use the **Upload Workout from File** feature.

## Syntax

Metrics use the `@` symbol followed by the metric type and a colon. Values, units, and notes are optional so you can program either a fully-populated datapoint or a placeholder the client will fill in later:

```
@metric_type: [value] [unit] [optional notes]
```

> **Note:** Metric names map to definitions that already exist in your Turnkey Coach metric catalog (e.g., `@duration:` matches the **Duration** metric). If you introduce a new metric name, create the matching definition in the platform first so uploads can attach it to the workout.

### Examples

```
@weight: 185.5 lbs
@body_fat: 15.2%
@sleep: 7.5 hours feeling well-rested
@waist: 34 inches
@stress: 6 1-10 work deadline this week
@recovery: 8 1-10
@duration:
@fatigue: report in app
```

## Placement in Workout Files

Metrics appear after the workout title (if present) and before the exercises. They are associated with the workout date of the block they appear in.

### Complete Example

```
Workout Date: 2025-10-11
Heavy Squat Day

@weight: 185.5 lbs
@sleep: 7.5 hours
@recovery: 8 1-10

Squat
5x5 @ 315
	Focus on depth and bar speed

Bench Press
3x8 @ 225

---

Workout Date: 2025-10-12
Active Recovery

@weight: 185.0 lbs
@stress: 3 1-10
@energy: 9 1-10

Walk
1x30:00

---
```

## Common Metric Types

| Metric Type | Unit Options | Description |
|------------|--------------|-------------|
| `weight` | lbs, kg | Body weight |
| `body_fat` | % | Body fat percentage |
| `waist`, `chest`, `arms`, `thighs` | inches, cm | Body measurements |
| `sleep` | hours | Sleep duration |
| `stress`, `recovery`, `energy` | 1-10 | Subjective scales |
| Custom types | any | e.g., `resting_hr`, `hrv`, `vertical_jump` |

## Workflow

1. **Create or edit a workout file** in your client's directory
2. **Add metrics** using the `@metric_type: value unit notes` format
3. **Use the Upload Program feature** (menu option 5) from the CLI
4. **Select your workout file**
5. Both workouts and metrics are uploaded automatically

When the file is parsed, you'll see confirmation messages:
```
[cyan]Found metric:[/cyan] weight = 185.5 lbs
[cyan]Found metric:[/cyan] sleep = 7.5 hours
[cyan]Found metric:[/cyan] recovery = 8 1-10
[cyan]Found metric placeholder:[/cyan] duration
[cyan]Found metric placeholder:[/cyan] fatigue (notes: report in app)
```

## Viewing Metrics

### Option 1: Browse & Save Workout History (Menu Option 4)

When you use the "Browse & Save Workout History" feature, the generated markup file will include all metrics that were previously uploaded for each workout date.

### Option 2: Program Metrics Tool (Menu Option 7)

The standalone Metrics Tool (menu option 7) provides:
- **View Client Metrics**: View historical metrics with date range filtering
- **Program Single Metric**: Manually add individual metrics
- **Program Bulk Metrics**: Add multiple metrics via comma-separated format

This tool is useful for viewing existing metrics or adding metrics outside of workout programming.

## Best Practices

### 1. Consistent Timing
Record metrics at the same time each day:
- **Body weight**: Morning, fasted
- **Body fat %**: Same time as weight
- **Sleep/Recovery**: Upon waking
- **Measurements**: Weekly, same day/time

### 2. Use Notes for Context
```
@weight: 188.2 lbs post-cheat day
@sleep: 5.5 hours poor quality - woke up multiple times
@stress: 8 1-10 work deadline pressure
```

### 3. Program Multiple Days at Once
Create a week's worth of workouts with daily metrics:

```
Workout Date: 2025-10-07
@weight: 185.5 lbs
Squat
5x5 @ 315
---

Workout Date: 2025-10-08
@weight: 185.3 lbs
Deadlift
3x5 @ 405
---

Workout Date: 2025-10-09
@weight: 185.5 lbs
Press
5x5 @ 155
---
```

### 4. Consistent Custom Metric Names
- **Good**: `resting_hr`, `vertical_jump`, `hrv`
- **Avoid**: `hr`, `jump`, `heart`

### 5. Placeholder Assignments
- Leave the value blank (e.g., `@motivation:`) when you want the client to submit the metric later.
- Add optional instructions as notes: `@duration: log total workout minutes`.
- Placeholder metrics are uploaded alongside workouts so the assignment appears in the client's app even without an initial value.

## Integration with Existing Workflow

The metrics feature integrates seamlessly with your existing workflow:

1. **Writing Programs**: Include metrics when programming workouts
2. **Uploading**: Metrics upload automatically with workouts
3. **Browsing History**: Downloaded workouts include their metrics
4. **Editing Programs**: Metrics are preserved in the markup format

## Technical Details

### File Format
See `markup.md` for complete markup language specification including metrics syntax.

### Parser Implementation
- Located in `upload_tool.py`
- Function: `parse_line_as_metric()` (lines 13-69)
- Supports regex pattern matching for flexible input
- Validates numeric values
- Associates metrics with workout dates

### API Integration
- Endpoint: `POST /api/v1/metrics`
- Uploads occur after workouts are uploaded
- Each metric is uploaded individually with full metadata

### Example Test File
See `tests/fixtures/metrics_example.txt` for a complete example file with multiple workouts and metrics.

## Troubleshooting

### Metric Not Parsed

**Problem**: Metric line doesn't appear in upload confirmation

**Solutions**:
- Ensure line starts with `@`
- Include colon after metric type: `@weight:` not `@weight`
- Provide a numeric value when submitting data, or leave it blank intentionally to create a placeholder
- Add unit immediately after numeric values when provided: `@weight: 185.5 lbs`

### Upload Failed

**Problem**: "Upload failed" error for metrics

**Solutions**:
1. Check network connectivity
2. Verify authentication token is valid
3. Check API response in error message for details
4. Ensure date format is YYYY-MM-DD
5. Verify value is numeric
6. Confirm the metric name exists in the platform catalog (e.g., create a **Duration** metric before using `@duration:`)

### Metric Not Showing in History

**Problem**: Uploaded metric doesn't appear when browsing history

**Solutions**:
1. Force refresh workout history (menu option 'r')
2. Check that metric was successfully uploaded (look for ✅ confirmation)
3. Verify date matches workout date

## Support

For issues or questions:
1. Check this guide for common solutions
2. Review the complete markup specification in `markup.md`
3. See `METRICS_GUIDE.md` for standalone metrics tool documentation
4. Check the DevGuides for architectural details

---

**Happy metric tracking!**
