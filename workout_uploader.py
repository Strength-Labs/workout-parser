#!/usr/bin/env python3
import requests
import json
import argparse
import sys
import os
import getpass
import readline
import glob
from datetime import datetime, timedelta

# --- SCRIPT DESCRIPTION ---
# This script authenticates with the Turnkey Coach API and uploads
# one or more workouts from a specified JSON file.
# The JSON file must contain a single workout object or a list of workout objects.

TOKEN_CACHE_FILE = ".tokencache"

def complete(text, state):
    return (glob.glob(text+'*')+[None])[state]

readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")

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

def get_access_token(email, password, api_base_url):
    """
    Authenticates with the API using email and password to get an access token.
    Returns the token string if successful, otherwise None.
    """
    # First, try to load a valid token from the cache
    token = load_token()
    if token:
        print("Using cached access token. 👍")
        return token

    url = f"{api_base_url}/users/tokens/sign_in"
    headers = {"Content-Type": "application/json"}
    payload = {"email": email, "password": password}

    print("Attempting to get new access token...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
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

def upload_workout(token, workout_data, api_base_url):
    """
    Uploads a single workout to the API.
    """
    url = f"{api_base_url}/api/v1/workouts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        print(f"Uploading workout for {workout_data['workout_date']}...")
        response = requests.post(url, headers=headers, json=workout_data)
        response.raise_for_status()
        print(f"✅ Successfully uploaded workout for {workout_data['workout_date']}!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to upload workout for {workout_data['workout_date']}. HTTP Error: {e}")
        print(f"API Response: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred while uploading workout for {workout_data['workout_date']}: {e}")

def main():
    """
    Main function to parse arguments and run the workout upload process.
    """
    parser = argparse.ArgumentParser(description="Upload workouts to the Turnkey Coach API.")
    parser.parse_args()
    
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    # Get API base URL from environment or use default
    api_base_url = os.getenv("API_BASE_URL", "https://app.turnkey.coach")

    access_token = get_access_token(email, password, api_base_url)
    if not access_token:
        print("Could not get a valid access token. Aborting workout upload.")
        sys.exit(1)

    while True:
        json_file = input("Enter the path to the JSON file (or 'q' to quit): ")
        if json_file.lower() == 'q':
            break

        if not os.path.exists(json_file):
            print(f"Error: The file '{json_file}' was not found.")
            continue

        try:
            with open(json_file, 'r') as f:
                workout_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from file '{json_file}'. Please check the file format.")
            continue

        # If the JSON file contains a single workout, wrap it in a list
        if isinstance(workout_data, dict):
            workout_data = [workout_data]
        
        for workout in workout_data:
            upload_workout(access_token, workout, api_base_url)
            print("-" * 20)  # Separator for clarity

if __name__ == "__main__":
    main()


