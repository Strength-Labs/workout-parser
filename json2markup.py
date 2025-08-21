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
        coach_name = workout['created_by']['full_name']
        client_name = workout['user']['full_name']

        # Process top-level workout comments
        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                user_id = comment['user']['id']
                body = clean_text(comment['body'])
                
                if user_id == coach_id:
                    output_lines.append(f"\t[{coach_name}]: {body}")
                else:
                    output_lines.append(f"\t[{client_name}]: {body}")
        
        # This is a placeholder for a future feature. If the API provides private coach notes,
        # you would add logic here to format them with a '>>' tag.
        # For now, this section is a conceptual placeholder.
        # if 'private_coach_notes' in workout and workout['private_coach_notes']:
        #     for note in workout['private_coach_notes']:
        #         output_lines.append(f">>\t{clean_text(note['body'])}")

        # Process exercises
        for exercise in workout['assigned_exercises']:
            exercise_name = exercise['exercise']['name']
            output_lines.append(f"\n{exercise_name}")
            
            # Process assigned and actual sets
            for assigned_set in exercise['assigned_sets']:
                set_line = ""
                # Check if the set is a standard rep/weight/rpe set
                if assigned_set['set_type'] == 'default':
                    if assigned_set['rep_type'] == 'AMRAP':
                        set_line = f"\t{assigned_set['sets']}xAMRAP @ "
                    else:
                        set_line = f"\t{assigned_set['sets']}x{assigned_set['reps']} @ "
                    
                    if assigned_set['weight_type'] == 'RPE':
                        set_line += f"RPE {assigned_set['weight_type_value']}"
                    elif assigned_set['weight_type'] == 'percent':
                        set_line += f"{assigned_set['weight_type_value']}%"
                    else:
                        set_line += f"{assigned_set['weight']} {workout['weight_type']}"
                    output_lines.append(set_line)
                
                # Check if the set is a custom note
                elif assigned_set['set_type'] == 'custom':
                    body = clean_text(assigned_set['body'])
                    output_lines.append(f"\t{body}")

                # Check for actual sets and format them in parentheses
                if 'actual_sets' in assigned_set and assigned_set['actual_sets']:
                    for actual_set in assigned_set['actual_sets']:
                        actual_set_line = f"\t({actual_set['sets']}x{actual_set['reps']} @ {actual_set['weight']} {workout['weight_type']})"
                        output_lines.append(actual_set_line)

            # Process exercise-level comments
            if 'comments' in exercise and exercise['comments']:
                for comment in exercise['comments']:
                    user_id = comment['user']['id']
                    body = clean_text(comment['body'])
                    if user_id == coach_id:
                        output_lines.append(f"\t[{coach_name}]: {body}")
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

