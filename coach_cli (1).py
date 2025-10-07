import os
import sys
import json
import glob
import subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from settings import get_default_editor, get_stored_credentials, clear_stored_credentials

# Import our shared functions
from api_client import get_access_token, get_clients, clear_screen, get_workout_history, load_exercise_map, update_exercise_list, CLIENT_DATA_DIR
# Import our tools
from feed_tool import run_feed
from pr_tool import run_pr_analyzer
from format_tool import format_workouts_to_markup
from actual_prs_tool import run_actual_prs_viewer
from upload_tool import parse_workouts_from_file, upload_workout

console = Console()

def select_client(token, user_id):
    """Displays a table of clients and prompts the user to select one."""
    clients = get_clients(token, user_id)
    if not clients:
        console.print("[bold red]No clients found.[/bold red]")
        return None
    table = Table(title="Your Clients", border_style="green")
    table.add_column("#", style="dim", width=4)
    table.add_column("Client Name", style="bold", min_width=20)
    table.add_column("Client ID", style="cyan", width=12)
    table.add_column("Coaches")
    for i, client in enumerate(clients):
        table.add_row(str(i + 1), client['full_name'], str(client['id']), ", ".join(client['coaches']))
    console.print(table)
    while True:
        console.print("\n[dim]Options:[/dim]")
        console.print("[dim]  [l] Logout (clear credentials)[/dim]")  # Fixed: No extra backslashes
        console.print("[dim]  [s] Adjust Settings (editor, credentials)[/dim]")
        console.print("[bold green]{:>80}".format("Enter a number to select a client, or 'q' to quit > "), end="")
        choice = input("").strip().lower()  # Raw input to avoid rich styling issues
        if choice == 'q':
            return None
        if choice == 'l':
            clear_stored_credentials()
            if os.path.exists(TOKEN_CACHE_FILE):
                os.remove(TOKEN_CACHE_FILE)
            console.print("[green]Logged out. Bye![/green]")
            sys.exit()
        if choice == 's':
            adjust_settings()
            clear_screen()
            console.print(table)  # Redisplay table after settings change
            continue
        try:
            index = int(choice) - 1
            if 0 <= index < len(clients):
                return clients[index]
            else:
                console.print("[bold red]Invalid number, please try again.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input, please enter a number or option.[/bold red]")

def browse_history(token, client, coach_user_id):
    """Generates a markup file and opens it in an editor inside the client's directory."""
    client_name = client['full_name']
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client['id']))
    workouts = get_workout_history(token, client)
    if not workouts:
        console.input("\nCould not load workout history. Press Enter to return.")
        return
    valid_workouts = [w for w in workouts if w.get('workout_date')]
    valid_workouts.sort(key=lambda w: w['workout_date'])
    markup_content = format_workouts_to_markup(valid_workouts, coach_user_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_client_name = client_name.replace(' ', '_')
    history_filename = f"{safe_client_name}_history_{timestamp}.txt"
    history_filepath = os.path.join(client_dir, history_filename)
    with open(history_filepath, 'w', encoding='utf-8') as f:
        f.write(markup_content)
    console.print(f"\nWorkout history saved to:\n[green]{history_filepath}[/green]")
   
    editor_cmd = get_default_editor()
    editor_name = ' '.join(editor_cmd)
    console.print(f"\nOpening history in [bold green]{editor_name}[/bold green]...")
    console.print("[dim]Close the editor to continue...[/dim]")
    original_dir = os.getcwd()
    try:
        os.chdir(client_dir)
        subprocess.run(editor_cmd + [history_filename], shell=False, check=False)
    finally:
        os.chdir(original_dir)

def run_uploader_tool(token, client, exercise_map):
    """UI flow for the workout uploader tool."""
    client_id = client['id']
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    if not os.path.exists(client_dir) or not any(f.endswith('.txt') for f in os.listdir(client_dir)):
        console.print(f"[yellow]No workout .txt files found in {client_dir}[/yellow]")
        console.input("Press Enter to continue.")
        return
    txt_files = [f for f in os.listdir(client_dir) if f.endswith('.txt')]
    console.print("\n[bold]Select a workout file to upload:[/bold]")
    for i, filename in enumerate(txt_files):
        console.print(f"  [[bold]{i+1}[/bold]] {filename}")
    console.print("  [[bold]q[/bold]] Cancel")
    choice = console.input("\n> ")
    if choice.lower() == 'q':
        return
    try:
        index = int(choice) - 1
        if 0 <= index < len(txt_files):
            filepath = os.path.join(client_dir, txt_files[index])
            workouts = parse_workouts_from_file(filepath, client_id, exercise_map)
            for workout in workouts:
                upload_workout(token, workout)
        else:
            console.print("[bold red]Invalid number, please try again.[/bold red]")
            console.input("Press Enter to continue.")
    except ValueError:
        console.print("[bold red]Invalid input, please enter a number.[/bold red]")
        console.input("Press Enter to continue.")

def clean_client_directory(client):
    """Cleans up a client directory by deleting all files except cached workouts and messages."""
    client_id = client['id']
    client_dir = os.path.join(CLIENT_DATA_DIR, str(client_id))
    if not os.path.exists(client_dir):
        console.print(f"[yellow]No directory found for client {client['full_name']}.[/yellow]")
        console.input("Press Enter to continue.")
        return
    
    files_to_delete = []
    for f in os.listdir(client_dir):
        if not (f.startswith("workouts_user_") or f == "messages_cache.json" or f == "workouts_index.json"):
            files_to_delete.append(f)
    
    if not files_to_delete:
        console.print(f"[yellow]No files to clean up in {client_dir}.[/yellow]")
        console.input("Press Enter to continue.")
        return
    
    console.print("\n[bold yellow]The following files will be permanently deleted:[/bold yellow]")
    for filename in files_to_delete:
        console.print(f"  - {filename}")
    
    choice = console.input("\nAre you sure you want to delete these files? (y/n) > ").lower()
    if choice == 'y':
        deleted_count = 0
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(client_dir, filename))
                deleted_count += 1
            except OSError as e:
                console.print(f"[red]Error deleting {filename}: {e}[/red]")
        console.print(f"\n[green]Successfully deleted {deleted_count} file(s).[/green]")
    else:
        console.print("\nCleanup cancelled.")
    
    console.input("Press Enter to continue.")

