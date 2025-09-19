from datetime import datetime
from api_client import clean_text # Import our shared helper

def format_workouts_to_markup(workouts, coach_user_id):
    """
    Parses a list of workout objects and formats it into the custom markup,
    with all comments being indented, including multi-line comments.
    """
    output_lines = []
    
    for workout in workouts:
        workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")
        output_lines.append(f"Workout Date: {workout_date.strftime('%Y-%m-%d')}\n")

        # Top-level workout comments
        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                commenter_name = comment['user']['full_name']
                body = clean_text(comment['body'])
                
                # Handle empty comments gracefully
                if not body:
                    output_lines.append(f"\t[{commenter_name}]: ")
                    continue
                
                # Split multi-line comments and indent each line
                comment_lines = body.split('\n')
                output_lines.append(f"\t[{commenter_name}]: {comment_lines[0]}")
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
                            reps = actual_set.get('reps', '')
                            weight = actual_set.get('weight', '')
                            sets = actual_set.get('sets', '')
                            output_lines.append(f"({sets}x{reps} @ {weight})")

            # Exercise-level comments
            if 'comments' in exercise and exercise['comments']:
                 output_lines.append("")
                 for comment in exercise['comments']:
                    commenter_name = comment['user']['full_name']
                    body = clean_text(comment['body'])

                    if not body:
                        output_lines.append(f"\t[{commenter_name}]: ")
                        continue

                    comment_lines = body.split('\n')
                    output_lines.append(f"\t[{commenter_name}]: {comment_lines[0]}")
                    for line in comment_lines[1:]:
                        output_lines.append(f"\t{line}")
            output_lines.append("")
        
        output_lines.append("---\n")

    return '\n'.join(output_lines)
