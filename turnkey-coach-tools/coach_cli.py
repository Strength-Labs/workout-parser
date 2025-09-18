import os
import sys
import json
import tempfile
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import our shared functions
from api_client import get_access_token, get_clients
# Import our tools
from feed_tool import run_feed
from pr_tool import run_pr_analyzer
from format_tool import format_workouts_to_markup

console = Console()

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

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
        choice = console.input("\nEnter a number to select a client, or '[bold]q[/bold]' to quit > ")
        if choice.lower() == 'q':
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(clients):
                return clients[index]
            else:
                console.print("[bold red]Invalid number, please try again.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input, please enter a number.[/bold red]")

def browse_history(client, coach_user_id):
    """Generates a markup file of workout history and opens it in a text editor."""
    client_id = client['id']
    filepath = os.path.join(os.path.expanduser("~/TurnkeyClients"), str(client_id), f"workouts_user_{client_id}.json")

    if not os.path.exists(filepath):
        console.print(f"\n[bold red]Workout history file not found.[/bold red]")
        console.print("[yellow]Hint: Run the 'Unified Feed' tool first to download the history.[/yellow]")
        console.input("\nPress Enter to return to the tool menu.")
        return

    console.print(f"Loading workout history from [cyan]{filepath}[/cyan]...")
    with open(filepath, 'r') as f:
        workouts = json.load(f)

    # --- ADDED THIS LINE TO SORT THE WORKOUTS ---
    workouts.sort(key=lambda w: w['workout_date'])
    # ---------------------------------------------

    markup_content = format_workouts_to_markup(workouts, coach_user_id)
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(markup_content)
        tmp_filepath = tmp_file.name

    editor = os.getenv('EDITOR', 'vim') 
    console.print(f"Opening history in [bold green]{editor}[/bold green]...")
    os.system(f"{editor} {tmp_filepath}")

    os.remove(tmp_filepath)

def show_tool_menu(token, user_id, client):
    """Displays the main tool menu for a selected client."""
    while True:
        clear_screen()
        console.print(Panel(f"Selected Client: [bold green]{client['full_name']}[/bold green]", expand=False))
        
        console.print("\n[bold]Select a tool:[/bold]")
        console.print("  [bold]1.[/bold] Unified Feed")
        console.print("  [bold]2.[/bold] PR Analyzer")
        console.print("  [bold]3.[/bold] Browse Workout History in Editor")
        console.print("  [bold]4.[/bold] Upload Workout from File")
        console.print("\n  [bold]q.[/bold] Go back to client list")

        choice = console.input("\n> ")

        if choice == '1':
            run_feed(token, user_id, client)
        elif choice == '2':
            run_pr_analyzer(client)
        elif choice == '3':
            browse_history(client, user_id)
        elif choice == '4':
            console.print(f"\n[yellow]Tool '{choice}' is not yet implemented.[/yellow]")
            console.input("Press Enter to continue...")
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

    while True:
        clear_screen()
        selected_client = select_client(token, user_id)
        
        if selected_client is None:
            break
        
        show_tool_menu(token, user_id, selected_client)

if __name__ == "__main__":
    main()
    console.print("\nExiting. Goodbye!", style="dim")
