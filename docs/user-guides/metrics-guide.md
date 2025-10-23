# Metrics Tool User Guide

## Overview

The Metrics Tool allows coaches to program and track client metrics (body weight, body fat percentage, measurements, recovery scores, etc.) and upload them to the Turnkey Coach platform via API.

## Accessing the Metrics Tool

1. Launch the Turnkey Coach CLI: `python coach_cli.py`
2. Select your client
3. Choose option **7. Program Metrics** from the Client Tools menu

## Features

### 1. Program Single Metric

**Purpose**: Add a single metric entry for a client

**Workflow**:
1. Select "1. Program Single Metric" from the Metrics Tool menu
2. Choose metric type from the predefined list or create a custom type
3. Enter the date (or press Enter for today's date)
4. Enter the metric value
5. Optionally add notes
6. Confirm and upload

**Predefined Metric Types**:
- **Body Weight** (lbs or kg)
- **Body Fat %** (%)
- **Waist** (inches or cm)
- **Chest** (inches or cm)
- **Arms** (inches or cm)
- **Thighs** (inches or cm)
- **Sleep Hours** (hours)
- **Stress Level** (1-10 scale)
- **Recovery Score** (1-10 scale)
- **Energy Level** (1-10 scale)

**Custom Metrics**: You can also create custom metric types (e.g., "resting_hr" for resting heart rate)

**Example**:
```
Select metric type > 1
Enter date (YYYY-MM-DD) or press Enter for today: 2025-10-11
Enter value (lbs): 185.5
Enter notes (optional): Post-workout weigh-in

Confirm Metric Entry:
  Client: John Doe
  Date: 2025-10-11
  Metric: Body Weight
  Value: 185.5 lbs
  Notes: Post-workout weigh-in

Upload this metric? (y/n) > y
```

### 2. Program Bulk Metrics

**Purpose**: Add multiple metrics at once using a simple comma-separated format

**Workflow**:
1. Select "2. Program Bulk Metrics" from the Metrics Tool menu
2. Enter metrics line by line in the format:
   ```
   YYYY-MM-DD, metric_type, value, unit, notes (optional)
   ```
3. Type `done` when finished entering metrics
4. Review and confirm upload

**Format Explanation**:
- **Date**: YYYY-MM-DD format (e.g., 2025-10-11)
- **Metric Type**: Use predefined types (weight, body_fat, etc.) or custom names
- **Value**: Numeric value
- **Unit**: Unit of measurement (lbs, kg, %, inches, etc.)
- **Notes**: Optional notes (can be omitted)

**Example**:
```
Enter metrics (one per line). Type 'done' when finished:

[1] > 2025-10-11, weight, 185.5, lbs, morning weigh-in
✓ Added weight: 185.5 lbs on 2025-10-11

[2] > 2025-10-11, body_fat, 15.2, %, post-workout
✓ Added body_fat: 15.2 % on 2025-10-11

[3] > 2025-10-11, waist, 34, inches
✓ Added waist: 34 inches on 2025-10-11

[4] > 2025-10-11, sleep, 7.5, hours, good quality
✓ Added sleep: 7.5 hours on 2025-10-11

[5] > done

Ready to upload 4 metrics:
  2025-10-11: weight = 185.5 lbs
  2025-10-11: body_fat = 15.2 %
  2025-10-11: waist = 34 inches
  2025-10-11: sleep = 7.5 hours

Upload these metrics? (y/n) > y
```

### 3. View Client Metrics

**Purpose**: View historical metrics with filtering options

**Workflow**:
1. Select "3. View Client Metrics" from the Metrics Tool menu
2. Choose a date range:
   - Last 30 Days
   - Last 90 Days
   - Last Year
   - All Time
   - Custom Range
3. View metrics in a formatted table
4. Optionally filter by specific metric type

**Example Output**:
```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Metrics                           │
├────────────┬──────────────────────┬───────────────┬─────────────┤
│ Date       │ Metric               │ Value         │ Notes       │
├────────────┼──────────────────────┼───────────────┼─────────────┤
│ 2025-10-11 │ Body Weight          │ 185.5 lbs     │ morning...  │
│ 2025-10-11 │ Body Fat %           │ 15.2 %        │ post-wor... │
│ 2025-10-10 │ Body Weight          │ 186.0 lbs     │             │
│ 2025-10-09 │ Body Weight          │ 185.8 lbs     │ fasted      │
│ 2025-10-09 │ Sleep Hours          │ 7.5 hours     │ good qua... │
└────────────┴──────────────────────┴───────────────┴─────────────┘

Showing 5 of 25 total metrics
```

## Placeholder Metrics from Workout Files

- When you program workouts in markup, you can leave metrics blank (e.g., `@duration:`) to assign a placeholder for the client.
- The uploader now recognises these lines and pushes a metric entry without an initial value so the client can report back later.
- Placeholder metrics show up as **Pending** in the CLI table and still display any notes you include (e.g., `@fatigue: log after training`).
- Add complete values in the metrics tool when you have the data, or let the client submit their own entry in the app.

## Use Cases

### Daily Check-ins
Program multiple daily metrics in bulk:
```
2025-10-11, weight, 185.5, lbs
2025-10-11, sleep, 7.5, hours
2025-10-11, stress, 4, 1-10
2025-10-11, recovery, 8, 1-10
2025-10-11, energy, 7, 1-10
```

### Weekly Body Composition Tracking
Track body composition changes:
```
2025-10-11, weight, 185.5, lbs
2025-10-11, body_fat, 15.2, %
2025-10-11, waist, 34, inches
2025-10-11, chest, 42, inches
2025-10-11, arms, 15.5, inches
2025-10-11, thighs, 24, inches
```

### Custom Performance Metrics
Track custom metrics like heart rate variability, vertical jump, etc.:
```
2025-10-11, hrv, 65, ms, morning reading
2025-10-11, vertical_jump, 28, inches, post-warmup
2025-10-11, resting_hr, 58, bpm, upon waking
```

## API Endpoints Used

### GET /api/v1/metrics
**Purpose**: Fetch client metrics

**Parameters**:
- `user_id` (required): Client ID
- `start_date` (optional): Start date filter (YYYY-MM-DD)
- `end_date` (optional): End date filter (YYYY-MM-DD)

**Response**: Array of metric objects

### POST /api/v1/metrics
**Purpose**: Upload a metric assignment or placeholder

**Request Body**:
```json
{
  "user_id": 101,
  "metric_date": "2025-10-11",
  "name": "Body Weight",
  "metric_type": "decimal",
  "value": 185.5,
  "unit": "lbs",
  "notes": "Post-workout weigh-in"
}
```

**Required Fields**:
- `user_id`
- `metric_date`
- `name` (display label shown in the app)
- `metric_type` (data type: one of `integer`, `decimal`, `short_text`, `long_text`, or `scale`)

**Conditionally Required**:
- `value` is sent for populated metrics. Leave it out for placeholders so the client can complete the entry.

**Optional Fields**:
- `unit`
- `notes`
- `scale_start` / `scale_end` (only for `metric_type: "scale"`)

The CLI tools in this repo automatically translate markup tags (like `@weight:` or `@fatigue:`) into the correct `name` and `metric_type` values when uploading. If you introduce a new metric, create its definition once in the Turnkey Coach app so later uploads can reference it by name.

## Best Practices

### 1. Consistent Timing
Record metrics at the same time each day for accurate tracking:
- **Body weight**: First thing in the morning, fasted
- **Body fat %**: Same time as weight measurements
- **Sleep/Recovery**: Upon waking
- **Measurements**: Weekly at the same day/time

### 2. Use Notes Effectively
Add context to your metrics:
```
2025-10-11, weight, 188.2, lbs, post-cheat day
2025-10-11, sleep, 5.5, hours, poor quality - woke up multiple times
2025-10-11, stress, 8, 1-10, work deadline pressure
```

### 3. Batch Entry
Use bulk metrics for efficiency when programming multiple days or metrics:
```
# Program a week of weigh-ins at once
2025-10-05, weight, 186.0, lbs
2025-10-06, weight, 185.8, lbs
2025-10-07, weight, 185.5, lbs
2025-10-08, weight, 185.3, lbs
2025-10-09, weight, 185.5, lbs
2025-10-10, weight, 185.7, lbs
2025-10-11, weight, 185.5, lbs
```

### 4. Custom Metric Naming
Use clear, consistent names for custom metrics:
- **Good**: `resting_hr`, `vertical_jump`, `hrv`
- **Avoid**: `hr`, `jump`, `heart`

## Troubleshooting

### Metric Upload Fails

**Symptom**: "Upload failed" error message

**Solutions**:
1. Check API response text for specific error
2. Verify date format is YYYY-MM-DD
3. Ensure value is numeric when submitting via this tool (placeholder metrics are only created through the workout-markup uploader)
4. Check token hasn't expired (re-login if needed)
5. Verify API endpoint accessibility

### Invalid Date Format

**Symptom**: "Invalid date format" error

**Solutions**:
- Use YYYY-MM-DD format (e.g., 2025-10-11)
- Pad single-digit months/days with zeros (10-01, not 10-1)
- Don't use slashes or other separators

### Bulk Entry Parse Errors

**Symptom**: "Error on line X" message

**Solutions**:
1. Ensure correct format: `date, type, value, unit, notes`
2. Use commas as separators (not tabs or spaces)
3. Ensure value is a number
4. Include at least 4 fields (date, type, value, unit)

## Technical Details

### File Location
`metrics_tool.py` (385 lines)

### Dependencies
- `requests` - API communication
- `rich` - Console UI formatting
- `api_client` - Authentication and shared utilities
- `directory_migration` - File system management
- `encoding_utils` - UTF-8 file handling

### Data Storage
- Metrics are uploaded directly to API
- No local caching (always fetches fresh from API)
- Consider adding local cache in future versions

### Integration Points
- Imported in `coach_cli.py` line 24
- Menu option 7 in `show_tool_menu()` (line 225-226)
- Uses standard authentication via `api_client.py`

## Future Enhancements

### Potential Features
1. **Metric Templates**: Save common metric sets for quick entry
2. **CSV Import**: Import metrics from spreadsheets
3. **Trend Analysis**: Calculate trends and display graphs
4. **Goal Tracking**: Set targets and track progress
5. **Local Caching**: Cache metrics for offline viewing
6. **Metric Deletion**: Delete or edit existing metrics
7. **Export**: Export metrics to CSV or PDF reports

### Contributing
To add new predefined metrics, edit the `METRIC_TYPES` dictionary in `metrics_tool.py`:

```python
METRIC_TYPES = {
    "new_metric": {
        "name": "Display Name",
        "unit": "unit_name",
        "alt_unit": "alternative_unit_or_None"
    },
    # ... existing metrics
}
```

## Support

For issues or questions:
1. Check this guide for common solutions
2. Review API documentation
3. Verify authentication and network connectivity
4. Check the DevGuides for architectural details

---

**Happy metric tracking!**
