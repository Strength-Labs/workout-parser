#!/usr/bin/env python3

# A script to download and intelligently display weightlifting PRs from the Turnkey Coach API.
#
# Required library: requests
# Install it by running: pip install requests

import requests
import getpass
import sys
import os
import json
from datetime import datetime, timedelta, date

# --- Configuration ---
API_BASE_URL = "https://app.turnkey.coach"
TOKEN_CACHE_FILE = ".tokencache"
MAIN_LIFTS = ["squat", "bench press", "deadlift", "press"]

def clear_screen():
    """Clears the terminal screen for a cleaner interface."""
    os.system('cls' if os.name == 'nt' else 'clear')

def save_auth_data(token, user_id):
    """Saves the access token, user ID, and expiration date to a cache file."""
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at.isoformat()
    }
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(auth_data, f)

def load_auth_data():
    """Loads auth data from the cache file if it's still valid."""
    if not os.path.exists(TOKEN_CACHE_FILE):
        return None, None
    with open(TOKEN_CACHE_FILE, 'r') as f:
        try:
            data = json.load(f)
            expires_at = datetime.fromisoformat(data.get("expires_at"))
            if expires_at > datetime.now():
                return data.get("token"), data.get("user_id")
        except (json.JSONDecodeError, KeyError, TypeError):
            return None, None
    return None, None

def get_access_token():
    """
    Authenticates with the API to get an access token and user ID.
    Uses a local cache to avoid logging in repeatedly.
    """
    token, user_id = load_auth_data()
    if token and user_id:
        print("Using cached access token. 👍")
        return token, user_id

    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    url = f"{API_BASE_URL}/users/tokens/sign_in"
    headers = {"Content-Type": "application/json"}
    payload = {"email": email, "password": password}

    print("Attempting to get new access token...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("token")
        user_id = data.get("resource_owner", {}).get("id")

        if token and user_id:
            print("Successfully obtained new access token. 🎉")
            save_auth_data(token, user_id)
            return token, user_id
        else:
            print("[ERROR] Authentication failed: Token or User ID missing in response.")
            return None, None
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] Login failed. The server responded with status {e.response.status_code}.")
        print(f"Server message: {e.response.text}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] A network error occurred during authentication: {e}")
        return None, None

def wendler_1rm(weight, reps):
    """Calculates estimated 1RM using the Wendler formula."""
    reps_val = reps if reps is not None else 1
    if not isinstance(reps_val, (int, float)) or reps_val <= 1:
        return weight
    return (weight * reps_val * 0.0333) + weight

def get_clients(token, user_id):
    """Fetches a de-duplicated list of clients."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/users/{user_id}/clients"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        relationships = response.json()
        
        unique_clients = {}
        for rel in relationships:
            if 'client' in rel:
                client = rel.get('client')
                client_id = client.get('id')
                if client_id and client_id not in unique_clients:
                    unique_clients[client_id] = client
        
        client_list = list(unique_clients.values())
        return sorted(client_list, key=lambda x: (x.get('last_name', ''), x.get('first_name', '')))
    except requests.exceptions.RequestException as err:
        print(f"\n[ERROR] Could not fetch clients: {err}")
        return []

def get_client_prs(token, client_id, start_date=None, end_date=None):
    """Fetches all PRs for a specific client within a date range."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": client_id}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
        
    url = f"{API_BASE_URL}/api/v1/prs"
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"\n[ERROR] Could not fetch PRs for client {client_id}: {err}")
        return []

def process_prs(all_prs):
    """Processes all PRs to find the single best PR for every exercise."""
    best_lifts = {}
    prs_by_exercise = {}
    for pr in all_prs:
        lift_name = pr.get("exercise", {}).get("name", "Unknown").lower()
        if lift_name not in prs_by_exercise:
            prs_by_exercise[lift_name] = []
        prs_by_exercise[lift_name].append(pr)

    for lift_name, pr_list in prs_by_exercise.items():
        best_pr_for_lift = None
        best_value = -1
        is_best_actual_1rm = False

        for pr in pr_list:
            reps = pr.get("reps")
            weight = float(pr.get("weight", 0) or 0)
            
            is_actual_1rm = (reps == 1)
            value = weight if is_actual_1rm else wendler_1rm(weight, reps)

            is_better = False
            if best_pr_for_lift is None:
                is_better = True
            elif is_actual_1rm and not is_best_actual_1rm:
                is_better = True
            elif is_actual_1rm == is_best_actual_1rm and value > best_value:
                is_better = True

            if is_better:
                best_pr_for_lift = pr
                best_value = value
                is_best_actual_1rm = is_actual_1rm
        
        best_lifts[lift_name] = best_pr_for_lift
            
    return best_lifts

