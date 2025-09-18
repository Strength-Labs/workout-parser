import requests
import os
import json
import re
import html 
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import shared functions from the api_client.py file
from api_client import API_BASE_URL

console = Console()

# --- HELPER FUNCTION ---
def clean_text(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</p>|</div>', '\n', text, flags=re.IGNORECASE)
    text = html.unescape(text)
    cleanr = re.compile('<.*?>')
    text = re.sub(cleanr, '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

# --- Data Fetching Functions ---
def download_workouts(token, client_id, client_dir):
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
            return detailed_workouts
        except requests.exceptions.RequestException as err:
            console.print(f"[bold red]Could not download workouts:[/bold red] {err}")
            return []

def get_client_messages(token, client_id, client_full_name):
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{API_BASE_URL}/api/v1/conversations"
    try:
        response = requests.get(conversations_url, headers=headers)
        response.raise_for_status()
        conversations = response.json().get("private_conversations", [])
    except requests.exceptions.RequestException as err:
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
    except requests.exceptions.RequestException as err:
        return conversation_id, []

def get_workout_comments(workouts_data):
    comments = []
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

def post_message(token, conversation_id, message_body):
    if not conversation_id: return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/messages"
    payload = {"conversation_id": conversation_id, "body": message_body}
    try:
        requests.post(url, headers=headers, json=payload).raise_for_status()
        console.print("\n[bold green]Message sent successfully![/bold green]")
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to send message:[/bold red] {err}")

def post_workout_comment(token, parent_id, parent_type, comment_body):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/api/v1/comments"
    params = {"parent_type": parent_type, "parent_id": parent_id}
    payload = {"body": comment_body}
    try:
        requests.post(url, headers=headers, params=params, json=payload).raise_for_status()
        console.print("\n[bold green]Comment posted successfully![/bold green]")
    except requests.exceptions.RequestException as err:
        console.print(f"\n[bold red]Failed to post comment:[/bold red] {err}")

# --- Display and Main Loop ---
def display_feed(feed, coach_user_id, search_term=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Panel(f"[bold cyan]Unified Feed[/bold cyan]", expand=False))
    if not feed:
        console.print("[bold yellow]No activity found.[/bold yellow]")
        return
        
    for item in feed:
        cleaned_content = clean_text(item.get('content') or "")
        display_text = cleaned_content or "[dim]Message body is empty.[/dim]"

        if search_term:
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

def fetch_and_aggregate_data(token, client, client_dir):
    client_id = client["id"]
    client_full_name = client["full_name"]
    with console.status("[bold green]Fetching data...") as status:
        workouts = download_workouts(token, client_id, client_dir)
        conversation_id, messages = get_client_messages(token, client_id, client_full_name)
    
    if not workouts and not messages:
        return None, None, None
        
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
            
    return all_events, conversation_id, comment_alias_map

def run_feed(token, coach_user_id, client):
    """The main interactive loop for the Unified Feed tool."""
    client_dir = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client["id"]))
    os.makedirs(client_dir, exist_ok=True)
    
    all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
    if not all_events:
        console.print("[bold yellow]No data found for this client.[/bold yellow]")
        console.input("\nPress Enter to continue...")
        return

    search_query = None
    while True:
        display_feed(all_events, coach_user_id, search_term=search_query)
        
        console.print("\n" + "-"*50)
        console.print("[bold]Options:[/bold] \n[bold]m <text>[/bold] - Send message\n[bold]c <ID> <text>[/bold] - Reply to comment\n[bold]/<query>[/bold] - Search\n[bold]u[/bold] - Update\n[bold]q[/bold] - Back to tool menu")
        
        try:
            command_line = console.input("[bold]>[/bold] ")
            parts = command_line.split(maxsplit=1)
            command = parts[0].lower() if parts else ""
            
            if command == 'q':
                break
            elif command == 'u':
                all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
            elif command == 'm':
                if len(parts) > 1: post_message(token, conversation_id, parts[1])
                all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
            elif command == 'c':
                if len(parts) > 1:
                    comment_id_parts = parts[1].split(maxsplit=1)
                    if len(comment_id_parts) == 2:
                        real_id_str = comment_alias_map.get(comment_id_parts[0])
                        if not real_id_str:
                            console.print("[bold red]Invalid comment alias ID.[/bold red]")
                            continue
                        target_event = next((e for e in all_events if e.get('comment_id') == real_id_str), None)
                        if target_event:
                            post_workout_comment(token, target_event['parent_id'], target_event['parent_type'], comment_id_parts[1])
                            all_events, conversation_id, comment_alias_map = fetch_and_aggregate_data(token, client, client_dir)
            elif command.startswith('/'):
                search_query = command[1:].strip()
            else:
                search_query = None
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
