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

def _get_workout_ids_from_api(token, client_id):
    """Lightweight function to get only workout IDs from server for sync comparison."""
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    
    try:
        response = requests.get(list_url, headers=headers, params=params)
        response.raise_for_status()
        workouts_summary = response.json()
        return {summary['id'] for summary in workouts_summary}  # Return set of IDs
    except requests.exceptions.RequestException:
        return set()

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

def _download_workouts_from_api_headless(token, client_id, start_date=None):
    """Headless version of _download_workouts_from_api - no Rich console output"""
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    if start_date:
        params["start_date"] = start_date
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
    """Get workout history with intelligent caching, deletion detection, and incremental updates."""
    client_id = client["id"]
    client_dir = get_client_dir(client_id)
    workout_cache_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    os.makedirs(client_dir, exist_ok=True)
    
    # Force refresh - download everything fresh
    if force_refresh:
        workouts = _download_workouts_from_api(token, client_id)
        safe_json_dump(workouts, workout_cache_path, indent=4)
        return workouts
    
    # No cache file - do initial download
    if not os.path.exists(workout_cache_path):
        return get_workout_history(token, client, force_refresh=True)
    
    # Load existing cache
    existing_workouts = safe_json_load(workout_cache_path, default=[])
    if not existing_workouts:
        console.print("[yellow]Cached workout file is empty, downloading fresh data...[/yellow]")
        return get_workout_history(token, client, force_refresh=True)
    
    # Filter for valid workouts
    valid_workouts = [w for w in existing_workouts if w.get('workout_date') and w.get('id')]
    if not valid_workouts:
        console.print("[yellow]No valid workouts in cache, downloading fresh data...[/yellow]")
        return get_workout_history(token, client, force_refresh=True)
    
    # Smart sync: Compare IDs to detect deletions and additions
    with console.status("[dim]Checking for workout changes...[/dim]"):
        server_workout_ids = _get_workout_ids_from_api(token, client_id)
        if not server_workout_ids:  # API error - use cached data
            console.print("[yellow]Could not fetch server workout list. Using cached data.[/yellow]")
            return existing_workouts
        
        cached_workout_ids = {w['id'] for w in valid_workouts}
        
        # Detect deletions
        deleted_ids = cached_workout_ids - server_workout_ids
        if deleted_ids:
            console.print(f"[yellow]Detected {len(deleted_ids)} deleted workout(s). Removing from cache...[/yellow]")
            valid_workouts = [w for w in valid_workouts if w['id'] not in deleted_ids]
        
        # Detect new workouts that need to be fetched
        missing_ids = server_workout_ids - cached_workout_ids
        
        if missing_ids:
            console.print(f"[green]Found {len(missing_ids)} new workout(s). Downloading details...[/green]")
            # For new workouts, we need to fetch full details
            # Get the latest date from remaining cached workouts to optimize the API call
            if valid_workouts:
                latest_date_str = max(w['workout_date'] for w in valid_workouts)
                start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)
                new_workouts = _download_workouts_from_api(token, client_id, start_date=start_date.isoformat())
            else:
                # No cached workouts left, download everything
                new_workouts = _download_workouts_from_api(token, client_id)
            
            # Combine and save
            all_workouts = valid_workouts + new_workouts
            safe_json_dump(all_workouts, workout_cache_path, indent=4)
            return all_workouts
        elif deleted_ids:
            # Only deletions occurred, save the cleaned cache
            safe_json_dump(valid_workouts, workout_cache_path, indent=4)
            return valid_workouts
        else:
            # No changes detected
            console.print("[dim]Workout history is up to date.[/dim]")
            return existing_workouts

def get_workout_history_headless(token, client, force_refresh=False):
    """Headless version of get_workout_history for bulk operations - no Rich console output"""
    client_id = client["id"]
    client_dir = get_client_dir(client_id)
    workout_cache_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    os.makedirs(client_dir, exist_ok=True)
    
    # Force refresh - download everything fresh
    if force_refresh:
        workouts = _download_workouts_from_api_headless(token, client_id)
        safe_json_dump(workouts, workout_cache_path, indent=4)
        return workouts
    
    # No cache file - do initial download
    if not os.path.exists(workout_cache_path):
        return get_workout_history_headless(token, client, force_refresh=True)
    
    # Load existing cache
    existing_workouts = safe_json_load(workout_cache_path, default=[])
    if not existing_workouts:
        return get_workout_history_headless(token, client, force_refresh=True)
    
    # Filter for valid workouts
    valid_workouts = [w for w in existing_workouts if w.get('workout_date') and w.get('id')]
    if not valid_workouts:
        return get_workout_history_headless(token, client, force_refresh=True)
    
    # Smart sync: Compare IDs to detect deletions and additions (no status display)
    server_workout_ids = _get_workout_ids_from_api(token, client_id)
    if not server_workout_ids:  # API error - use cached data
        return existing_workouts
    
    cached_workout_ids = {w['id'] for w in valid_workouts}
    
    # Detect deletions
    deleted_ids = cached_workout_ids - server_workout_ids
    if deleted_ids:
        valid_workouts = [w for w in valid_workouts if w['id'] not in deleted_ids]
    
    # Detect new workouts that need to be fetched
    missing_ids = server_workout_ids - cached_workout_ids
    
    if missing_ids:
        # For new workouts, we need to fetch full details
        # Get the latest date from remaining cached workouts to optimize the API call
        if valid_workouts:
            latest_date_str = max(w['workout_date'] for w in valid_workouts)
            start_date = datetime.fromisoformat(latest_date_str).date() + timedelta(days=1)
            new_workouts = _download_workouts_from_api_headless(token, client_id, start_date=start_date.isoformat())
        else:
            # No cached workouts left, download everything
            new_workouts = _download_workouts_from_api_headless(token, client_id)
        
        # Combine and save
        all_workouts = valid_workouts + new_workouts
        safe_json_dump(all_workouts, workout_cache_path, indent=4)
        return all_workouts
    elif deleted_ids:
        # Only deletions occurred, save the cleaned cache
        safe_json_dump(valid_workouts, workout_cache_path, indent=4)
        return valid_workouts
    else:
        # No changes detected
        return existing_workouts


