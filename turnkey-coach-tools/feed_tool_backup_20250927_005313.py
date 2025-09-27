import requests
import os
import json
import re
import html 
import threading
import copy
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import shared functions from the api_client.py file
from api_client import API_BASE_URL, CLIENT_DATA_DIR, clean_text, clear_screen

console = Console()

# --- Data Fetching Functions ---
def download_workouts(token, client_id, client_dir):
    """Downloads full workout details for a client, including comments."""
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    
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

        cache_file = os.path.join(client_dir, f"workouts_user_{client_id}.json")
        with open(cache_file, 'w') as f:
            json.dump(detailed_workouts, f, indent=4)
        return detailed_workouts
    except requests.exceptions.RequestException:
        return []

def get_client_messages(token, client_id, client_full_name):
    """Fetches the full conversation for a specific client from the API."""
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{API_BASE_URL}/api/v1/conversations"
    try:
        response = requests.get(conversations_url, headers=headers)
        response.raise_for_status()
        conversations = response.json().get("private_conversations", [])
    except requests.exceptions.RequestException:
        return None, []

    conversation_id = None
    for convo in conversations:
        if convo.get("member_count") == 2 and convo.get("display_name") == client_full_name:
            conversation_id = convo.get("id")
            break
    if not conversation_id:
        return None, []

    messages_url = f"{API_BASE_URL}/api/v1/messages"
    params = {"conversation_id": conversation_id, "per_page": 100}
    try:
        response = requests.get(messages_url, headers=headers, params=params)
        response.raise_for_status()
        return conversation_id, response.json()
    except requests.exceptions.RequestException:
        return conversation_id, []


def get_workout_comments(workouts_data):
    """Extracts all comments from a list of detailed workout objects."""
    comments = []
    if not workouts_data: return comments
    for workout in workouts_data:
        workout_id = workout.get('id')
        for i, comment in enumerate(workout.get('comments', [])):
            comments.append({
                "type": "workout_comment", "content": comment.get('body'),
                "author_id": comment.get('user', {}).get('id'), "author": comment.get('user', {}).get('full_name'),
                "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                "parent_id": workout_id, "parent_type": "Workout",
                "comment_id": f"Workout-{workout_id}-{i}"
            })
        for exercise in workout.get('assigned_exercises', []):
            for i, comment in enumerate(exercise.get('comments', [])):
                comments.append({
                    "type": "workout_comment", "content": comment.get('body'),
                    "author_id": comment.get('user', {}).get('id'), "author": comment.get('user', {}).get('full_name'),
                    "timestamp": datetime.fromisoformat(comment.get('updated_at').replace('Z', '+00:00')),
                    "parent_id": exercise.get('id'), "parent_type": "AssignedExercise",
                    "comment_id": f"AssignedExercise-{exercise.get('id')}-{i}"
                })
    return comments

def fetch_and_aggregate_data(token, client, feed_data_lock, feed_data):
    """
    Fetches all data from API and updates a shared dictionary.
    This function is designed to be run in a background thread.
    """
    client_id = client["id"]
    client_full_name = client["full_name"]
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    
    # Always download fresh workouts and messages for a refresh
    workouts = download_workouts(token, client_id, client_dir)
    conversation_id, messages = get_client_messages(token, client_id, client_full_name)

    if not workouts and not messages:
        with feed_data_lock:
            feed_data["is_refreshing"] = False
        return

    all_events = []
    if messages:
        for msg in messages:
            ts_str = msg.get('created_at')
            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00')) if 'Z' in ts_str else datetime.fromisoformat(ts_str)
            all_events.append({
                "type": "message", "content": msg.get('body'),
                "author_id": msg.get('user', {}).get('id'), "author": msg.get('user', {}).get('full_name'),
                "timestamp": timestamp,
            })
        
    all_events.extend(get_workout_comments(workouts))
    all_events.sort(key=lambda x: x['timestamp'])

    comment_alias_map = {}
    alias_counter = 1
    for item in reversed(all_events):
        if item['type'] == 'workout_comment':
            item['alias_id'] = str(alias_counter)
            comment_alias_map[str(alias_counter)] = item['comment_id']
            alias_counter += 1
            
    # Safely update the shared data structure
    with feed_data_lock:
        feed_data["events"] = all_events
        feed_data["conversation_id"] = conversation_id
        feed_data["alias_map"] = comment_alias_map
        feed_data["is_refreshing"] = False
        
    # Save the fresh data to the feed cache file
    cache_path = os.path.join(client_dir, "feed_cache.json")
    events_to_cache = [dict(event) for event in all_events]
    for event in events_to_cache:
        event['timestamp'] = event['timestamp'].isoformat()
    with open(cache_path, 'w') as f:
        json.dump({"events": events_to_cache, "conversation_id": conversation_id, "alias_map": comment_alias_map}, f)