def display_main_prs(client_name, client_id, best_lifts, date_range_str):
    """Displays the main lift PRs."""
    clear_screen()
    print(f"--- Top Personal Records for {client_name} (ID: {client_id}) ---")
    print(f"---      Date Range: {date_range_str}      ---\n")

    for lift in MAIN_LIFTS:
        pr = best_lifts.get(lift)
        lift_display_name = lift.replace(" press", " Press").title()

        if pr:
            weight = float(pr.get("weight", 0) or 0)
            reps = pr.get("reps")
            date_str = pr.get("date", "N/A")
            unit = pr.get("weight_type", "units")

            if reps == 1:
                print(f"{lift_display_name:<15} {weight:7.1f} {unit} on {date_str}")
            else:
                estimated_1rm = wendler_1rm(weight, reps)
                print(f"{lift_display_name:<15} {estimated_1rm:7.1f} {unit} on {date_str} (estimated from {weight} {unit} x {reps})")
        else:
            print(f"{lift_display_name:<15} No PR found")

def get_custom_dates():
    """Prompts user for a custom date range."""
    while True:
        try:
            start_str = input("Enter start date (YYYY-MM-DD): ")
            end_str = input("Enter end date   (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            return start_date.isoformat(), end_date.isoformat()
        except ValueError:
            print("\n[ERROR] Invalid date format. Please use YYYY-MM-DD.")
            if input("Try again? (y/n): ").lower() != 'y':
                return None, None

def pr_view_loop(token, client):
    """The loop for viewing a single client's PRs with date filtering."""
    client_id = client.get("id")
    client_name = f"{client.get('first_name')} {client.get('last_name')}"
    start_date, end_date = None, None
    date_range_str = "All Time"

    while True:
        all_prs = get_client_prs(token, client_id, start_date, end_date)
        if all_prs is None:
            input("\nCould not fetch PRs. Press Enter to return to client list.")
            break

        best_lifts = process_prs(all_prs)
        best_other_lifts = {k: v for k, v in best_lifts.items() if k not in MAIN_LIFTS}
        
        display_main_prs(client_name, client_id, best_lifts, date_range_str)

        print("\n" + "-"*50)
        print("OPTIONS: [3]m  [6]m  [Y]ear  [A]ll Time  [C]ustom  [M]ore PRs  [Enter] Go Back")
        choice = input("> ").lower()

        if choice == '':
            break
        elif choice == 'a':
            start_date, end_date = None, None
            date_range_str = "All Time"
        elif choice == '3':
            end_date = date.today()
            start_date = end_date - timedelta(days=90)
            date_range_str = f"Last 3 Months ({start_date.isoformat()} to {end_date.isoformat()})"
            start_date, end_date = start_date.isoformat(), end_date.isoformat()
        elif choice == '6':
            end_date = date.today()
            start_date = end_date - timedelta(days=180)
            date_range_str = f"Last 6 Months ({start_date.isoformat()} to {end_date.isoformat()})"
            start_date, end_date = start_date.isoformat(), end_date.isoformat()
        elif choice == 'y':
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            date_range_str = f"Last Year ({start_date.isoformat()} to {end_date.isoformat()})"
            start_date, end_date = start_date.isoformat(), end_date.isoformat()
        elif choice == 'c':
            start_date, end_date = get_custom_dates()
            if start_date and end_date:
                 date_range_str = f"Custom ({start_date} to {end_date})"
            else: # User cancelled custom date entry
                continue
        elif choice == 'm':
            print("\n--- Other Lifts ---")
            if not best_other_lifts:
                print("No other PRs found in this period.")
            else:
                for lift_name in sorted(best_other_lifts.keys()):
                    pr = best_other_lifts[lift_name]
                    display_name = lift_name.title()
                    weight = float(pr.get("weight", 0) or 0)
                    reps = pr.get("reps")
                    date_str = pr.get("date", "N/A")
                    unit = pr.get("weight_type", "units")
                    if reps == 1:
                        print(f"{display_name:<25} {weight:7.1f} {unit} on {date_str}")
                    else:
                        e1rm = wendler_1rm(weight, reps)
                        print(f"{display_name:<25} {e1rm:7.1f} {unit} on {date_str} (estimated from {weight} {unit} x {reps})")
            input("\nPress Enter to continue...")
        else:
            input("Invalid option. Press Enter to try again...")

def client_selection_loop(token, user_id):
    """The main application loop for selecting clients."""
    while True:
        clear_screen()
        clients = get_clients(token, user_id)
        if not clients:
            print("No clients found or could not fetch client list. Exiting.")
            break

        print("--- Select a Client ---")
        for i, client in enumerate(clients):
            first_name = client.get('first_name', 'N/A')
            last_name = client.get('last_name', 'N/A')
            print(f"{i + 1:2d}. {first_name} {last_name}")
        print("\nEnter a number to select a client, or 'q' to quit.")
        
        choice = input("> ")
        if choice.lower() == 'q':
            break

        try:
            client_index = int(choice) - 1
            if 0 <= client_index < len(clients):
                pr_view_loop(token, clients[client_index])
            else:
                input("Invalid number. Press Enter to try again...")
        except ValueError:
            input("Invalid input. Please enter a number. Press Enter to try again...")

if __name__ == "__main__":
    clear_screen()
    print("--- Turnkey Coach PR Downloader ---")
    
    access_token, coach_user_id = get_access_token()

    if access_token and coach_user_id:
        client_selection_loop(access_token, coach_user_id)
    
    print("\nExiting. Goodbye!")
