import requests
import getpass
import os
import json
import re
import html
from datetime import datetime, timedelta
from rich.console import Console
from settings import get_stored_credentials # for login ease
from directory_migration import get_client_dir, get_shared_dir, perform_migration, needs_migration
from encoding_utils import safe_open, safe_json_dump, safe_json_load


# --- Configuration ---
API_BASE_URL = "https://app.turnkey.coach"
console = Console()

# Directory paths (now managed by migration module)
def get_token_cache_file():
    return os.path.join(get_shared_dir(), '.tokencache')

def get_exercise_list_file():
    return os.path.join(get_shared_dir(), 'exerciselist.json')

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
    """Loads exerciselist.json and creates a name-to-ID mapping with exercise types.

    Returns dict with structure: {exercise_name_lower: {'id': id, 'type': exercise_type}}
    """
    try:
        filepath = get_exercise_list_file()
        exercises = safe_json_load(filepath)
        if exercises is None:
            raise FileNotFoundError()
        return {ex['name'].lower(): {'id': ex['id'], 'type': ex.get('exercise_type', 'resistance')} for ex in exercises}
    except FileNotFoundError:
        console.print("[bold red]Error: `exerciselist.json` not found.[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error loading exercise list: {e}[/bold red]")
        return None

def get_exercise_id(exercise_map, exercise_name):
    """Safely retrieve an exercise ID from the cached exercise map."""
    if not exercise_map or not exercise_name:
        return None
    entry = exercise_map.get(exercise_name.strip().lower())
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("id")
    return entry

def get_exercise_type(exercise_map, exercise_name, default="resistance"):
    """Safely retrieve the exercise_type for an exercise name."""
    if not exercise_map or not exercise_name:
        return default
    entry = exercise_map.get(exercise_name.strip().lower())
    if isinstance(entry, dict):
        return entry.get("type", default)
    return default

def update_exercise_list(token):
    """Fetches the latest exercise list from the API and saves it to exerciselist.json."""
    url = f"{API_BASE_URL}/api/v1/exercises"
    headers = {"Authorization": f"Bearer {token}"}
    filepath = get_exercise_list_file()

    with console.status("[bold green]Downloading latest exercise list...[/bold green]"):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            exercises = response.json()
            safe_json_dump(exercises, filepath)
            console.print(f"✅ [green]Successfully saved {len(exercises)} exercises to {filepath}[/green]")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"❌ [red]Error fetching exercises: {e}[/red]")
            return False


def fetch_metric_catalog(token):
    """Retrieve the global list of available metric definitions."""
    url = f"{API_BASE_URL}/api/v1/metrics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        console.print(f"[bold red]Error fetching metric catalog:[/bold red] {err}")
        return []

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
    """Get workout history with intelligent caching and incremental updates."""
    client_id = client["id"]
    client_dir = get_client_dir(client_id)
    workout_cache_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    os.makedirs(client_dir, exist_ok=True)
    if force_refresh:
        workouts = _download_workouts_from_api(token, client_id)
        safe_json_dump(workouts, workout_cache_path, indent=4)
        return workouts
    if os.path.exists(workout_cache_path):
        existing_workouts = safe_json_load(workout_cache_path, default=[])
        if not existing_workouts:
            console.print("[yellow]Cached workout file is empty, downloading fresh data...[/yellow]")
            return get_workout_history(token, client, force_refresh=True)
        valid_workouts = [w for w in existing_workouts if w.get('workout_date')]
        if not valid_workouts:
            console.print("[yellow]No valid workouts in cache, downloading fresh data...[/yellow]")
            return get_workout_history(token, client, force_refresh=True)
        latest_date_str = max(w['workout_date'] for w in valid_workouts)
        start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)
        new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())
        if new_workouts:
            console.print(f"[green]Found {len(new_workouts)} new workouts. Updating cache...[/green]")
            all_workouts = existing_workouts + new_workouts
            safe_json_dump(all_workouts, workout_cache_path, indent=4)
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
    token_cache_file = get_token_cache_file()
    safe_json_dump(auth_data, token_cache_file)

def load_auth_data():
    token_cache_file = get_token_cache_file()
    if not os.path.exists(token_cache_file): return None, None
    data = safe_json_load(token_cache_file)
    if data:
        try:
            if datetime.fromisoformat(data.get("expires_at")) > datetime.now():
                return data.get("token"), data.get("user_id")
        except (KeyError, TypeError, ValueError): pass
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


def get_user_profile(token, user_id):
    """Get user profile information from workspace settings."""
    try:
        from settings import get_current_workspace
        
        current_workspace = get_current_workspace()
        if current_workspace:
            return {
                'user_id': user_id,
                'email': current_workspace.get('email'),
                'company_name': current_workspace.get('company_name'),
                'relationships': []
            }
    except Exception:
        pass
    
    # Fallback - return basic profile with user ID
    return {
        'user_id': user_id,
        'email': None,
        'company_name': None,
        'relationships': []
    }

def get_access_token():
    token, user_id = load_auth_data()
    if token and user_id:
        console.print("Using cached access token. 👍", style="green")
        return token, user_id
    
    # Try stored credentials for auto-login
    email, password = get_stored_credentials()
    if email and password:
        console.print("[dim]Auto-logging in with stored credentials...[/dim]")
    else:
        # Fallback to manual prompt
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
                console.print("Successfully obtained access token. 🎉", style="green")
                save_auth_data(token, user_id)
                return token, user_id
        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Login failed:[/bold red] {e}")
            return None, None

def sanitize_workspace_name(company_name):
    """Convert company name to a safe directory name."""
    if not company_name:
        return "default"
    
    # Remove/replace unsafe characters and convert to lowercase
    safe_name = company_name.lower()
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '-' for c in safe_name)
    # Remove multiple consecutive dashes and trim
    safe_name = '-'.join(filter(None, safe_name.split('-')))
    return safe_name or "default"
