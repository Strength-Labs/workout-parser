#!/usr/bin/env python3

# A script to provide a unified message and workout comment feed for a coach.
#
# Required libraries: requests, rich
# Install it by running: pip install requests rich

import requests
import getpass
import os
import json
import re
import html 
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# --- Configuration ---
API_BASE_URL = "https://app.turnkey.coach"
TOKEN_CACHE_FILE = ".tokencache"
CLIENT_DATA_DIR = os.path.expanduser("~/TurnkeyClients")

console = Console()

# --- HELPER FUNCTION ---
def clean_text(raw_html):
    """
    Strips HTML tags, unescapes entities, and preserves line breaks.
    """
    if not raw_html:
        return ""
    
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</p>|</div>', '\n', text, flags=re.IGNORECASE)
    text = html.unescape(text)
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

# --- Authentication and Caching Functions ---
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

    console.print("Attempting to get new access token...", style="yellow")
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
            console.print("[bold red]Authentication failed:[/bold red] Token or User ID missing in response.")
            return None, None
    except requests.exceptions.HTTPError as e:
        console.print(f"\n[bold red]Login failed.[/bold red] The server responded with status {e.response.status_code}.")
        console.print(f"[red]Server message:[/red] {e.response.text}")
        return None, None
    except requests.exceptions.RequestException as e:
        console.print(f"\n[bold red]A network error occurred during authentication:[/bold red] {e}")
        return None, None

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
        console.print(f"\n[bold red]Could not fetch clients:[/bold red] {err}")
        return []

# --- Data Fetching Functions ---
def get_client_data_directory(client_id):
    """Creates and returns the path to a client's data directory."""
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    os.makedirs(client_dir, exist_ok=True)
    return client_dir

def download_workouts(token, client_id, client_dir):
    """
    Downloads full workout details for a client, including comments.
    """
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    
    with console.status(f"[bold green]Downloading workouts for client {client_id}...") as status:
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
                else:
                    console.print(f"[yellow]Warning: Could not fetch details for workout {workout_id}[/yellow]")

            cache_file = os.path.join(client_dir, f"workouts_user_{client_id}.json")
            with open(cache_file, 'w') as f:
                json.dump(detailed_workouts, f, indent=4)
            console.print(f"Downloaded and cached {len(detailed_workouts)} workouts.", style="green")
            return detailed_workouts
        except requests.exceptions.RequestException as err:
            console.print(f"[bold red]Could not download workouts:[/bold red] {err}")
            return []

def get_client_messages(token, client_id, client):
    """
    Fetches the full conversation for a specific client from the API.
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    conversations_url = f"{API_BASE_URL}/api/v1/conversations"
    try:
        response = requests.get(conversations_url, headers=headers)
        response.raise_for_status()
        conversations = response.json().get("private_conversations", [])
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Could not fetch conversations:[/bold red] {err}")
        return None, []

    conversation_id = None
    client_full_name = client.get("full_name")
    for convo in conversations:
        if convo.get("member_count") == 2 and convo.get("display_name") == client_full_name:
            conversation_id = convo.get("id")
            break
    if not conversation_id:
        console.print(f"\n[bold yellow]No private conversation found with client {client_full_name}.[/bold yellow]")
        return None, []

    messages_url = f"{API_BASE_URL}/api/v1/messages"
    params = {"conversation_id": conversation_id, "per_page": 100}
    try:
        response = requests.get(messages_url, headers=headers, params=params)
        response.raise_for_status()
        return conversation_id, response.json()
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Could not fetch messages for conversation {conversation_id}:[/bold red] {err}")
        return conversation_id, []


def get_workout_comments(workouts_data):
    """
    Extracts all comments from a list of detailed workout objects.
    """
    comments = []
    for workout in workouts_data:
        workout_id = workout.get('id')
        for i, comment in enumerate(workout.get('comments', [])):
            comments.append({
                "type": "workout_comment",
                "content": comment.get('body'),
                "author_id": comment.get('user', {}).get('id'),
                "author": comment.get('user', {}).get('full_name'),
                "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                "parent_id": workout_id,
                "parent_type": "Workout",
                "comment_id": f"Workout-{workout_id}-{i}"
            })
        for exercise in workout.get('assigned_exercises', []):
            for i, comment in enumerate(exercise.get('comments', [])):
                comments.append({
                    "type": "workout_comment",
                    "content": comment.get('body'),
                    "author_id": comment.get('user', {}).get('id'),
                    "author": comment.get('user', {}).get('full_name'),
                    "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                    "parent_id": exercise.get('id'),
                    "parent_type": "AssignedExercise",
                    "comment_id": f"AssignedExercise-{exercise.get('id')}-{i}"
                })
    return comments

# --- API Posting Functions ---
def post_message(token, conversation_id, message_body):
    """Posts a new message to a conversation."""
    if not conversation_id:
        console.print("\n[bold red]Cannot send message: Conversation ID is missing.[/bold red]")
        return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/messages"
    payload = {"conversation_id": conversation_id, "body": message_body}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        console.print("\n[bold green]Message sent successfully![/bold green]")
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to send message:[/bold red] {err}")

def post_workout_comment(token, parent_id, parent_type, comment_body):
    """Posts a new comment to a workout or assigned exercise."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/comments"
    params = {"parent_type": parent_type, "parent_id": parent_id}
    payload = {"body": comment_body}
    try:
        response = requests.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        console.print("\n[bold green]Comment posted successfully![/bold green]")
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to post comment:[/bold red] {err}")

