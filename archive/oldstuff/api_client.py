import requests
import getpass
import os
import json
import re
import html
from datetime import datetime, timedelta
from rich.console import Console

# --- Configuration ---
API_BASE_URL = "https://app.turnkey.coach"
TOKEN_CACHE_FILE = ".tokencache"
CLIENT_DATA_DIR = os.path.expanduser("~/TurnkeyClients")
console = Console()

# --- Shared Helper Functions ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def clean_text(raw_html):
    if not raw_html: return ""
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</p>|</div>', '\n', text, flags=re.IGNORECASE)
    text = html.unescape(text)
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

# --- Data Loading and Updating ---
def load_exercise_map():
    """Loads exerciselist.json and creates a name-to-ID mapping."""
    try:
        filepath = os.path.join(os.path.dirname(__file__), 'exerciselist.json')
        with open(filepath, 'r') as f:
            exercises = json.load(f)
        return {ex['name'].lower(): ex['id'] for ex in exercises}
    except FileNotFoundError:
        console.print("[bold red]Error: `exerciselist.json` not found.[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error loading exercise list: {e}[/bold red]")
        return None

def update_exercise_list(token):
    """Fetches the latest exercise list from the API and saves it to exerciselist.json."""
    url = f"{API_BASE_URL}/api/v1/exercises"
    headers = {"Authorization": f"Bearer {token}"}
    filepath = os.path.join(os.path.dirname(__file__), 'exerciselist.json')

    with console.status("[bold green]Downloading latest exercise list...[/bold green]"):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            exercises = response.json()
            with open(filepath, 'w') as f:
                json.dump(exercises, f, indent=2)
            console.print(f"✅ [green]Successfully saved {len(exercises)} exercises to {filepath}[/green]")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [red]Error fetching exercises: {e}[/red]")
            return False

def _download_workouts_from_api(token, client_id, start_date=None):
    # ... (This function remains the same)
    status_message = "Downloading full workout history" if not start_date else "Downloading new workouts"
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    if start_date:
        params["start_date"] = start_date
    with console.status(f"[bold green]{status_message} for client {client_id}...[/bold green]"):
        try:
            response = requests.get(list_url, headers=headers, params=params)
            response.raise_for_status()
            workouts_summary = response.json()
            detailed_workouts = []
            for summary in workouts_summary:
                workout_id = summary['id']
                detail_url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
                detail_response = requests.get(detail_url, headers=headers)
                if detail_response.status_code == 200:
                    detailed_workouts.append(detail_response.json())
            return detailed_workouts
        except requests.exceptions.RequestException:
            return []

def get_workout_history(token, client, force_refresh=False):
    # ... (This function remains the same)
    client_id = client["id"]
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    workout_cache_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    os.makedirs(client_dir, exist_ok=True)
    if force_refresh:
        workouts = _download_workouts_from_api(token, client_id)
        with open(workout_cache_path, 'w', encoding='utf-8') as f: json.dump(workouts, f, indent=4)
        return workouts
    if os.path.exists(workout_cache_path):
        with open(workout_cache_path, 'r', encoding='utf-8') as f:
            existing_workouts = json.load(f)
        if not existing_workouts:
            return get_workout_history(token, client, force_refresh=True)
        valid_workouts = [w for w in existing_workouts if w.get('workout_date')]
        if not valid_workouts:
             return get_workout_history(token, client, force_refresh=True)
        latest_date_str = max(w['workout_date'] for w in valid_workouts)
        start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)
        new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())
        if new_workouts:
            console.print(f"[green]Found {len(new_workouts)} new workouts. Updating cache...[/green]")
            all_workouts = existing_workouts + new_workouts
            with open(workout_cache_path, 'w', encoding='utf-8') as f: json.dump(all_workouts, f, indent=4)
            return all_workouts
        else:
            console.print("[dim]Workout history is up to date.[/dim]")
            return existing_workouts
    else:
        return get_workout_history(token, client, force_refresh=True)

# --- (Authentication and get_clients functions remain the same) ---
def save_auth_data(token, user_id):
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {"token": token, "user_id": user_id, "expires_at": expires_at.isoformat()}
    with open(TOKEN_CACHE_FILE, 'w') as f: json.dump(auth_data, f)

def load_auth_data():
    if not os.path.exists(TOKEN_CACHE_FILE): return None, None
    with open(TOKEN_CACHE_FILE, 'r') as f:
        try:
            data = json.load(f)
            if datetime.fromisoformat(data.get("expires_at")) > datetime.now():
                return data.get("token"), data.get("user_id")
        except (json.JSONDecodeError, KeyError, TypeError): pass
    return None, None

def get_access_token():
    token, user_id = load_auth_data()
    if token and user_id:
        console.print("Using cached access token. 👍", style="green")
        return token, user_id
    email = console.input("[bold]Enter your email:[/bold] ")
    password = getpass.getpass("Enter your password: ")
    url = f"{API_BASE_URL}/users/tokens/sign_in"
    headers = {"Content-Type": "application/json"}
    payload = {"email": email, "password": password}
    with console.status("Authenticating..."):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            token, user_id = data.get("token"), data.get("resource_owner", {}).get("id")
            if token and user_id:
                console.print("Successfully obtained new access token. 🎉", style="green")
                save_auth_data(token, user_id)
                return token, user_id
        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Login failed:[/bold red] {e}")
            return None, None

def get_clients(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/users/{user_id}/clients"
    with console.status("Fetching client list..."):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            relationships = response.json()
            clients_data = {}
            for rel in relationships:
                client_info, coach_info = rel.get('client'), rel.get('coach')
                if not client_info or not coach_info: continue
                client_id = client_info.get('id')
                if client_id not in clients_data:
                    clients_data[client_id] = {'id': client_id, 'full_name': client_info.get('full_name', 'N/A'), 'coaches': []}
                clients_data[client_id]['coaches'].append(f"{coach_info.get('full_name', 'Unknown')} ({rel.get('display_coach_type', 'Coach')})")
            return sorted(list(clients_data.values()), key=lambda x: x['full_name'])
        except requests.exceptions.RequestException as err:
            console.print(f"\n[bold red]Could not fetch clients:[/bold red] {err}")
            return []
