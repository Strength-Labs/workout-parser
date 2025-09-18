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
console = Console()

# --- Shared Helper Function ---
def clean_text(raw_html):
    """Strips HTML tags, unescapes entities, and preserves line breaks."""
    if not raw_html:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</p>|</div>', '\n', text, flags=re.IGNORECASE)
    text = html.unescape(text)
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

# --- Authentication ---
def save_auth_data(token, user_id):
    """Saves the access token, user ID, and expiration date to a cache file."""
    expires_at = datetime.now() + timedelta(hours=1)
    auth_data = {"token": token, "user_id": user_id, "expires_at": expires_at.isoformat()}
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
    """Authenticates with the API to get an access token and user ID."""
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
            token = data.get("token")
            user_id = data.get("resource_owner", {}).get("id")
            if token and user_id:
                console.print("Successfully obtained new access token. 🎉", style="green")
                save_auth_data(token, user_id)
                return token, user_id
            else:
                return None, None
        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold red]Login failed:[/bold red] {e}")
            return None, None

def get_clients(token, user_id):
    """Fetches a de-duplicated list of clients and their coaches."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/users/{user_id}/clients"
    
    with console.status("Fetching client list..."):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            relationships = response.json()
            clients_data = {}
            for rel in relationships:
                client_info = rel.get('client')
                coach_info = rel.get('coach')
                if not client_info or not coach_info: continue
                client_id = client_info.get('id')
                if client_id not in clients_data:
                    clients_data[client_id] = {
                        'id': client_id,
                        'full_name': client_info.get('full_name', 'N/A'),
                        'coaches': []
                    }
                coach_name = coach_info.get('full_name', 'Unknown')
                coach_type = rel.get('display_coach_type', 'Coach')
                clients_data[client_id]['coaches'].append(f"{coach_name} ({coach_type})")
            return sorted(list(clients_data.values()), key=lambda x: x['full_name'])
        except requests.exceptions.RequestException as err:
            console.print(f"\n[bold red]Could not fetch clients:[/bold red] {err}")
            return []
