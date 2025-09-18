#!/usr/bin/env python3

# A script to provide a unified message and workout comment feed for a coach.
#
# Required libraries: requests, rich
# Install it by running: pip install requests rich

import requests
import getpass
import os
import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

# --- Configuration ---
API_BASE_URL = "https://app.turnkey.coach"
TOKEN_CACHE_FILE = ".tokencache"
CLIENT_DATA_DIR = os.path.expanduser("~/TurnkeyClients")

console = Console()

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

# --- New Functions for Unified Feed ---
def get_client_data_directory(client_id):
    """Creates and returns the path to a client's data directory."""
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    os.makedirs(client_dir, exist_ok=True)
    return client_dir

def download_workouts(token, client_id, client_dir):
    """
    Downloads all workouts for a client and caches them.
    This is a simplified version of your `workout_downloader.py`.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": client_id}
    url = f"{API_BASE_URL}/api/v1/workouts"
    
    with console.status(f"[bold green]Downloading workouts for client {client_id}...") as status:
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            workouts_data = response.json()
            
            # Cache the workouts in a file
            cache_file = os.path.join(client_dir, f"workouts_user_{client_id}.json")
            with open(cache_file, 'w') as f:
                json.dump(workouts_data, f, indent=4)
            console.print(f"Downloaded and cached {len(workouts_data)} workouts.", style="green")
            return workouts_data
        except requests.exceptions.RequestException as err:
            console.print(f"[bold red]Could not download workouts:[/bold red] {err}")
            return []

def get_client_messages(token, client_id):
    """Fetches all messages for a specific client from the API."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get all conversations for the current user (the coach)
    conversations_url = f"{API_BASE_URL}/api/v1/conversations"
    try:
        response = requests.get(conversations_url, headers=headers)
        response.raise_for_status()
        conversations = response.json().get("private_conversations", [])
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Could not fetch conversations:[/bold red] {err}")
        return None, []

    # 2. Find the correct conversation with the client
    conversation_id = None
    for convo in conversations:
        # Assuming direct client-coach conversations have a member count of 2
        if convo.get("member_count") == 2 and any(m.get('id') == client_id for m in convo.get('members_synopsis', [])):
            conversation_id = convo.get("id")
            break
    
    if not conversation_id:
        # Fallback to display_name match if members_synopsis is not present
        client_full_name = next((c.get('full_name') for c in get_clients(token, None) if c.get('id') == client_id), None)
        for convo in conversations:
             if convo.get("member_count") == 2 and convo.get("display_name") == client_full_name:
                conversation_id = convo.get("id")
                break
        if not conversation_id:
            console.print(f"\n[bold yellow]No private conversation found with client ID {client_id}.[/bold yellow]")
            return None, []


    # 3. Get all messages from that conversation
    messages_url = f"{API_BASE_URL}/api/v1/messages"
    params = {"conversation_id": conversation_id, "per_page": 100} # Get a reasonable number of messages
    try:
        response = requests.get(messages_url, headers=headers, params=params)
        response.raise_for_status()
        messages = response.json()
        return conversation_id, messages
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Could not fetch messages for conversation {conversation_id}:[/bold red] {err}")
        return conversation_id, []

def get_workout_comments(workouts_data):
    """
    Extracts all comments from a list of workouts.
    This simulates the logic from your other scripts.
    """
    comments = []
    for workout in workouts_data:
        workout_id = workout.get('id')
        workout_date = workout.get('workout_date')
        
        # Extract top-level workout comments
        for comment in workout.get('comments', []):
            comments.append({
                "type": "workout_comment",
                "content": comment.get('body'),
                "author": comment.get('user', {}).get('full_name'),
                "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                "parent_id": workout_id,
                "parent_type": "Workout"
            })
            
        # Extract comments on assigned exercises
        for exercise in workout.get('assigned_exercises', []):
            for comment in exercise.get('comments', []):
                comments.append({
                    "type": "workout_comment",
                    "content": comment.get('body'),
                    "author": comment.get('user', {}).get('full_name'),
                    "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                    "parent_id": exercise.get('id'),
                    "parent_type": "AssignedExercise"
                })
    return comments

def post_message(token, conversation_id, message_body):
    """Posts a new message to a conversation."""
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

