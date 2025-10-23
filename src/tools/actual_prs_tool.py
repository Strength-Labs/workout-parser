import requests
import os
from datetime import date, timedelta, datetime
from rich.console import Console

# Import the base URL from our shared library
from src.api_client import API_BASE_URL

console = Console()

# --- Configuration ---
MAIN_LIFTS = ["squat", "bench press", "deadlift", "press"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def wendler_1rm(weight, reps):
    """Calculates estimated 1RM using the Wendler formula for comparison."""
    if not isinstance(reps, (int, float)) or reps <= 1:
        return weight
    return (weight * reps * 0.0333) + weight

def get_client_prs(token, client_id, start_date=None, end_date=None):
    """Fetches all PRs for a specific client within a date range from the API."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"user_id": client_id}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
        
    url = f"{API_BASE_URL}/api/v1/prs"
    with console.status("Fetching PRs from API..."):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            console.print(f"\n[bold red]Could not fetch PRs for client {client_id}: {err}[/bold red]")
            return []

def process_prs(all_prs):
    """Processes all PRs to find the single best PR for every exercise."""
    best_lifts = {}
    prs_by_exercise = {}
    for pr in all_prs:
        lift_name = pr.get("exercise", {}).get("name", "Unknown").lower()
        if lift_name not in prs_by_exercise:
            prs_by_exercise[lift_name] = []
        prs_by_exercise[lift_name].append(pr)

    for lift_name, pr_list in prs_by_exercise.items():
        # Prefer actual 1-rep maxes, otherwise find the best estimated 1RM
        actual_1rms = [p for p in pr_list if p.get("reps") == 1]
        if actual_1rms:
            best_pr_for_lift = max(actual_1rms, key=lambda p: float(p.get("weight", 0) or 0))
        else:
            best_pr_for_lift = max(pr_list, key=lambda p: wendler_1rm(float(p.get("weight", 0) or 0), p.get("reps")))
        
        best_lifts[lift_name] = best_pr_for_lift
            
    return best_lifts

def display_prs(client_name, best_lifts, date_range_str):
    """Displays the main lift PRs."""
    clear_screen()
    console.print(f"--- [bold]Official Personal Records for {client_name}[/bold] ---")
    console.print(f"---      [cyan]Date Range: {date_range_str}[/cyan]      ---\n")

    for lift in MAIN_LIFTS:
        pr = best_lifts.get(lift)
        lift_display_name = lift.replace(" press", " Press").title()

        if pr:
            weight = float(pr.get("weight", 0) or 0)
            reps = pr.get("reps")
            date_str = pr.get("date", "N/A")
            unit = pr.get("weight_type", "units")

            if reps == 1:
                console.print(f"{lift_display_name:<15} [bold green]{weight:7.1f}[/bold green] {unit} on {date_str}")
            else:
                estimated_1rm = wendler_1rm(weight, reps)
                console.print(f"{lift_display_name:<15} [bold yellow]{estimated_1rm:7.1f}[/bold yellow] {unit} on {date_str} ([dim]estimated from {weight} {unit} x {reps}[/dim])")
        else:
            console.print(f"{lift_display_name:<15} [dim]No PR found[/dim]")

def run_actual_prs_viewer(token, client):
    """The main loop for viewing a single client's PRs with date filtering."""
    client_id = client.get("id")
    client_name = client.get('full_name')
    start_date, end_date = None, None
    date_range_str = "All Time"

    while True:
        all_prs = get_client_prs(token, client_id, start_date, end_date)
        if all_prs is None:
            console.input("\nCould not fetch PRs. Press Enter to return to the tool menu.")
            break

        best_lifts = process_prs(all_prs)
        best_other_lifts = {k: v for k, v in best_lifts.items() if k not in MAIN_LIFTS}
        
        display_prs(client_name, best_lifts, date_range_str)

        console.print("\n" + "-"*50)
        console.print(r"\[a]ll Time | \[3]m | \[6]m | \[y]ear | \[m]ore PRs | \[q]uit")
        choice = console.input("> ").lower()

        if choice == 'q':
            break
        elif choice == 'a':
            start_date, end_date = None, None
            date_range_str = "All Time"
        elif choice == '3':
            end_date = date.today()
            start_date = (end_date - timedelta(days=90)).isoformat()
            date_range_str = "Last 3 Months"
        elif choice == '6':
            end_date = date.today()
            start_date = (end_date - timedelta(days=180)).isoformat()
            date_range_str = "Last 6 Months"
        elif choice == 'y':
            end_date = date.today()
            start_date = (end_date - timedelta(days=365)).isoformat()
            date_range_str = "Last Year"
        elif choice == 'm':
            console.print("\n--- [bold]Other Lifts[/bold] ---")
            if not best_other_lifts:
                console.print("No other PRs found in this period.")
            else:
                for lift_name in sorted(best_other_lifts.keys()):
                    pr = best_other_lifts[lift_name]
                    display_name = lift_name.title()
                    weight = float(pr.get("weight", 0) or 0)
                    reps = pr.get("reps")
                    date_str = pr.get("date", "N/A")
                    unit = pr.get("weight_type", "units")
                    if reps == 1:
                        console.print(f"{display_name:<25} [bold green]{weight:7.1f}[/bold green] {unit} on {date_str}")
                    else:
                        e1rm = wendler_1rm(weight, reps)
                        console.print(f"{display_name:<25} [bold yellow]{e1rm:7.1f}[/bold yellow] {unit} on {date_str} ([dim]estimated from {weight} {unit} x {reps}[/dim])")
            console.input("\nPress Enter to continue...")
