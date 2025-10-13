from datetime import datetime
from api_client import clean_text

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

        # Add metrics for this workout date (from external metrics parameter)
        workout_date_str = workout['workout_date']
        if workout_date_str in metrics_by_date:
            for metric in metrics_by_date[workout_date_str]:
                metric_type = metric.get('metric_type', '')
                value = metric.get('value')
                unit = metric.get('unit') or ''
                notes = metric.get('notes') or ''

                # Build components while allowing placeholder metrics (no numeric value)
                components = []
                if value not in [None, '']:
                    components.append(str(value))
                if unit:
                    components.append(unit)
                if notes:
                    components.append(notes)

                metric_line = f"@{metric_type}:"
                if components:
                    metric_line += f" {' '.join(components)}"

                output_lines.append(metric_line)
            output_lines.append("")
        
        # Add assigned metrics from the workout data itself
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
                
                # Determine if this is prescribed (has target value) or tracking (client enters value)
                # Based on API structure: metric_answer.value exists when there's a prescribed target
                # or when client has responded to a tracking metric
                
                if metric_answer and metric_answer.get('value') is not None:
                    # There's a value - this could be either:
                    # 1. Prescribed target (coach set a goal)
                    # 2. Client response to tracking request
                    
                    # The API structure doesn't clearly distinguish these cases in the download
                    # For now, we'll assume most metrics with values are client responses
                    # and should show both the request and response
                    
                    # Output the coach's request (either with description or just the metric name)
                    if description:
                        metric_line = f"@{metric_name}: {description}"
                    else:
                        # Even without description, this is likely a tracking request
                        # The client provided a value, so show it as a tracking request
                        metric_line = f"@{metric_name}:"
                    
                    output_lines.append(metric_line)
                    
                    # Output the client's actual response in parentheses
                    client_value = metric_answer['value']
                    # Include any additional info from metric_answer if available
                    response_parts = [str(client_value)]
                    
                    # Check if there are additional fields in metric_answer we should include
                    # (like units or notes from the client's response)
                    response_line = f"(@{metric_name}: {' '.join(response_parts)})"
                    output_lines.append(response_line)
                else:
                    # No value - this is a tracking metric that client hasn't responded to yet
                    metric_line = f"@{metric_name}: {description}" if description else f"@{metric_name}:"
                    output_lines.append(metric_line)
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
                    # THE FIX: Check if the set is a custom note
                    elif assigned_set.get('set_type') == 'custom':
                        note_body = clean_text(assigned_set.get('body') or "")
                        if note_body:
                            output_lines.append(f"\t{note_body}")
                    else:
                        output_lines.append(f"{assigned_set['display_label']}")

                    if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
                        for actual_set in assigned_set['actual_sets']:
                            reps, weight, sets = actual_set.get('reps', ''), actual_set.get('weight', ''), actual_set.get('sets', '')
                            output_lines.append(f"({sets}x{reps} @ {weight})")

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
