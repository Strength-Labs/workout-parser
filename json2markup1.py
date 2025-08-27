import json
import sys
import argparse
import re
import os
import html

def parse_and_format_workouts(input_json_path, coach_id):
    """
    Parses a JSON file of workouts and formats it into a custom plain text markup.

    Args:
        input_json_path (str): The path to the input JSON file.
        coach_id (int): The user ID of the coach to distinguish comments.

    Returns:
        str: The formatted workout string.
    """
    try:
        with open(input_json_path, 'r') as f:
            workouts = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{input_json_path}' was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: Could not decode JSON from file '{input_json_path}'. Please check the file format.")

    output_lines = []

    def clean_text(raw_html):
        """Strips HTML tags, unescapes HTML entities, and removes extra whitespace from a string."""
        # Unescape HTML entities first
        unescaped_text = html.unescape(raw_html)
        # Then strip HTML tags
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', unescaped_text)
        # Replace multiple whitespace characters with a single space and strip leading/trailing spaces
        return re.sub(r'\s+', ' ', cleantext).strip()

    for workout in workouts:
        # Start with the workout date
        output_lines.append(f"Workout Date: {workout['workout_date']}\n")

        # Get coach's and client's full names from the workout object
        coach_name = None
        if workout.get('created_by') and workout['created_by']['id'] == coach_id:
            coach_name = workout['created_by']['full_name']
        client_name = workout['user']['full_name']

        # Process top-level workout comments
        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                user_id = comment['user']['id']
                body = clean_text(comment['body'])
                
                # Check for the coach's ID
                if user_id == coach_id:
                    if coach_name:
                        output_lines.append(f"\t[{coach_name}]: {body}")
                    else:
                        # Fallback if coach_name is None
                        output_lines.append(f"\t[Coach]: {body}")
                else:
                    output_lines.append(f"\t[{client_name}]: {body}")
        
        # Process exercises
        for exercise in workout['assigned_exercises']:
            exercise_name = exercise['exercise']['name']
            output_lines.append(f"\n{exercise_name}")
            
            # Process assigned and actual sets
            for assigned_set in exercise['assigned_sets']:
                set_line = ""
                
                # Check for distance-based sets
                if assigned_set['set_type'] == 'distance' and assigned_set.get('distance') is not None:
                    distance = assigned_set.get('distance')
                    distance_unit = assigned_set.get('distance_unit')
                    time_minutes = assigned_set.get('minutes', 0)
                    time_seconds = assigned_set.get('seconds', 0)
                    
                    time_string = ""
                    if time_minutes or time_seconds:
                        time_string = f"@ {str(time_minutes).zfill(2)}:{str(time_seconds).zfill(2)}"
                    
                    set_line = f"\t{distance} {distance_unit} {time_string}".strip()
                    
                # Check if the set is a standard rep/weight/rpe set
                elif assigned_set['set_type'] == 'default':
                    if 'sets' in assigned_set and 'reps' in assigned_set:
                        if assigned_set['rep_type'] == 'AMRAP':
                            set_line = f"\t{assigned_set['sets']}xAMRAP @ "
                        else:
                            set_line = f"\t{assigned_set['sets']}x{assigned_set['reps']} @ "
                    
                    if assigned_set['weight_type'] == 'RPE':
                        set_line += f"RPE {assigned_set['weight_type_value']}"
                    elif 'weight' in assigned_set and assigned_set['weight'] is not None:
                        if assigned_set['weight_type'] == 'percent':
                            set_line += f"{assigned_set['weight_type_value']}%"
                        else:
                            set_line += f"{assigned_set['weight']} {workout['weight_type']}"
                    
                # Check if the set is a custom note
                elif assigned_set['set_type'] == 'custom':
                    if 'body' in assigned_set and assigned_set['body']:
                        body = clean_text(assigned_set['body'])
                        set_line = f"\t{body}"

                # Append the formatted line
                if set_line:
                    output_lines.append(set_line)

                # Now process the actual sets without indentation
                if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
                    for actual_set in assigned_set['actual_sets']:
                        actual_weight = actual_set.get('weight')
                        actual_reps = actual_set.get('reps')
                        actual_sets_count = actual_set.get('sets')
                        
                        actual_set_line = ""
                        if actual_weight is not None and actual_reps is not None:
                            actual_set_line = f"({actual_sets_count}x{actual_reps} @ {actual_weight} {workout['weight_type']})"
                        elif actual_reps is not None:
                            actual_set_line = f"({actual_sets_count}x{actual_reps})"
                        
                        if actual_set_line:
                            output_lines.append(f"\t{actual_set_line}")


            # Process exercise-level comments
            if 'comments' in exercise and exercise['comments']:
                for comment in exercise['comments']:
                    user_id = comment['user']['id']
                    body = clean_text(comment['body'])
                    if user_id == coach_id:
                        if coach_name:
                            output_lines.append(f"\t[{coach_name}]: {body}")
                        else:
                            output_lines.append(f"\t[Coach]: {body}")
                    else:
                        output_lines.append(f"\t[{client_name}]: {body}")
        
        output_lines.append("\n" + "---" + "\n") # Separator between workouts

    return "\n".join(output_lines).strip()

def main():
    """
    Main function to run the reverse parser.
    """
    parser = argparse.ArgumentParser(description="Convert JSON workout file to custom markup.")
    parser.add_argument("input_json_file", help="Path to the JSON file to be parsed.")
    parser.add_argument("--coach_id", type=int, required=True, help="The user ID of the coach to distinguish comments.")
    parser.add_argument("--output_file", help="Optional output file path. Defaults to input_file.txt.")
    args = parser.parse_args()

    try:
        formatted_output = parse_and_format_workouts(args.input_json_file, args.coach_id)
        
        output_filename = args.output_file
        if not output_filename:
            base, _ = os.path.splitext(args.input_json_file)
            output_filename = f"{base}.txt"

        with open(output_filename, 'w') as f:
            f.write(formatted_output)
        
        print(f"Successfully converted and saved workout to '{output_filename}'")
    
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