# --- Display and Main Loop ---
def display_feed(feed, coach_user_id, search_term=None):
    """Displays the unified feed with styling for search, coach, and comment IDs."""
    clear_screen()
    console.print(Panel(f"[bold cyan]Unified Feed[/bold cyan]", expand=False))
    
    if not feed:
        console.print("[bold yellow]No activity found in the feed.[/bold yellow]")
        return
        
    for item in feed:
        cleaned_content = clean_text(item.get('content') or "")
        display_text = cleaned_content or "[dim]Message body is empty.[/dim]"

        if search_term and search_term.lower() in cleaned_content.lower():
            display_text = re.sub(f'({re.escape(search_term)})', r'[bold yellow]\1[/bold yellow]', display_text, flags=re.IGNORECASE)
        
        is_coach = (item.get('author_id') == coach_user_id)
        border_style = "blue" if is_coach else "default"
        
        # Add a visual indicator for the coach's posts
        if is_coach:
            display_text = f"[blue]>>>[/blue] {display_text}"

        item_type = item['type']
        type_style = "bold yellow" if item_type == 'workout_comment' else "bold"

        title_text = Text()
        title_text.append(f"[{item_type}] ", style=type_style)
        title_text.append(f"{item['timestamp'].strftime('%Y-%m-%d %H:%M')} ", style="dim")
        title_text.append(f"by {item['author']}", style="bold")
        
        subtitle = None
        if item['type'] == 'workout_comment':
            alias_id = item.get('alias_id')
            subtitle = Text()
            subtitle.append("Reply with: ", style="dim")
            subtitle.append(f"c {alias_id}", style="bold cyan")

        console.print(Panel(display_text, title=title_text, subtitle=subtitle, border_style=border_style, padding=(0, 1)))


def fetch_and_aggregate_data(token, client, client_dir):
    """Fetches, aggregates, sorts, and prepares all data for display."""
    client_id = client.get("id")
    with console.status("[bold green]Fetching data...") as status:
        workouts = download_workouts(token, client_id, client_dir)
        conversation_id, messages = get_client_messages(token, client_id, client)
    
    if not workouts and (not messages):
        console.print("\n[bold yellow]No data found for this client.[/bold yellow]")
        input("\nPress Enter to return to client list.")
        return None, None, None
        
    all_events = []
    if messages:
        for msg in messages:
            ts_str = msg.get('created_at')
            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00')) if 'Z' in ts_str else datetime.fromisoformat(ts_str)
            all_events.append({
                "type": "message",
                "content": msg.get('body'),
                "author_id": msg.get('user', {}).get('id'),
                "author": msg.get('user', {}).get('full_name'),
                "timestamp": timestamp,
            })
        
    all_events.extend(get_workout_comments(workouts))
    all_events.sort(key=lambda x: x['timestamp'])
    
    comment_alias_map = {}
    alias_counter = 1
    for item in reversed(all_events):
        if item['type'] == 'workout_comment':
            alias = str(alias_counter)
            item['alias_id'] = alias
            comment_alias_map[alias] = item['comment_id']
            alias_counter += 1
            
    return all_events, conversation_id, comment_alias_map

