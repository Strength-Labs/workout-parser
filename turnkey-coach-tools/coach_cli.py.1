import os
import sys
import json
import tempfile
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import our shared functions
from api_client import get_access_token, get_clients, clear_screen, get_workout_history, load_exercise_map, update_exercise_list
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
    table.add_column("#", style="dim", width=4); table.add_column("Client Name", style="bold", min_width=20)
    table.add_column("Client ID", style="cyan", width=12); table.add_column("Coaches")
    for i, client in enumerate(clients):
        table.add_row(str(i + 1), client['full_name'], str(client['id']), ", ".join(client['coaches']))
    console.print(table)
    while True:
        choice = console.input("\nEnter a number to select a client, or '[bold]q[/bold]' to quit > ")
        if choice.lower() == 'q': return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(clients): return clients[index]
            else: console.print("[bold red]Invalid number, please try again.[/bold red]")
        except ValueError: console.print("[bold red]Invalid input, please enter a number.[/bold red]")

def browse_history(token, client, coach_user_id):
    """Generates a markup file and opens it in an editor inside the client's directory."""
    client_name = client['full_name']
    client_dir = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client['id']))
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
    with open(history_filepath, 'w') as f:
        f.write(markup_content)
    console.print(f"\nWorkout history saved to:\n[green]{history_filepath}[/green]")
    editor = os.getenv('EDITOR', 'nvim') 
    console.print(f"\nOpening history in [bold green]{editor}[/bold green]...")
    console.print("[dim]Close the editor to continue...[/dim]")
    original_dir = os.getcwd()
    try:
        os.chdir(client_dir)
        os.system(f"{editor} {history_filename}")
    finally:
        os.chdir(original_dir)

def run_uploader_tool(token, client, exercise_map):
    """UI flow for the workout uploader tool."""
    client_id = client['id']
    client_dir = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client_id))
    
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
    if choice.lower() == 'q': return
    try:
        index = int(choice) - 1
        if 0 <= index < len(txt_files):
            filepath = os.path.join(client_dir, txt_files[index])
            workouts_to_upload = parse_workouts_from_file(filepath, client_id, exercise_map)
            
            if not workouts_to_upload:
                console.print("[red]Could not parse any valid workouts from the file.[/red]")
                console.input("\nPress Enter to continue.")
                return

            # --- NEW DEBUGGING STEP: Save the generated JSON to a file ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"plan_for_upload_{timestamp}.json"
            json_filepath = os.path.join(client_dir, json_filename)
            with open(json_filepath, 'w') as f:
                json.dump(workouts_to_upload, f, indent=2)
            console.print(f"\n[bold yellow]Debug JSON saved to:[/bold yellow]\n[green]{json_filepath}[/green]\n")
            # -----------------------------------------------------------------

            for workout in workouts_to_upload:
                upload_workout(token, workout)

            console.input("\nUpload process finished. Press Enter to continue.")
        else:
            console.print("[red]Invalid selection.[/red]")
            console.input("Press Enter to continue.")
    except ValueError:
        console.print("[red]Invalid input.[/red]")
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
        console.print("\n[bold]System Tools:[/bold]")
        console.print("  [bold]r.[/bold] Force Refresh Workout History")
        console.print("  [bold]u.[/bold] Update Exercise List")
        console.print("\n  [bold]q.[/bold] Go back to client list")

        choice = console.input("\n> ")
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
        elif choice.lower() == 'r':
            get_workout_history(token, client, force_refresh=True)
            console.input("Workout history has been refreshed. Press Enter to continue.")
        elif choice.lower() == 'u':
            if update_exercise_list(token):
                exercise_map = load_exercise_map()
                if not exercise_map: sys.exit("Failed to reload exercise list after update.")
            console.input("Press Enter to continue.")
        elif choice.lower() == 'q':
            break
        else:
            console.print(f"\n[red]Invalid choice '{choice}'.[/red]")
            console.input("Press Enter to continue...")

def main():
    """The main application loop."""
    clear_screen()
    console.print(Panel("[bold blue]Turnkey Coach CLI[/bold blue]", expand=False))
    
    token, user_id = get_access_token()
    if not token or not user_id:
        sys.exit("Could not authenticate. Exiting.")

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
        clear_screen()
        selected_client = select_client(token, user_id)
        if selected_client is None:
            break
        get_workout_history(token, selected_client)
        show_tool_menu(token, user_id, selected_client, exercise_map)

if __name__ == "__main__":
    main()
    console.print("\nExiting. Goodbye!", style="dim")
