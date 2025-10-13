
import os
import sys
import json
import glob
import subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text  # Added for explicit text rendering
from settings import get_default_editor, get_stored_credentials, clear_stored_credentials
from workspace_manager import workspace_selector, get_workspace_info, logout_current_workspace, ensure_workspace_directories

# Import our shared functions
from api_client import get_access_token, get_clients, clear_screen, get_workout_history, load_exercise_map, update_exercise_list
from directory_migration import get_client_dir, get_shared_dir
# Import our tools
from feed_tool import run_feed
from pr_tool import run_pr_analyzer
from format_tool import format_workouts_to_markup
from actual_prs_tool import run_actual_prs_viewer
from upload_tool import parse_workouts_from_file, upload_workout, prepare_assigned_metrics_for_workout, get_metric_lookup_structures
from metrics_tool import get_client_metrics
from ai_chat_tool import run_ai_chat
from metrics_tool import run_metrics_tool

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
        console.print("\n")  # Spacer for clarity
        console.print(Text("Options:", style="dim"))
        console.print(Text("  [l] Logout (clear credentials)", style="dim"))  # Use Text to avoid markdown
        console.print(Text("  [s] Adjust Settings (editor, credentials)", style="dim"))
        console.print(Text("  [w] Create New Workspace", style="dim"))
        
        # Show workspace switcher option only if user has multiple workspaces
        from settings import list_workspaces
        workspaces = list_workspaces()
        if len(workspaces) > 1:
            console.print(Text("  [ws] Switch Workspace", style="dim"))
        
        console.print(Text("{:>80}".format("Enter a number to select a client, or 'q' to quit > "), style="bold green"), end="")
        choice = input("").strip().lower()  # Raw input for clean capture
        if choice == 'q':
            return None
        if choice == 'l':
            if logout_current_workspace():
                console.print("[green]Logged out. You can now switch workspaces or quit.[/green]")
                console.input("Press Enter to return to workspace selector...")
                # Restart the main loop to show workspace selector
                main()
            else:
                console.print("[red]Logout failed.[/red]")
            sys.exit()
        if choice == 's':
            adjust_settings()
            clear_screen()
            console.print(table)  # Redisplay table after settings change
            continue
        if choice == 'w':
            from workspace_manager import setup_new_workspace
            new_workspace_key = setup_new_workspace()
            if new_workspace_key:
                console.print(f"[green]✅ Created workspace successfully! Restart the app to use it.[/green]")
                console.input("Press Enter to continue...")
            clear_screen()
            console.print(table)
            continue
        if choice == 'ws':
            from workspace_manager import quick_workspace_switcher
            switched_workspace = quick_workspace_switcher()
            if switched_workspace:
                console.print(f"[green]✅ Switched to {switched_workspace}! Loading clients...[/green]")
                # Return a special signal to restart client selection with new workspace
                return "WORKSPACE_SWITCHED"
            clear_screen()
            console.print(table)
            continue
        try:
            index = int(choice) - 1
            if 0 <= index < len(clients):
                return clients[index]
            else:
                console.print("[bold red]Invalid number.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input, please enter a number or option.[/bold red]")


def browse_history(token, client, coach_user_id):
    """Generates a markup file and opens it in an editor inside the client's directory."""
    client_name = client['full_name']
    client_dir = get_client_dir(client['id'])
    workouts = get_workout_history(token, client)
    valid_workouts = [w for w in workouts if w.get('workout_date')]
    if not valid_workouts:
        console.input("\nCould not load workout history. Press Enter to return.")
        return
    valid_workouts.sort(key=lambda w: w['workout_date'])

    # Fetch metrics for this client
    metrics = get_client_metrics(token, client['id'])

    markup_content = format_workouts_to_markup(valid_workouts, coach_user_id, metrics=metrics)
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