def show_tool_menu(token, user_id, client, exercise_map):
    """Displays the main tool menu for a selected client."""
    while True:
        clear_screen()
        console.print(Panel(f"Selected Client: [bold green]{client['full_name']}[/bold green]", expand=False))
        console.print("\n[bold]Client Tools:[/bold]")
        console.print("  [bold]1.[/bold] Unified Feed")
        console.print("  [bold]2.[/bold] Estimated 1RMs (from history)")
        console.print("  [bold]3.[/bold] Actual PRs (from API)")
        console.print("  [bold]4.[/bold] Browse & Save Workout History")
        console.print("  [bold]5.[/bold] Upload Workout from File")
        console.print("\n[bold]Utilities:[/bold]")
        console.print("  [bold]n.[/bold] Add a Quick Note")
        console.print("  [bold]c.[/bold] Clean Up Directory")
        console.print("  [bold]r.[/bold] Force Refresh Workout History")
        console.print("  [bold]u.[/bold] Update Exercise List")
        console.print("\n  [bold]q.[/bold] Go back to client list")

        choice = console.input("\n> ").lower()
        if choice == '1':
            run_feed(token, user_id, client)
        elif choice == '2':
            run_pr_analyzer(token, client)
        elif choice == '3':
            run_actual_prs_viewer(token, client)
        elif choice == '4':
            browse_history(token, client, user_id)
        elif choice == '5':
            run_uploader_tool(token, client, exercise_map)
        elif choice == 'n':
            add_note(client)
        elif choice == 'c':
            clean_client_directory(client)
        elif choice == 'r':
            get_workout_history(token, client, force_refresh=True)
            console.input("Workout history has been refreshed. Press Enter to continue.")
        elif choice == 'u':
            if update_exercise_list(token):
                exercise_map = load_exercise_map()
                if not exercise_map: sys.exit("Failed to reload exercise list.")
            console.input("Press Enter to continue.")
        elif choice == 'q':
            break
        else:
            console.print(f"\n[red]Invalid choice '{choice}'.[/red]")
            console.input("Press Enter to continue...")

def adjust_settings():
    """Sub-menu to adjust settings like creds or editor."""
    while True:
        clear_screen()
        console.print("[bold]Adjust Settings:[/bold]")
        console.print("  [bold]1.[/bold] Change Editor")
        console.print("  [bold]2.[/bold] Change Credentials")
        console.print("  [bold]q.[/bold] Back")
        
        choice = console.input("\n> ").lower()
        if choice == '1':
            settings = load_or_init_settings()
            console.print("\n[bold]Enter new editor command (e.g., 'code -w' or 'nvim'):[/bold]")
            custom_cmd = console.input("> ").strip().split()
            if custom_cmd:
                settings['default_editor'] = custom_cmd
                with open(SETTINGS_FILE, 'w') as f:
                    json.dump(settings, f, indent=2)
                console.print("[green]Editor updated.[/green]")
        elif choice == '2':
            email = console.input("[bold]New Email:[/bold] ").strip()
            password = getpass.getpass("New Password: ")
            key = Fernet.generate_key()
            encoded_key = base64.urlsafe_b64encode(key).decode('utf-8')
            fernet = Fernet(key)
            encrypted_password = fernet.encrypt(password.encode()).decode('utf-8')
            settings = load_or_init_settings()
            settings['email'] = email
            settings['encrypted_password'] = encrypted_password
            settings['encryption_key'] = encoded_key
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            console.print("[green]Credentials updated.[/green]")
        elif choice == 'q':
            break
        console.input("Press Enter to continue...")

def main():
    """The main application loop."""
    clear_screen()
    console.print(Panel("[bold blue]Turnkey Coach Tools CLI[/bold blue]", expand=False))
    
    token, user_id = get_access_token()
    if not token or not user_id:
        sys.exit("Could not authenticate. Exiting.")
    _ = get_default_editor()  # Triggers if needed
    exercise_map = load_exercise_map()
    if not exercise_map:
        console.print("[yellow]`exerciselist.json` not found.[/yellow]")
        if console.input("Would you like to download it now? (y/n) > ").lower() == 'y':
            if update_exercise_list(token):
                exercise_map = load_exercise_map()
            if not exercise_map:
                sys.exit("Failed to load exercise list after download. Exiting.")
        else:
            sys.exit("Cannot proceed without an exercise list. Exiting.")

    while True:
        selected_client = select_client(token, user_id)
        if selected_client is None:
            break  # Exit on 'q' or logout from select_client
        get_workout_history(token, selected_client)
        show_tool_menu(token, user_id, selected_client, exercise_map)

if __name__ == "__main__":
    main()
    console.print("\nExiting. Goodbye!", style="dim")