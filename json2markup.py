#!/usr/bin/env python3

import json
import argparse
from datetime import datetime
import html
import re
import os
import sys

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
        unescaped_text = html.unescape(raw_html)
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', unescaped_text)
        return re.sub(r'\s+', ' ', cleantext).strip()

    for workout in workouts:
        workout_date = datetime.strptime(workout['workout_date'], "%Y-%m-%d")
        output_lines.append(f"Workout Date: {workout_date.strftime('%Y-%m-%d')}\n")

        if 'comments' in workout and workout['comments']:
            for comment in workout['comments']:
                commenter_name = comment['user']['full_name']
                body = clean_text(comment['body'])
                output_lines.append(f"\t[{commenter_name}]: {body}")
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
                            output_lines.append(f"\tAccomplished: {sets}x{reps} @ {weight}")

            if 'comments' in exercise and exercise['comments']:
                 output_lines.append("")
                 for comment in exercise['comments']:
                    commenter_name = comment['user']['full_name']
                    body = clean_text(comment['body'])
                    output_lines.append(f"\t[{commenter_name}]: {body}")
            output_lines.append("")


    return '\n'.join(output_lines)

def main():
    """Main function to parse arguments and call the formatting function."""
    parser = argparse.ArgumentParser(description='Parse and format workout JSON data.')
    parser.add_argument('input_json_file', help='Path to the input JSON file')
    parser.add_argument('--coach_id', type=int, required=True, help='Coach ID to format comments differently')
    parser.add_argument('-o', '--output', help='Path to the output text file')
    args = parser.parse_args()

    try:
        formatted_output = parse_and_format_workouts(args.input_json_file, args.coach_id)

        if args.output:
            output_filename = args.output
        else:
            base = os.path.basename(args.input_json_file)
            output_filename = os.path.splitext(base)[0] + '.txt'

        with open(output_filename, 'w') as f:
            f.write(formatted_output)
        
        print(f"Successfully formatted workout data to {output_filename}")

    except (FileNotFoundError, ValueError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