def delete_workout_by_id(token, workout_id):
    """Delete a single workout by ID via the API.
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return True, None
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        if e.response.status_code == 422:
            try:
                error_data = e.response.json()
                if "Cannot delete a completed workout" in str(error_data):
                    error_msg = "Cannot delete completed workout"
                elif "not authorized" in str(error_data).lower():
                    error_msg = "Not authorized to delete this workout"
                else:
                    error_msg = f"Deletion failed: {error_data}"
            except:
                pass
        return False, error_msg
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {e}"


def delete_workouts_filtered(token, client_id, start_date=None, end_date=None, 
                            workout_types=None, dry_run=False):
    """Delete workouts matching the specified criteria.
    
    Args:
        token: API authentication token
        client_id: Client ID to delete workouts for
        start_date: Delete workouts on/after this date (YYYY-MM-DD) - None means no start limit
        end_date: Delete workouts on/before this date (YYYY-MM-DD) - None means no end limit
        workout_types: List of workout types to delete ['default', 'nutrition'] - None means all types
        dry_run: If True, only show what would be deleted without actually deleting
    
    Returns:
        dict: {
            'would_delete' or 'deleted': [list of workout info],
            'skipped': [list of skipped workout info with reasons],
            'errors': [list of error info],
            'total_matched': int
        }
    """
    from datetime import datetime
    
    # Get workouts from cache (uses intelligent caching system)
    try:
        # Create a minimal client object for get_workout_history
        client = {'id': client_id}
        workouts = get_workout_history_headless(token, client, force_refresh=False)
    except Exception as e:
        return {
            'would_delete' if dry_run else 'deleted': [],
            'skipped': [],
            'errors': [f"Failed to fetch workouts: {e}"],
            'total_matched': 0
        }
    
    if not workouts:
        return {
            'would_delete' if dry_run else 'deleted': [],
            'skipped': [],
            'errors': [],
            'total_matched': 0
        }
    
    # Filter workouts based on criteria
    matching_workouts = []
    
    for workout in workouts:
        workout_date_str = workout.get('workout_date')
        workout_type = workout.get('workout_type', 'default')
        workout_id = workout.get('id')
        
        if not workout_date_str or not workout_id:
            continue
            
        # Date filtering
        if start_date:
            if workout_date_str < start_date:
                continue
        
        if end_date:
            if workout_date_str > end_date:
                continue
                
        # Type filtering  
        if workout_types and workout_type not in workout_types:
            continue
            
        matching_workouts.append(workout)
    
    result = {
        'would_delete' if dry_run else 'deleted': [],
        'skipped': [],
        'errors': [],
        'total_matched': len(matching_workouts)
    }
    
    # Process each matching workout
    for workout in matching_workouts:
        workout_info = {
            'id': workout.get('id'),
            'date': workout.get('workout_date'),
            'type': workout.get('workout_type', 'default'),
            'title': workout.get('title', ''),
            'completed': workout.get('completed', False)
        }
        
        if dry_run:
            result['would_delete'].append(workout_info)
        else:
            # Check if workout is completed (cannot be deleted)
            if workout.get('completed', False):
                result['skipped'].append({
                    **workout_info,
                    'reason': 'Workout is completed and cannot be deleted'
                })
                continue
            
            # Attempt deletion
            success, error_msg = delete_workout_by_id(token, workout['id'])
            if success:
                result['deleted'].append(workout_info)
            else:
                result['errors'].append({
                    **workout_info,
                    'error': error_msg
                })
    
    return result

# --- (Authentication and get_clients functions remain the same) ---
def save_auth_data(token, user_id):
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {"token": token, "user_id": user_id, "expires_at": expires_at.isoformat()}
    token_cache_file = get_token_cache_file()
    # Ensure parent directory exists (first run on fresh systems)
    os.makedirs(os.path.dirname(token_cache_file), exist_ok=True)
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
                    clients_data[client_id] = {
                        'id': client_id, 
                        'full_name': client_info.get('full_name', 'N/A'), 
                        'coach_roles': {}  # Changed from 'coaches' list to 'coach_roles' dict
                    }
                
                # Group roles by coach name
                coach_name = coach_info.get('full_name', 'Unknown')
                coach_type = rel.get('display_coach_type', 'Coach')
                # Replace "Workout" with "Strength" for clearer naming
                if coach_type == 'Workout':
                    coach_type = 'Strength'
                
                if coach_name not in clients_data[client_id]['coach_roles']:
                    clients_data[client_id]['coach_roles'][coach_name] = []
                clients_data[client_id]['coach_roles'][coach_name].append(coach_type)
            
            # Convert coach_roles dict to coaches list with proper formatting
            for client_data in clients_data.values():
                coaches_list = []
                for coach_name, roles in client_data['coach_roles'].items():
                    # Sort roles for consistent display (Strength before Nutrition)
                    sorted_roles = sorted(roles)
                    roles_str = ', '.join(sorted_roles)
                    coaches_list.append(f"{coach_name} ({roles_str})")
                client_data['coaches'] = coaches_list
                # Clean up temporary coach_roles field
                del client_data['coach_roles']
            
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
        try:
            password = getpass.getpass("Enter your password: ")
        except Exception:
            console.print("[yellow]Could not securely hide password input on this terminal.[/yellow]")
            password = console.input("Password (visible): ")
    
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
