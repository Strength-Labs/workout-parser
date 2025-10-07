import requests
import os
import json
import re
import html
import threading
import copy
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import shared functions from the api_client.py file
from api_client import API_BASE_URL, CLIENT_DATA_DIR, clean_text, clear_screen

console = Console()

# --- Incremental Caching Helpers ---

def _parse_ts(ts_str):
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        try:
            return datetime.fromisoformat(ts_str)
        except Exception:
            return None


def _load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _get_or_create_conversation_id(token, client_full_name):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/conversations"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        conversations = resp.json().get("private_conversations", [])
        for convo in conversations:
            if convo.get("member_count") == 2 and convo.get("display_name") == client_full_name:
                return convo.get("id")
    except requests.exceptions.RequestException:
        return None
    return None


def _load_messages_cache(client_dir):
    path = os.path.join(client_dir, "messages_cache.json")
    return _load_json(path, {"conversation_id": None, "last_seen_id": None, "messages": {}})


def _save_messages_cache(client_dir, cache):
    path = os.path.join(client_dir, "messages_cache.json")
    _save_json(path, cache)


def _refresh_messages_cache(token, client_full_name, client_dir, initial_max_pages=5, per_page=100):
    cache = _load_messages_cache(client_dir)
    if not cache.get("conversation_id"):
        convo_id = _get_or_create_conversation_id(token, client_full_name)
        cache["conversation_id"] = convo_id
        _save_messages_cache(client_dir, cache)
    convo_id = cache.get("conversation_id")
    if not convo_id:
        return cache

    headers = {"Authorization": f"Bearer {token}"}
    last_seen_id = cache.get("last_seen_id")

    max_pages = 1 if last_seen_id else initial_max_pages
    max_id_seen = last_seen_id or 0
    any_new = False

    for page in range(1, max_pages + 1):
        params = {"conversation_id": convo_id, "per_page": per_page, "page": page}
        try:
            resp = requests.get(f"{API_BASE_URL}/api/v1/messages", headers=headers, params=params)
            resp.raise_for_status()
            items = resp.json() or []
        except requests.exceptions.RequestException:
            break

        if not items:
            break

        new_in_page = 0
        for msg in items:
            mid = msg.get('id')
            if mid is None:
                continue
            if str(mid) not in cache['messages']:
                cache['messages'][str(mid)] = {
                    'id': mid,
                    'created_at': msg.get('created_at'),
                    'body': msg.get('body'),
                    'user': msg.get('user') or {},
                }
                new_in_page += 1
                any_new = True
                if mid > (max_id_seen or 0):
                    max_id_seen = mid
        # Stop early if nothing new found on this page and we already had a watermark
        if last_seen_id is not None and new_in_page == 0:
            break
        # If fewer than per_page, it's the last page
        if len(items) < per_page:
            break

    if any_new:
        cache['last_seen_id'] = max_id_seen
        _save_messages_cache(client_dir, cache)
    return cache


def _load_workouts_index(client_dir, client_id):
    path = os.path.join(client_dir, "workouts_index.json")
    default = {"client_id": client_id, "last_summary_sync": None, "workouts": {}}
    return _load_json(path, default)


def _save_workouts_index(client_dir, index):
    path = os.path.join(client_dir, "workouts_index.json")
    _save_json(path, index)


