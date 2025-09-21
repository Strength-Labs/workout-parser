from datetime import datetime
from api_client import clean_text

def format_workouts_to_markup(workouts, coach_user_id):
    """
    Parses a list of workout objects and formats it into the custom markup,
    now including the workout title.
    """
    output_lines = []
    
    for workout in workouts:
        workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")
        output_lines.append(f"Workout Date: {workout_date.strftime('%Y-%m-%d')}")
        
        # Add the title if it exists
        if workout.get('title'):
            output_lines.append(f"{workout['title']}")
        
        output_lines.append("") # Add a blank line for spacing

        # ... (rest of the function remains the same) ...
        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                body = clean_text(comment['body'])
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
                    output_lines.append(f"{assigned_set['display_label']}")
                    if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
                        for actual_set in assigned_set['actual_sets']:
                            reps, weight, sets = actual_set.get('reps', ''), actual_set.get('weight', ''), actual_set.get('sets', '')
                            output_lines.append(f"({sets}x{reps} @ {weight})")

            if 'comments' in exercise and exercise['comments']:
                 output_lines.append("")
                 for comment in exercise['comments']:
                    body = clean_text(comment['body'])
                    if not body: continue
                    comment_lines = body.split('\n')
                    output_lines.append(f"\t[{comment['user']['full_name']}]: {comment_lines[0]}")
                    for line in comment_lines[1:]:
                        output_lines.append(f"\t{line}")
            output_lines.append("")
        
        output_lines.append("---\n")

    return '\n'.join(output_lines)