# --- API Posting Functions ---
def post_message(token, conversation_id, message_body):
    """Posts a new message to a conversation."""
    if not conversation_id:
        console.print("\n[bold red]Cannot send message: Conversation ID is missing.[/bold red]")
        return False
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/messages"
    payload = {"conversation_id": conversation_id, "body": message_body}
    try:
        requests.post(url, headers=headers, json=payload).raise_for_status()
        console.print("\n[bold green]Message sent successfully![/bold green]")
        return True
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to send message:[/bold red] {err}")
        return False

def post_workout_comment(token, parent_id, parent_type, comment_body):
    """Posts a new comment to a workout or assigned exercise."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/comments"
    params = {"parent_type": parent_type, "parent_id": parent_id}
    payload = {"body": comment_body}
    try:
        requests.post(url, headers=headers, params=params, json=payload).raise_for_status()
        console.print("\n[bold green]Comment posted successfully![/bold green]")
        return True
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to post comment:[/bold red] {err}")
        return False

# --- Display and Main Loop ---
def display_feed(feed, coach_user_id, search_term=None, is_refreshing=False):
    """Displays the unified feed with styling and status."""
    clear_screen()
    title = "[bold cyan]Unified Feed[/bold cyan]"
    if is_refreshing:
        title += " [yellow](Refreshing...)[/yellow]"
    console.print(Panel(title, expand=False))
    
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

def run_feed(token, coach_user_id, client):
    """Main interactive loop for the Unified Feed tool with asynchronous caching."""
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client['id']))
    os.makedirs(client_dir, exist_ok=True)
    cache_path = os.path.join(client_dir, "feed_cache.json")

    feed_data = {"events": [], "conversation_id": None, "alias_map": {}, "is_refreshing": True}
    feed_data_lock = threading.Lock()

    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                feed_data["events"] = cached_data.get("events", [])
                for event in feed_data["events"]:
                    event['timestamp'] = datetime.fromisoformat(event['timestamp'])
                feed_data["conversation_id"] = cached_data.get("conversation_id")
                feed_data["alias_map"] = cached_data.get("alias_map", {})
        except (json.JSONDecodeError, KeyError):
            pass 
    
    refresh_thread = threading.Thread(target=fetch_and_aggregate_data, args=(token, client, feed_data_lock, feed_data))
    refresh_thread.start()

    search_query = None
    while True:
        with feed_data_lock:
            display_data = copy.deepcopy(feed_data)
        
        display_feed(display_data["events"], coach_user_id, search_query, display_data["is_refreshing"])
        
        if not display_data["is_refreshing"] and refresh_thread.is_alive():
             refresh_thread.join(timeout=0.1) 

        if not display_data["is_refreshing"]:
            console.print("\n" + "-"*50)
            console.print("[bold]Options:[/bold] \n[bold]m <text>[/bold] - Send message\n[bold]c <ID> <text>[/bold] - Reply to comment\n[bold]/<query>[/bold] - Search\n[bold]u[/bold] - Force refresh\n[bold]q[/bold] - Back to tool menu")
            command_line = console.input("[bold]>[/bold] ")
        else:
            command_line = console.input("\n[dim]Feed is refreshing... ('q' to go back)[/dim]\n> ")

        parts = command_line.split(maxsplit=1)
        command = parts[0].lower() if parts else ""
        
        if command == 'q':
            if refresh_thread.is_alive():
                console.print("[yellow]Waiting for background refresh to finish before exiting...[/yellow]")
                refresh_thread.join()
            break
        
        if display_data["is_refreshing"]:
            continue

        should_refresh = False
        if command == 'u':
            should_refresh = True
        elif command == 'm':
            if len(parts) > 1 and post_message(token, display_data["conversation_id"], parts[1]):
                should_refresh = True
        elif command == 'c':
            if len(parts) > 1:
                comment_id_parts = parts[1].split(maxsplit=1)
                if len(comment_id_parts) == 2:
                    real_id_str = display_data["alias_map"].get(comment_id_parts[0])
                    target_event = next((e for e in display_data["events"] if e.get('comment_id') == real_id_str), None) if real_id_str else None
                    if target_event and post_workout_comment(token, target_event['parent_id'], target_event['parent_type'], comment_id_parts[1]):
                        should_refresh = True
        elif command.startswith('/'):
            search_query = command[1:].strip()
        else:
            search_query = None

        if should_refresh and not refresh_thread.is_alive():
            with feed_data_lock:
                feed_data["is_refreshing"] = True
            refresh_thread = threading.Thread(target=fetch_and_aggregate_data, args=(token, client, feed_data_lock, feed_data))
            refresh_thread.start()