def display_feed(feed, search_term=None):
    """Displays the unified feed with optional search highlighting."""
    clear_screen()
    console.print(Panel(f"[bold cyan]Unified Feed[/bold cyan]", expand=False))
    
    if not feed:
        console.print("[bold yellow]No activity found in the feed.[/bold yellow]")
        return
        
    for item in feed:
        content = item['content']
        if search_term and search_term.lower() in content.lower():
            # Highlight search term
            content = content.replace(search_term, f"[bold yellow]{search_term}[/bold yellow]", 1)
        
        item_text = Markdown(f"**[{item['type']}]** [dim]{item['timestamp'].strftime('%Y-%m-%d %H:%M')}[/dim] by [bold]{item['author']}[/bold]\n\n{content}")
        
        # Add a unique ID for replying to comments
        if item['type'] == 'workout_comment':
            panel_title = f"Comment ID: {item.get('comment_id', 'N/A')}"
            console.print(Panel(item_text, title=panel_title))
        else:
            console.print(Panel(item_text))

def interact_with_client_feed(token, client, client_dir):
    """Main interactive loop for a single client's feed."""
    client_name = client.get("full_name")
    client_id = client.get("id")
    
    # Get and cache data
    with console.status("[bold green]Fetching data...") as status:
        workouts = download_workouts(token, client_id, client_dir)
        conversation_id, messages = get_client_messages(token, client_id)
    
    if not workouts and not messages:
        console.print("\n[bold yellow]No data found for this client.[/bold yellow]")
        input("\nPress Enter to return to client list.")
        return

    # Aggregate all messages and comments
    all_events = []
    
    # Process messages
    for msg in messages:
        all_events.append({
            "type": "message",
            "content": msg.get('body'),
            "author": msg.get('user', {}).get('full_name'),
            "timestamp": datetime.fromisoformat(msg.get('created_at').replace('Z', '+00:00')),
            "conversation_id": conversation_id,
        })
        
    # Process workout comments and assign unique IDs for replying
    comments = get_workout_comments(workouts)
    for i, comment in enumerate(comments):
        comment['comment_id'] = f"{comment['parent_type']}-{comment['parent_id']}-{i}"
        all_events.append(comment)

    # Sort everything chronologically
    all_events.sort(key=lambda x: x['timestamp'])

    search_query = None
    while True:
        display_feed(all_events, search_term=search_query)
        
        console.print("\n" + "-"*50)
        console.print("[bold]Options:[/bold] \n[bold]m <text>[/bold] - Send a message\n[bold]c <ID> <text>[/bold] - Reply to a workout comment by ID\n[bold]/<query>[/bold] - Search feed\n[bold]q[/bold] - Quit to client list")
        
        try:
            command_line = console.input("[bold]>[/bold] ")
            parts = command_line.split(maxsplit=1)
            command = parts[0].lower() if parts else ""
            
            if command == 'q':
                break
            elif command == 'm':
                if len(parts) > 1:
                    post_message(token, conversation_id, parts[1])
                    # Refresh the feed after sending a message
                    messages = get_client_messages(token, client_id)[1]
                    all_events = [] # A new event list, including new messages, needs to be created
                    for msg in messages:
                        all_events.append({
                            "type": "message",
                            "content": msg.get('body'),
                            "author": msg.get('user', {}).get('full_name'),
                            "timestamp": datetime.fromisoformat(msg.get('created_at').replace('Z', '+00:00')),
                            "conversation_id": conversation_id,
                        })
                    comments = get_workout_comments(workouts)
                    for i, comment in enumerate(comments):
                        comment['comment_id'] = f"{comment['parent_type']}-{comment['parent_id']}-{i}"
                        all_events.append(comment)
                    all_events.sort(key=lambda x: x['timestamp'])
                else:
                    console.print("[bold red]Please provide a message body.[/bold red]")
            elif command == 'c':
                if len(parts) > 1:
                    comment_id_parts = parts[1].split(maxsplit=1)
                    if len(comment_id_parts) == 2:
                        id_parts = comment_id_parts[0].split('-')
                        parent_type = id_parts[0]
                        parent_id = int(id_parts[1])
                        reply_text = comment_id_parts[1]
                        
                        post_workout_comment(token, parent_id, parent_type, reply_text)
                        # Refresh the feed with the new comment
                        workouts = download_workouts(token, client_id, client_dir)
                        # The rest of the refresh logic would go here, similar to the 'm' command.
                    else:
                        console.print("[bold red]Invalid comment ID or format. Use 'c <ID> <text>'.[/bold red]")
                else:
                    console.print("[bold red]Please provide a comment ID and text.[/bold red]")
            elif command.startswith('/'):
                search_query = command[1:]
            else:
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
                interact_with_client_feed(token, selected_client, client_dir)
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

