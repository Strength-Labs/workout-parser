
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
from src.settings import get_default_editor, get_stored_credentials, clear_stored_credentials
from src.workspace_manager import workspace_selector, get_workspace_info, logout_current_workspace, ensure_workspace_directories

# Import our shared functions
from src.api_client import get_access_token, get_clients, clear_screen, get_workout_history, get_workout_history_headless, load_exercise_map, update_exercise_list
from src.directory_migration import get_client_dir, get_shared_dir
# Import display utilities for bundled app compatibility
from src.display_utils import safe_input
# Import our tools
from src.tools.feed_tool import run_feed
from src.tools.pr_tool import run_pr_analyzer
from src.tools.format_tool import format_workouts_to_markup
from src.tools.actual_prs_tool import run_actual_prs_viewer
from src.tools.upload_tool import parse_workouts_from_file, upload_workout, prepare_assigned_metrics_for_workout, get_metric_lookup_structures
from src.tools.metrics_tool import get_client_metrics
from src.tools.ai_chat_tool import run_ai_chat
from src.tools.metrics_tool import run_metrics_tool

console = Console()


def run_bulk_sync_from_cli(token, user_id):
    """Launch the standalone bulk sync script with user-friendly options."""
    clear_screen()
    console.print(Panel.fit("🌙 [bold blue]Bulk Sync All Clients[/bold blue] 🌙", border_style="blue"))
    
    console.print("\n[dim]This will launch the bulk sync tool to sync workout history and feed data for all your clients.[/dim]")
    console.print("[dim]This will run with a live progress display in this window.[/dim]")
    console.print("[dim]Depending on data volume, this may take several minutes.[/dim]")
    
    # Show sync options
    console.print("\n[bold]Sync Options:[/bold]")
    console.print("  [bold]1.[/bold] Quick Sync (2 workers, recommended)")
    console.print("  [bold]2.[/bold] Fast Sync (4 workers)")
    console.print("  [bold]3.[/bold] Test Mode (first 5 clients only)")
    console.print("  [bold]q.[/bold] Cancel")
    
    choice = safe_input("\n> ").strip().lower()
    if choice == 'q':
        return
    
    # Set parameters based on choice (in-process run for bundled apps)
    workers = 2
    test_limit = None
    if choice == '1':
        workers = 2
        mode_desc = "Quick Sync with 2 workers"
    elif choice == '2':
        workers = 4
        mode_desc = "Fast Sync with 4 workers"
    elif choice == '3':
        workers = 2
        test_limit = 5
        mode_desc = "Test Mode (first 5 clients)"
    else:
        workers = 2  # default
        mode_desc = "Quick Sync with 2 workers (default)"
    
    # Final confirmation
    console.print(f"\n[yellow]Ready to launch {mode_desc}[/yellow]")
    prompt = "Proceed? Type 'y' to proceed (default is No) [y/N]: "
    if safe_input(f"[bold green]{prompt}[/bold green]").lower() != 'y':
        console.print("[yellow]Bulk sync cancelled.[/yellow]")
        safe_input("Press Enter to continue...")
        return
    
    # Run the bulk sync in-process (works in source and packaged builds)
    console.print("\n[dim]Launching bulk sync tool...[/dim]")
    try:
        from src.bulk_sync import run_bulk_sync
        success = run_bulk_sync(max_workers=workers, force_refresh=False, test_limit=test_limit)
        if success:
            console.print("\n[bold green]✨ Bulk sync completed successfully! ✨[/bold green]")
        else:
            console.print("\n[yellow]⚠️ Bulk sync finished with errors or no work.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Bulk sync failed: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

    safe_input("\nPress Enter to return to client list...")


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
        console.print(Text("  [b] Bulk Sync All Clients", style="dim"))
        console.print(Text("  [l] Logout (clear credentials)", style="dim"))  # Use Text to avoid markdown
        console.print(Text("  [s] Adjust Settings (editor, credentials)", style="dim"))
        console.print(Text("  [w] Create New Workspace", style="dim"))
        
        # Show workspace switcher option only if user has multiple workspaces
        from src.settings import list_workspaces
        workspaces = list_workspaces()
        if len(workspaces) > 1:
            console.print(Text("  [ws] Switch Workspace", style="dim"))
        
        console.print(Text("{:>80}".format("Enter a number to select a client, or 'q' to quit > "), style="bold green"), end="")
        choice = safe_input("").strip().lower()  # Use safe_input for bundled app compatibility
        if choice == 'q':
            return None
        if choice == 'b':
            run_bulk_sync_from_cli(token, user_id)
            clear_screen()
            console.print(table)  # Redisplay table after bulk sync
            continue
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
            from src.workspace_manager import setup_new_workspace
            new_workspace_key = setup_new_workspace()
            if new_workspace_key:
                console.print(f"[green]✅ Created workspace successfully! Restart the app to use it.[/green]")
                console.input("Press Enter to continue...")
            clear_screen()
            console.print(table)
            continue
        if choice == 'ws':
            from src.workspace_manager import quick_workspace_switcher
            switched_workspace = quick_workspace_switcher()
            if switched_workspace:
                console.print(f"[green]✅ Switched to {switched_workspace}! Loading clients...[/green]")
                safe_input("Press Enter to continue...")
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
    workouts = get_workout_history_headless(token, client)
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

def delete_workouts_ui(token, client):
    """Interactive UI for deleting workouts with various filtering options."""
    from datetime import datetime, date
    from src.api_client import delete_workouts_filtered
    
    client_name = client['full_name']
    client_id = client['id']
    
    while True:
        clear_screen()
        console.print(Panel(f"Delete Workouts - [bold green]{client_name}[/bold green]", expand=False))
        
        console.print("\n[bold]Delete Options:[/bold]")
        console.print("  [bold]1.[/bold] Delete after TODAY (default)")
        console.print("  [bold]2.[/bold] Delete after specific date")
        console.print("  [bold]3.[/bold] Delete date range")
        console.print("  [bold]q.[/bold] Back to menu")
        
        date_choice = console.input("\n> ").lower()
        if date_choice == 'q':
            return
        
        # Date selection logic
        start_date = None
        end_date = None
        
        if date_choice == '1':  # After today
            today = date.today()
            start_date = (today).isoformat()
            date_desc = f"after today ({start_date})"
        elif date_choice == '2':  # After specific date
            date_str = console.input("Enter start date (YYYY-MM-DD): ").strip()
            try:
                # Validate date format
                datetime.strptime(date_str, '%Y-%m-%d')
                start_date = date_str
                date_desc = f"on/after {start_date}"
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
                console.input("Press Enter to try again...")
                continue
        elif date_choice == '3':  # Date range
            start_str = console.input("Enter start date (YYYY-MM-DD): ").strip()
            end_str = console.input("Enter end date (YYYY-MM-DD): ").strip()
            try:
                # Validate date formats
                datetime.strptime(start_str, '%Y-%m-%d')
                datetime.strptime(end_str, '%Y-%m-%d')
                start_date = start_str
                end_date = end_str
                date_desc = f"from {start_date} to {end_date}"
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
                console.input("Press Enter to try again...")
                continue
        else:
            console.print("[red]Invalid choice.[/red]")
            console.input("Press Enter to try again...")
            continue
        
        # Workout type selection
        clear_screen()
        console.print(Panel(f"Delete Workouts {date_desc} - [bold green]{client_name}[/bold green]", expand=False))
        
        console.print("\n[bold]Workout Type:[/bold]")
        console.print("  [bold]1.[/bold] Strength workouts only")
        console.print("  [bold]2.[/bold] Nutrition assignments only")
        console.print("  [bold]3.[/bold] Both strength and nutrition")
        console.print("  [bold]q.[/bold] Back")
        
        type_choice = console.input("\n> ").lower()
        if type_choice == 'q':
            continue
        
        workout_types = None
        type_desc = ""
        if type_choice == '1':
            workout_types = ['default']
            type_desc = "strength workouts"
        elif type_choice == '2':
            workout_types = ['nutrition']
            type_desc = "nutrition assignments"
        elif type_choice == '3':
            workout_types = ['default', 'nutrition']
            type_desc = "strength workouts and nutrition assignments"
        else:
            console.print("[red]Invalid choice.[/red]")
            console.input("Press Enter to try again...")
            continue
        
        # Preview what would be deleted (dry run)
        console.print(f"\n[dim]Checking what {type_desc} would be deleted {date_desc}...[/dim]")
        
        preview_result = delete_workouts_filtered(
            token, client_id, start_date, end_date, workout_types, dry_run=True
        )
        
        if preview_result['errors']:
            console.print("[red]Error fetching workouts for preview:[/red]")
            for error in preview_result['errors']:
                console.print(f"  - {error}")
            console.input("Press Enter to continue...")
            continue
        
        if not preview_result['would_delete']:
            console.print(f"[yellow]No {type_desc} found {date_desc}.[/yellow]")
            console.input("Press Enter to continue...")
            continue
        
        # Show preview
        console.print(f"\n[bold yellow]Preview: {len(preview_result['would_delete'])} workout(s) would be deleted:[/bold yellow]")
        for workout in preview_result['would_delete']:
            workout_type_label = "Nutrition" if workout['type'] == 'nutrition' else "Strength"
            title_part = f" - {workout['title']}" if workout['title'] else ""
            console.print(f"  • {workout['date']} ({workout_type_label}){title_part}")
        
        # Final confirmation
        console.print(f"\n[bold red]⚠️  WARNING: This will permanently delete {len(preview_result['would_delete'])} workout(s)![/bold red]")
        console.print("[dim]Completed workouts cannot be deleted and will be skipped.[/dim]")
        
        confirm = console.input("\nAre you ABSOLUTELY SURE you want to delete these workouts? Type 'DELETE' to confirm: ").strip()
        
        if confirm != 'DELETE':
            console.print("[green]Deletion cancelled.[/green]")
            console.input("Press Enter to continue...")
            continue
        
        # Perform actual deletion
        console.print("\n[yellow]Deleting workouts...[/yellow]")
        
        delete_result = delete_workouts_filtered(
            token, client_id, start_date, end_date, workout_types, dry_run=False
        )
        
        # Show results
        deleted_count = len(delete_result['deleted'])
        skipped_count = len(delete_result['skipped'])
        error_count = len(delete_result['errors'])
        
        if deleted_count > 0:
            console.print(f"[bold green]✅ Successfully deleted {deleted_count} workout(s)![/bold green]")
        
        if skipped_count > 0:
            console.print(f"[yellow]⚠️  Skipped {skipped_count} workout(s):[/yellow]")
            for workout in delete_result['skipped']:
                console.print(f"  • {workout['date']}: {workout['reason']}")
        
        if error_count > 0:
            console.print(f"[red]❌ {error_count} error(s) occurred:[/red]")
            for workout in delete_result['errors']:
                console.print(f"  • {workout['date']}: {workout['error']}")
        
        # Force refresh the workout cache since we deleted workouts
        with console.status("[bold green]Refreshing workout cache...", spinner="dots"):
            get_workout_history_headless(token, client, force_refresh=True)
        console.print("[bold green]✅ Cache refreshed successfully![/bold green]")

        console.input("\nPress Enter to continue...")
        return  # Exit after successful operation


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
        console.print("  [bold]7.[/bold] Review AI Chat History")
        console.print("  [bold]8.[/bold] Program Metrics")
        console.print("  [bold]9.[/bold] Validate Markup (Dry Run)")
        console.print("\n[bold]Utilities:[/bold]")
        console.print("  [bold]d.[/bold] Delete Workouts")
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
            from src.tools.ai_chat_tool import browse_chat_history
            browse_chat_history(client)
        elif choice == '8':
            run_metrics_tool(token, client)
        elif choice == '9':
            run_uploader_tool(token, client, exercise_map, dry_run=True)
        elif choice == 'd':
            delete_workouts_ui(token, client)
        elif choice == 'n':
            add_note(client)
        elif choice == 'c':
            clean_client_directory(client)
        elif choice == 'r':
            get_workout_history_headless(token, client, force_refresh=True)
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
    from src.settings import load_or_init_settings, SETTINGS_FILE
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
