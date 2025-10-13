from datetime import datetime
from api_client import clean_text

def format_time(seconds):
    """Formats raw seconds (int) to MM:SS string for markup."""
    if not seconds or seconds <= 0:
        return None
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def format_workouts_to_markup(workouts, coach_user_id):
    """
    Parses a list of workout objects and formats it into the custom markup,
    now correctly indenting "custom" set notes and formatting time-based sets as MM:SS.
    """
    output_lines = []
    
    for workout in workouts:
        workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")
        output_lines.append(f"Workout Date: {workout_date.strftime('%Y-%m-%d')}")
        
        if workout.get('title'):
            output_lines.append(f"{workout['title']}")
        
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