def run_uploader_tool(token, client, exercise_map, dry_run=False):
    """UI flow for uploading or validating workout and nutrition assignments."""
    client_id = client['id']
    client_dir = get_client_dir(client_id)
    if not os.path.exists(client_dir) or not any(f.endswith('.txt') for f in os.listdir(client_dir)):
        console.print(f"[yellow]No assignment .txt files found in {client_dir}[/yellow]")
        console.input("Press Enter to continue.")
        return
    txt_files = [f for f in os.listdir(client_dir) if f.endswith('.txt')]
    prompt_action = "validate" if dry_run else "upload"
    console.print(f"\n[bold]Select a file to {prompt_action} (workouts, nutrition, or mixed):[/bold]")
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
            assignments = parse_workouts_from_file(filepath, client_id, exercise_map)

            # Separate workouts and nutrition assignments for summary
            workouts = [a for a in assignments if a.get('workout_type') == 'default']
            nutrition = [a for a in assignments if a.get('workout_type') == 'nutrition']

            total_pending_metrics = sum(len(a.get("pending_metrics", [])) for a in assignments)
            metric_catalog_index = {}
            metric_catalog_slugs = []
            if total_pending_metrics:
                console.print(f"\n[dim]Resolving {total_pending_metrics} metric placeholder(s) against catalog...[/dim]")
                metric_catalog_index, metric_catalog_slugs = get_metric_lookup_structures(token)
                if not metric_catalog_index:
                    console.print("[yellow]Warning: Could not load metric catalog. Metrics will be skipped.[/yellow]")

            # Upload all assignments (both types use same API endpoint)
            action_label = "Validating" if dry_run else "Uploading"
            console.print(f"\n[cyan]{action_label} {len(workouts)} workout(s) and {len(nutrition)} nutrition assignment(s)...[/cyan]")
            for assignment in assignments:
                if metric_catalog_index and assignment.get("pending_metrics"):
                    assigned_metrics, skipped = prepare_assigned_metrics_for_workout(assignment, metric_catalog_index, metric_catalog_slugs)
                    if skipped:
                        for metric in skipped:
                            console.print(
                                f"[yellow]Warning: Unknown metric '{metric.get('metric_type')}' "
                                f"on {assignment.get('workout_date')} – skipping.[/yellow]"
                            )
                else:
                    assignment.pop("pending_metrics", None)
                    assignment.setdefault("assigned_metrics", [])
                assignment_type = "nutrition assignment" if assignment.get('workout_type') == "nutrition" else "workout"
                if dry_run:
                    console.print(
                        f"[dim]- {assignment_type.title()} on {assignment.get('workout_date')} "
                        f"({len(assignment.get('assigned_exercises', []))} items, "
                        f"{len(assignment.get('assigned_metrics', []))} metric(s))[/dim]"
                    )
                else:
                    upload_workout(token, assignment)

            if dry_run:
                console.print("[green]Dry run complete. No API calls were made.[/green]")
            else:
                console.print("[green]Upload complete.[/green]")
            
            # Pause to let user read the output
            console.input("\nPress Enter to continue...")
        else:
            console.print("[bold red]Invalid number, please try again.[/bold red]")
            console.input("Press Enter to continue.")
    except ValueError:
        console.print("[bold red]Invalid input, please enter a number.[/bold red]")
        console.input("Press Enter to continue.")


def clean_client_directory(client):
    """Cleans up a client directory by deleting all files except cached workouts and messages."""
    client_id = client['id']
    client_dir = get_client_dir(client_id)
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


def add_note(client):
    """Add a quick note to the client directory."""
    client_id = client['id']
    client_dir = get_client_dir(client_id)
    os.makedirs(client_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    note_filename = f"note-{date_str}.txt"
    editor_cmd = get_default_editor()
    original_dir = os.getcwd()
    try:
        os.chdir(client_dir)
        subprocess.run(editor_cmd + [note_filename], shell=False, check=False)
    finally:
        os.chdir(original_dir)
    console.print(f"[green]Note saved to {note_filename}.[/green]")
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
        console.print("  [bold]5.[/bold] Upload Workouts/Nutrition from File")
        console.print("  [bold]6.[/bold] AI Chat")
        console.print("  [bold]7.[/bold] Program Metrics")
        console.print("  [bold]8.[/bold] Validate Markup (Dry Run)")
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
        elif choice == '6':
            run_ai_chat(token, user_id, client, exercise_map)
        elif choice == '7':
            run_metrics_tool(token, client)
        elif choice == '8':
            run_uploader_tool(token, client, exercise_map, dry_run=True)
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
                if not exercise_map:
                    sys.exit("Failed to reload exercise list.")
            console.input("Press Enter to continue.")
        elif choice == 'q':
            break
        else:
            console.print(f"\n[red]Invalid choice '{choice}'.[/red]")
            console.input("Press Enter to continue...")


def adjust_settings():
    """Sub-menu to adjust settings like creds or editor."""
    from getpass import getpass  # Added import for password input
    from settings import load_or_init_settings, SETTINGS_FILE
    import base64
    from cryptography.fernet import Fernet
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
            password = getpass("New Password: ")
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


def main_with_workspace_selected():
    """Main application loop assuming workspace is already selected."""
    # Ensure workspace directories exist
    if not ensure_workspace_directories():
        sys.exit("Failed to create workspace directories. Exiting.")
    
    clear_screen()
    workspace_info = get_workspace_info()
    console.print(Panel(f"[bold blue]Turnkey Coach Tools CLI[/bold blue]\n[dim]Workspace: {workspace_info}[/dim]", expand=False))
    
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
        clear_screen() # clear the screen before showing client list
        selected_client = select_client(token, user_id)
        if selected_client is None:
            break  # Exit on 'q' or logout from select_client
        elif selected_client == "WORKSPACE_SWITCHED":
            # Workspace was switched, restart the main loop with new workspace
            main_with_workspace_selected()
            break  # Exit current main loop
        get_workout_history(token, selected_client)
        show_tool_menu(token, user_id, selected_client, exercise_map)

def main():
    """The main application loop."""
    # First, select workspace
    selected_workspace = workspace_selector()
    if not selected_workspace:
        console.print("\nExiting. Goodbye!", style="dim")
        return
    
    # Continue with the main app loop
    main_with_workspace_selected()

if __name__ == "__main__":
    main()
    console.print("\nExiting. Goodbye!", style="dim")
