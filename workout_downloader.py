#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import os
import getpass
from datetime import datetime, timedelta

# --- SCRIPT DESCRIPTION ---
# This script authenticates with the Turnkey Coach API and downloads
# workouts for a specified user, including all comments and details.

TOKEN_CACHE_FILE = ".tokencache"
API_BASE_URL = os.getenv("API_BASE_URL", "https://app.turnkey.coach")

def save_token(token):
    """
    Saves the access token and its expiration date to a cache file.
    """
    # Expiration is set to 1 hour from now
    expires_at = datetime.now() + timedelta(hours=1)
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump({"token": token, "expires_at": expires_at.isoformat()}, f)

def load_token():
    """
    Loads the access token from the cache file and checks if it's still valid.
    Returns the token string if valid, otherwise None.
    """
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None

    with open(TOKEN_CACHE_FILE, 'r') as f:
        try:
            data = json.load(f)
            expires_at = datetime.fromisoformat(data.get("expires_at"))
            if expires_at > datetime.now():
                return data.get("token")
            else:
                return None
        except (json.JSONDecodeError, KeyError):
            return None

def get_access_token(email, password):
    """
    Authenticates with the API using email and password to get an access token.
    Returns the token string if successful, otherwise None.
    """
    token = load_token()
    if token:
        print("Using cached access token. 👍")
        return token

    url = f"{API_BASE_URL}/users/tokens/sign_in"
    headers = {"Content-Type": "application/json"}
    payload = {"email": email, "password": password}

    print("Attempting to get new access token...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        token = response.json().get("token")
        if token:
            print("Successfully obtained new access token. 🎉")
            save_token(token)
            return token
        else:
            print("Authentication failed: No token in response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during authentication: {e}")
        return None

def download_workouts(token, user_id, start_date=None, end_date=None):
    """
    Downloads workouts from the API, fetching full details for each workout to include comments.
    """
    # First, get a list of all workout IDs for the specified user and date range.
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": user_id, "sort": "ascending", "published": True}
    
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        print(f"Fetching list of workouts for user ID {user_id}...")
        response = requests.get(list_url, headers=headers, params=params)
        response.raise_for_status()
        workouts_list = response.json()
        print(f"Found {len(workouts_list)} workouts.")
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred while fetching the workout list: {e}")
        return None
    
    detailed_workouts = []
    # Now, iterate through the list and get the full details for each workout, including comments.
    for workout_summary in workouts_list:
        workout_id = workout_summary['id']
        detail_url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
        
        try:
            print(f"Downloading details for workout ID {workout_id}...")
            response = requests.get(detail_url, headers=headers)
            response.raise_for_status()
            detailed_workout = response.json()
            detailed_workouts.append(detailed_workout)
            print(f"✅ Successfully downloaded workout {workout_id}.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to download details for workout {workout_id}. Error: {e}")

    return detailed_workouts

def main():
    """
    Main function to handle user input and run the download process.
    """
    parser = argparse.ArgumentParser(description="Download workouts from the Turnkey Coach API.")
    parser.add_argument("--user_id", type=int, required=True, help="The ID of the user to download workouts for.")
    parser.add_argument("--start_date", help="Start date (YYYY-MM-DD) to filter workouts.")
    parser.add_argument("--end_date", help="End date (YYYY-MM-DD) to filter workouts.")
    args = parser.parse_args()

    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    access_token = get_access_token(email, password)
    if not access_token:
        print("Could not get a valid access token. Aborting workout download.")
        sys.exit(1)

    workouts = download_workouts(access_token, args.user_id, args.start_date, args.end_date)
    
    if workouts:
        output_filename = f"workouts_user_{args.user_id}.json"
        with open(output_filename, 'w') as f:
            json.dump(workouts, f, indent=2)
        print(f"Successfully saved {len(workouts)} workouts to {output_filename}")

if __name__ == "__main__":
    main()