def _fetch_workouts_summary(token, client_id):
    headers = {"Authorization": f"Bearer {token}"}
    list_url = f"{API_BASE_URL}/api/v1/workouts"
    params = {"user_id": client_id, "sort": "ascending", "published": True}
    try:
        response = requests.get(list_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json() or []
    except requests.exceptions.RequestException:
        return []


def _fetch_workout_detail(token, workout_id):
    headers = {"Authorization": f"Bearer {token}"}
    detail_url = f"{API_BASE_URL}/api/v1/workouts/{workout_id}"
    try:
        resp = requests.get(detail_url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        return None
    return None


def _update_workouts_cache_incremental(token, client, client_dir):
    client_id = client['id']
    index = _load_workouts_index(client_dir, client_id)

    # Load existing detailed workouts
    workouts_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")
    existing_workouts = _load_json(workouts_path, [])
    existing_map = {w.get('id'): w for w in existing_workouts if isinstance(w, dict)}

    # Get summaries and diff by updated_at
    summaries = _fetch_workouts_summary(token, client_id)
    changed_ids = []
    updated_index = index.get('workouts', {})

    for summary in summaries:
        wid = summary.get('id')
        if wid is None:
            continue
        updated_at = summary.get('updated_at') or summary.get('last_activity')
        prev = updated_index.get(str(wid), {}).get('updated_at')
        if not prev or (updated_at and updated_at != prev) or (wid not in existing_map):
            changed_ids.append(wid)
        # Prime index with current value; we'll save it after fetching details
        updated_index[str(wid)] = {"updated_at": updated_at}

    # Fetch only changed workout details concurrently
    if changed_ids:
        headers = {"Authorization": f"Bearer {token}"}
        with ThreadPoolExecutor(max_workers=8) as pool:
            future_map = {pool.submit(_fetch_workout_detail, token, wid): wid for wid in changed_ids}
            for fut in as_completed(future_map):
                wid = future_map[fut]
                detail = fut.result()
                if detail:
                    existing_map[wid] = detail

        # Write merged list back (sorted by workout_date if available)
        merged = list(existing_map.values())
        try:
            merged.sort(key=lambda w: w.get('workout_date') or '')
        except Exception:
            pass
        try:
            with open(workouts_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    # Save updated index
    index['workouts'] = updated_index
    index['last_summary_sync'] = datetime.now(timezone.utc).isoformat()
    _save_workouts_index(client_dir, index)

    # Return full detailed workouts and which ones changed
    final_workouts = list(existing_map.values()) if existing_map else existing_workouts
    return final_workouts, set(changed_ids)


def _extract_comments_from_workouts(workouts):
    comments = []
    if not workouts:
        return comments
    for workout in workouts:
        workout_id = workout.get('id')
        # Workout-level comments
        for comment in workout.get('comments', []) or []:
            cid = comment.get('id')
            ts = _parse_ts(comment.get('updated_at'))
            user = comment.get('user') or {}
            parent_type = comment.get('parent_type') or 'Workout'
            parent_id = comment.get('parent_id') or workout_id
            comments.append({
                "type": "workout_comment",
                "content": comment.get('body'),
                "author_id": user.get('id'),
                "author": user.get('full_name'),
                "timestamp": ts,
                "parent_id": parent_id,
                "parent_type": parent_type,
                "comment_id": str(cid) if cid is not None else f"Workout-{workout_id}"
            })
        # Exercise-level comments
        for exercise in workout.get('assigned_exercises', []) or []:
            ex_id = exercise.get('id')
            for comment in exercise.get('comments', []) or []:
                cid = comment.get('id')
                ts = _parse_ts(comment.get('updated_at'))
                user = comment.get('user') or {}
                parent_type = comment.get('parent_type') or 'AssignedExercise'
                parent_id = comment.get('parent_id') or ex_id
                comments.append({
                    "type": "workout_comment",
                    "content": comment.get('body'),
                    "author_id": user.get('id'),
                    "author": user.get('full_name'),
                    "timestamp": ts,
                    "parent_id": parent_id,
                    "parent_type": parent_type,
                    "comment_id": str(cid) if cid is not None else f"AssignedExercise-{ex_id}"
                })
    return comments

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
    Incrementally refreshes messages and workouts, rebuilds the unified feed,
    and updates the shared state plus the feed cache file.
    Designed to be run in a background thread.
    """
    client_id = client["id"]
    client_full_name = client["full_name"]
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))

    # 1) Messages: refresh cache (resolve conversation_id if needed)
    messages_cache = _refresh_messages_cache(token, client_full_name, client_dir)
    conversation_id = messages_cache.get('conversation_id')

    # 2) Workouts/comments: update only changed workouts using updated_at diff
    workouts, _changed = _update_workouts_cache_incremental(token, client, client_dir)

    # 3) Build events from caches
    all_events = []
    for msg in (messages_cache.get('messages') or {}).values():
        ts = _parse_ts(msg.get('created_at'))
        user = msg.get('user') or {}
        all_events.append({
            "type": "message",
            "content": msg.get('body'),
            "author_id": user.get('id'),
            "author": user.get('full_name'),
            "timestamp": ts,
        })

    all_events.extend(_extract_comments_from_workouts(workouts))
    all_events = [e for e in all_events if e.get('timestamp') is not None]
    all_events.sort(key=lambda x: x['timestamp'])

    # 4) Assign alias IDs for workout comments (stable by comment_id)
    comment_alias_map = {}
    alias_counter = 1
    for item in reversed(all_events):
        if item['type'] == 'workout_comment':
            item['alias_id'] = str(alias_counter)
            comment_alias_map[str(alias_counter)] = item.get('comment_id')
            alias_counter += 1

    # 5) Update shared state
    with feed_data_lock:
        feed_data["events"] = all_events
        feed_data["conversation_id"] = conversation_id
        feed_data["alias_map"] = comment_alias_map
        feed_data["is_refreshing"] = False

    # 6) Persist feed cache
    cache_path = os.path.join(client_dir, "feed_cache.json")
    events_to_cache = [dict(event) for event in all_events]
    for event in events_to_cache:
        if isinstance(event.get('timestamp'), datetime):
            event['timestamp'] = event['timestamp'].isoformat()
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({"events": events_to_cache, "conversation_id": conversation_id, "alias_map": comment_alias_map}, f, ensure_ascii=False)
    except Exception:
        pass

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

    # Load last materialized feed if present
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                feed_data["events"] = cached_data.get("events", [])
                for event in feed_data["events"]:
                    try:
                        event['timestamp'] = datetime.fromisoformat(event['timestamp'])
                    except Exception:
                        event['timestamp'] = _parse_ts(event.get('timestamp'))
                feed_data["conversation_id"] = cached_data.get("conversation_id")
                feed_data["alias_map"] = cached_data.get("alias_map", {})
        except Exception:
            pass

    # If conversation_id is still missing, try messages cache
    if not feed_data.get("conversation_id"):
        msg_cache = _load_messages_cache(client_dir)
        feed_data["conversation_id"] = msg_cache.get("conversation_id")

    # Kick off background refresh
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
            console.print("\n" + "-" * 50)
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
                    target_event = next((e for e in display_data["events"] if str(e.get('comment_id')) == str(real_id_str)), None) if real_id_str else None
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
