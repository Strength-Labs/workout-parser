from datetime import datetime
from src.api_client import clean_text

def format_time(seconds):
    """Formats raw seconds (int) to MM:SS string for markup."""
    if not seconds or seconds <= 0:
        return None
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def format_workouts_to_markup(workouts, coach_user_id, metrics=None):
    """
    Parses a list of workout/nutrition objects and formats it into the custom markup,
    correctly handling both training calendar (workout_type: default) and nutrition calendar
    (workout_type: nutrition) assignments.

    Args:
        workouts: List of workout/nutrition assignment dictionaries
        coach_user_id: User ID of the coach (for filtering comments)
        metrics: Optional list of metric dictionaries to include in output
    """
    output_lines = []

    # Group metrics by date for easy lookup
    metrics_by_date = {}
    if metrics:
        for metric in metrics:
            date = metric.get('metric_date')
            if date:
                if date not in metrics_by_date:
                    metrics_by_date[date] = []
                metrics_by_date[date].append(metric)

    for workout in workouts:
        workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")

        # Determine date header based on workout_type
        workout_type = workout.get('workout_type', 'default')
        date_header = "Nutrition Date:" if workout_type == "nutrition" else "Workout Date:"

        output_lines.append(f"{date_header} {workout_date.strftime('%Y-%m-%d')}")

        if workout.get('title'):
            output_lines.append(f"{workout['title']}")

        output_lines.append("")

        # Check if this is a future workout (not yet due)
        from datetime import date
        today = date.today()
        if workout_date.date() > today:
            output_lines.append("> Future workout (not yet completed)")
            output_lines.append("")

        # Add metrics for this workout date (from external metrics parameter)
        # These are from pending_metrics in upload, which may have is_prescriptive flag
        workout_date_str = workout['workout_date']
        if workout_date_str in metrics_by_date:
            for metric in metrics_by_date[workout_date_str]:
                metric_type = metric.get('metric_type', '')
                value = metric.get('value')
                unit = metric.get('unit') or ''
                notes = metric.get('notes') or ''
                is_prescriptive = metric.get('is_prescriptive', False)

                # Determine symbol: @ for prescriptive (has value), ? for informational (no value)
                if value not in [None, '']:
                    # Prescriptive metric with target value
                    symbol = '@'
                    components = [str(value)]
                    if unit:
                        components.append(unit)
                    if notes:
                        components.append(notes)
                    metric_line = f"{symbol}{metric_type}: {' '.join(components)}"
                else:
                    # Informational/tracking metric (no value)
                    symbol = '?'
                    # For informational metrics, notes may contain unit info
                    metric_line = f"{symbol}{metric_type}:"
                    if notes:
                        metric_line += f" {notes}"

                output_lines.append(metric_line)

                # Handle multi-line notes (notes with newlines)
                if notes and '\n' in notes:
                    # First line was already added inline, add rest as indented
                    note_lines = notes.split('\n')
                    for note_line in note_lines[1:]:  # Skip first line, already inline
                        output_lines.append(f"    {note_line}")

            output_lines.append("")
        
        # Add assigned metrics from the workout data itself (downloaded from API)
        assigned_metrics = workout.get('assigned_metrics', [])
        if assigned_metrics:
            for assigned_metric in assigned_metrics:
                # Extract metric info from the assigned metric structure
                description = assigned_metric.get('description', '')
                metric_info = assigned_metric.get('metric', {})
                metric_answer = assigned_metric.get('metric_answer')

                # Get the canonical metric name from the metric definition
                metric_name = metric_info.get('name', '').lower().replace(' ', '_').replace('(', '').replace(')', '')
                if not metric_name:
                    metric_name = f"metric_{assigned_metric.get('id', 'unknown')}"

                # Determine metric type based on whether there's a prescribed value vs tracking request
                # The API doesn't clearly distinguish, so we infer from structure:
                # - If description exists AND there's a numeric value in it → prescriptive (@)
                # - If description is just instructions (no number) → informational (?)
                # - If client responded with value → show both request and response

                if metric_answer and metric_answer.get('value') is not None:
                    # Client has responded - determine if coach prescribed a target or asked for tracking
                    # Check if description contains a number (prescriptive) or just instructions (informational)
                    import re
                    has_number_in_desc = bool(re.search(r'\d+', description)) if description else False

                    if has_number_in_desc:
                        # Prescriptive metric: coach set a target, client reported actual
                        symbol = '@'
                        metric_line = f"{symbol}{metric_name}: {description}"
                    else:
                        # Informational metric: coach asked for data, client provided
                        symbol = '?'
                        metric_line = f"{symbol}{metric_name}:"
                        if description:
                            # Add description as inline notes
                            metric_line += f" {description}"

                    output_lines.append(metric_line)

                    # Handle multi-line description as indented notes
                    if description and '\n' in description:
                        desc_lines = description.split('\n')
                        for desc_line in desc_lines[1:]:  # Skip first line, already inline
                            output_lines.append(f"    {desc_line}")

                    # Output the client's actual response in parentheses
                    client_value = metric_answer['value']
                    response_parts = [str(client_value)]

                    # Check if there are additional fields in metric_answer (units, notes)
                    # Include them in the response if present
                    response_line = f"({symbol}{metric_name}: {' '.join(response_parts)})"
                    output_lines.append(response_line)
                else:
                    # No client response yet - this is an unanswered metric request
                    # Use ? for informational (tracking request with no response yet)
                    symbol = '?'
                    metric_line = f"{symbol}{metric_name}:"
                    if description:
                        metric_line += f" {description}"

                    output_lines.append(metric_line)

                    # Handle multi-line description
                    if description and '\n' in description:
                        desc_lines = description.split('\n')
                        for desc_line in desc_lines[1:]:
                            output_lines.append(f"    {desc_line}")
                    # No parentheses = client didn't provide a value

            output_lines.append("")

        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                body = clean_text(comment['body'] or "")
                if not body: continue
                comment_lines = body.split('\n')
                output_lines.append(f"\t[{comment['user']['full_name']}]: {comment_lines[0]}")
                for line in comment_lines[1:]:
                    output_lines.append(f"\t{line}")
            output_lines.append("")

        for exercise in workout.get('assigned_exercises', []):
            output_lines.append(f"{exercise['exercise']['name']}")

            # BULLETPROOF COMPLETION LOGIC (Priority Order):
            # Priority 1: Check if exercise was explicitly marked as missed
            # Priority 2: Check if actual_sets data exists (takes precedence over completed flag)
            # Priority 3: Check if workout not completed and no actual_sets
            # Priority 4: Workout completed, no actual_sets, not missed = completed as prescribed

            # Check if exercise has ANY actual_sets
            has_any_actual_sets = False
            if 'assigned_sets' in exercise:
                for assigned_set in exercise['assigned_sets']:
                    if assigned_set.get('actual_sets') and len(assigned_set.get('actual_sets', [])) > 0:
                        has_any_actual_sets = True
                        break

            # Priority 1: Explicitly marked as missed
            if exercise.get('missed', False):
                # Output prescribed sets first
                if 'assigned_sets' in exercise:
                    for assigned_set in exercise['assigned_sets']:
                        if assigned_set.get('set_type') == 'custom':
                            note_body = clean_text(assigned_set.get('body') or "")
                            if note_body:
                                output_lines.append(f"\t{note_body}")
                        else:
                            output_lines.append(f"{assigned_set['display_label']}")
                # Mark as skipped
                output_lines.append("(skipped)")

            # Priority 2: Has actual_sets data (regardless of completed flag)
            elif has_any_actual_sets:
                # Output prescribed sets with actual performance data
                if 'assigned_sets' in exercise:
                    for assigned_set in exercise['assigned_sets']:
                        # Custom formatter for time-based sets (override API's raw display_label)
                        if (assigned_set.get('time', 0) > 0 and
                            (assigned_set.get('reps') is None or assigned_set.get('reps', 0) == 0) and
                            assigned_set.get('weight_type') in ['bodyweight', 'RPE']):
                            # Time-based: e.g., "10 x 00:10 @ RPE 10"
                            sets = assigned_set.get('sets', 1)
                            formatted_time = format_time(assigned_set.get('time'))
                            if formatted_time:
                                if assigned_set.get('weight_type') == 'RPE' and assigned_set.get('weight_type_value'):
                                    rpe_val = assigned_set['weight_type_value']
                                    display = f"{sets} x {formatted_time} @ RPE {rpe_val}"
                                else:
                                    display = f"{sets} x {formatted_time}"
                                output_lines.append(f"{display}")
                            else:
                                # Fallback to API label if formatting fails
                                output_lines.append(f"{assigned_set['display_label']}")
                        # Check if the set is a custom note
                        elif assigned_set.get('set_type') == 'custom':
                            note_body = clean_text(assigned_set.get('body') or "")
                            if note_body:
                                output_lines.append(f"\t{note_body}")
                        else:
                            output_lines.append(f"{assigned_set['display_label']}")

                        # Output actual performance data in parentheses
                        if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
                            for actual_set in assigned_set['actual_sets']:
                                reps, weight, sets = actual_set.get('reps', ''), actual_set.get('weight', ''), actual_set.get('sets', '')
                                output_lines.append(f"({sets}x{reps} @ {weight})")

            # Priority 3: Workout not completed and no actual_sets = skipped (only for past workouts)
            elif not workout.get('completed', False) and workout_date.date() <= today:
                # Output prescribed sets first
                if 'assigned_sets' in exercise:
                    for assigned_set in exercise['assigned_sets']:
                        if assigned_set.get('set_type') == 'custom':
                            note_body = clean_text(assigned_set.get('body') or "")
                            if note_body:
                                output_lines.append(f"\t{note_body}")
                        else:
                            output_lines.append(f"{assigned_set['display_label']}")
                # Mark as skipped
                output_lines.append("(skipped)")

            # Priority 4: Workout completed, no actual_sets, not missed = completed as prescribed
            else:
                # Output prescribed sets only (no parentheses = completed as prescribed)
                if 'assigned_sets' in exercise:
                    for assigned_set in exercise['assigned_sets']:
                        # Custom formatter for time-based sets
                        if (assigned_set.get('time', 0) > 0 and
                            (assigned_set.get('reps') is None or assigned_set.get('reps', 0) == 0) and
                            assigned_set.get('weight_type') in ['bodyweight', 'RPE']):
                            sets = assigned_set.get('sets', 1)
                            formatted_time = format_time(assigned_set.get('time'))
                            if formatted_time:
                                if assigned_set.get('weight_type') == 'RPE' and assigned_set.get('weight_type_value'):
                                    rpe_val = assigned_set['weight_type_value']
                                    display = f"{sets} x {formatted_time} @ RPE {rpe_val}"
                                else:
                                    display = f"{sets} x {formatted_time}"
                                output_lines.append(f"{display}")
                            else:
                                output_lines.append(f"{assigned_set['display_label']}")
                        elif assigned_set.get('set_type') == 'custom':
                            note_body = clean_text(assigned_set.get('body') or "")
                            if note_body:
                                output_lines.append(f"\t{note_body}")
                        else:
                            output_lines.append(f"{assigned_set['display_label']}")

            if 'comments' in exercise and exercise['comments']:
                 output_lines.append("")
                 for comment in exercise['comments']:
                    body = clean_text(comment['body'] or "")
                    if not body: continue
                    comment_lines = body.split('\n')
                    output_lines.append(f"\t[{comment['user']['full_name']}]: {comment_lines[0]}")
                    for line in comment_lines[1:]:
                        output_lines.append(f"\t{line}")
            output_lines.append("")
        
        output_lines.append("---\n")

    return '\n'.join(output_lines)