def interact_with_client_feed(token, coach_user_id, client, client_dir):
    """Main interactive loop for a single client's feed."""
    all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
    if not all_events:
        return

    search_query = None
    while True:
        display_feed(all_events, coach_user_id, search_term=search_query)
        
        console.print("\n" + "-"*50)
        console.print("[bold]Options:[/bold] \n[bold]m <text>[/bold] - Send a message\n[bold]c <ID>[/bold] - Reply to a workout comment by alias ID\n[bold]/<query>[/bold] - Search feed\n[bold]q[/bold] - Quit to client list\n[bold]u[/bold] - Update feed")
        
        try:
            command_line = console.input("[bold]>[/bold] ")
            parts = command_line.split(maxsplit=1)
            command = parts[0].lower() if parts else ""
            
            if command == 'q':
                break
            elif command == 'u':
                all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
                if not all_events: break
            elif command == 'm':
                if len(parts) > 1:
                    post_message(token, conversation_id, parts[1])
                    all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
                    if not all_events: break
                else:
                    console.print("[bold red]Please provide a message body.[/bold red]")
            elif command == 'c':
                if len(parts) > 1:
                    comment_id_parts = parts[1].split(maxsplit=1)
                    if len(comment_id_parts) == 2:
                        alias_str = comment_id_parts[0]
                        reply_text = comment_id_parts[1]
                        
                        real_id_str = comment_alias_map.get(alias_str)
                        if not real_id_str:
                            console.print("[bold red]Invalid comment alias ID.[/bold red]")
                            continue

                        target_event = next((e for e in all_events if e.get('comment_id') == real_id_str), None)
                        
                        if target_event:
                            post_workout_comment(token, target_event['parent_id'], target_event['parent_type'], reply_text)
                            all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
                            if not all_events: break
                        else:
                            console.print("[bold red]Internal error: Could not find comment for alias.[/bold red]")
                    else:
                        console.print("[bold red]Invalid format. Use 'c <ID> <text>'.[/bold red]")
                else:
                    console.print("[bold red]Please provide a comment alias ID and text.[/bold red]")
            elif command.startswith('/'):
                search_query = command[1:].strip()
            else:
                search_query = None
                console.print("[bold red]Invalid command.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


def client_selection_loop(token, user_id):
    """The main application loop for selecting clients."""
    while True:
        clear_screen()
        clients = get_clients(token, user_id)
        if not clients:
            console.print("[bold red]No clients found or could not fetch client list. Exiting.[/bold red]")
            break

        console.print(Panel("[bold]--- Select a Client ---[/bold]", expand=False))
        for i, client in enumerate(clients):
            first_name = client.get('first_name', 'N/A')
            last_name = client.get('last_name', 'N/A')
            console.print(f"{i + 1:2d}. [bold]{first_name} {last_name}[/bold]")
        console.print("\n[bold yellow]Enter a number to select a client, or 'q' to quit.[/bold yellow]")
        
        choice = console.input("> ")
        if choice.lower() == 'q':
            break

        try:
            client_index = int(choice) - 1
            if 0 <= client_index < len(clients):
                selected_client = clients[client_index]
                client_id = selected_client.get('id')
                client_dir = get_client_data_directory(client_id)
                console.print(f"Client directory set to: {client_dir}", style="dim")
                interact_with_client_feed(token, user_id, selected_client, client_dir)
            else:
                console.print("[bold red]Invalid number. Press Enter to try again...[/bold red]")
                input()
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a number. Press Enter to try again...[/bold red]")
            input()

if __name__ == "__main__":
    clear_screen()
    console.print(Panel("[bold blue]--- Turnkey Coach Unified Feed ---[/bold blue]", expand=False))
    
    access_token, coach_user_id = get_access_token()

    if access_token and coach_user_id:
        client_selection_loop(access_token, coach_user_id)
    
    console.print("\nExiting. Goodbye!", style="dim")
