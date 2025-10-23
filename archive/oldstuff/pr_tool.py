import os
from datetime import datetime, timedelta, date
from rich.console import Console
from rich.text import Text
from api_client import get_workout_history

console = Console()

# --- Configuration ---
MAIN_LIFTS = ["squat", "bench press", "deadlift", "press"]

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def wendler_1rm(weight, reps):
    """Calculates estimated 1RM using the Wendler formula."""
    if not isinstance(reps, (int, float)) or reps <= 1:
        return weight
    return (weight * reps * 0.0333) + weight

def calculate_wilks(total_kg, bodyweight_kg, gender):
    """Calculates the Wilks score."""
    x = bodyweight_kg
    # Coefficients for the formula
    if gender.lower() == 'male':
        a, b, c, d, e, f = -216.0475144, 16.2606339, -0.002388645, -0.00113732, 7.01863E-06, -1.291E-08
    elif gender.lower() == 'female':
        a, b, c, d, e, f = 594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913, 4.731582E-05, -9.054E-08
    else:
        return 0

    denominator = a + (b*x) + (c*x**2) + (d*x**3) + (e*x**4) + (f*x**5)
    if denominator == 0:
        return 0
        
    return total_kg * (500 / denominator)

def process_workout_history(workouts, start_date=None, end_date=None):
    """Processes workout history to find the best e1RM for every exercise in a date range."""
    best_performances = {}
    for workout in workouts:
        workout_date_str = workout.get("workout_date")
        if not workout_date_str:
            continue
        workout_date = datetime.strptime(workout_date_str, "%Y-%m-%d").date()
        if (start_date and workout_date < start_date) or (end_date and workout_date > end_date):
            continue

        for exercise in workout.get("assigned_exercises", []):
            lift_name = exercise.get("exercise", {}).get("name", "Unknown").lower()
            for assigned_set in exercise.get("assigned_sets", []):
                for actual_set in assigned_set.get("actual_sets", []):
                    weight = float(actual_set.get("weight", 0) or 0)
                    reps = actual_set.get("reps")
                    if not reps or not weight:
                        continue
                    
                    estimated_1rm = wendler_1rm(weight, reps)
                    if lift_name not in best_performances or estimated_1rm > best_performances[lift_name]['e1rm']:
                        best_performances[lift_name] = {
                            'e1rm': estimated_1rm, 'weight': weight, 'reps': reps,
                            'unit': workout.get("weight_type", "lbs"), 'date': workout.get("workout_date")
                        }
    return best_performances

def display_prs(main_lifts, other_lifts, date_range_str, show_other=False):
    """A pure display function that only prints the results."""
    clear_screen()
    console.print(f"--- [bold]Best Lift Performances[/bold] ---")
    console.print(f"---  [cyan]Date Range: {date_range_str}[/cyan]  ---\n")

    console.print("--- [bold]Main Lifts[/bold] ---")
    for lift in MAIN_LIFTS:
        perf = main_lifts.get(lift)
        lift_display_name = lift.replace(" press", " Press").title()
        if perf:
            console.print(f"{lift_display_name:<15} [bold green]{perf['e1rm']:.1f}[/bold green] {perf['unit']} on {perf['date']} ([dim]from {perf['weight']} {perf['unit']} x {perf['reps']}[/dim])")
        else:
            console.print(f"{lift_display_name:<15} [dim]No performance found[/dim]")

    if show_other:
        console.print("\n--- [bold]Other Lifts[/bold] ---")
        if not other_lifts:
            console.print("No other lift performances found in this period.")
        else:
            for lift_name in sorted(other_lifts.keys()):
                perf = other_lifts[lift_name]
                display_name = lift_name.title()
                console.print(f"{display_name:<25} [bold green]{perf['e1rm']:.1f}[/bold green] {perf['unit']} on {perf['date']} ([dim]from {perf['weight']} {perf['unit']} x {perf['reps']}[/dim])")

def run_pr_analyzer(token, client):
    """Main analysis loop for the PR tool with Wilks score functionality."""
    client_name = client['full_name']
    client_gender = None
    
    workouts = get_workout_history(token, client)
    if not workouts:
        console.input("\nCould not load workout history. Press Enter to return.")
        return

    while True:
        clear_screen()
        console.print(f"Analyzing PRs for: [bold green]{client_name}[/bold green]")
        console.print("\n--- [bold]Select a Date Range[/bold] ---")
        console.print(Text(" [3] Last 3 Months"))
        console.print(Text(" [6] Last 6 Months"))
        console.print(Text(" [y] Last Year"))
        console.print(Text(" [a] All Time"))
        console.print(Text(" [c] Custom Range"))
        console.print(Text(" [q] Back to tool menu"))
        choice = console.input("> ").lower()

        start_date, end_date = None, None
        today = date.today()
        date_range_str = "All Time"

        if choice == 'q':
            return
        elif choice == 'a':
            pass
        elif choice == '3':
            start_date = today - timedelta(days=90)
            date_range_str = "Last 3 Months"
        elif choice == '6':
            start_date = today - timedelta(days=180)
            date_range_str = "Last 6 Months"
        elif choice == 'y':
            start_date = today - timedelta(days=365)
            date_range_str = "Last Year"
        elif choice == 'c':
            try:
                start_str = console.input("Enter start date (YYYY-MM-DD): ")
                end_str = console.input("Enter end date   (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                date_range_str = f"Custom ({start_date} to {end_date})"
            except ValueError:
                console.input("\n[red]Invalid date format. Press Enter to try again.[/red]")
                continue
        else:
            console.input("[red]Invalid option. Press Enter to try again.[/red]")
            continue

        best_performances = process_workout_history(workouts, start_date, end_date)
        main_lift_performances = {k: v for k, v in best_performances.items() if k in MAIN_LIFTS}
        other_lift_performances = {k: v for k, v in best_performances.items() if k not in MAIN_LIFTS}
        
        show_other = False
        while True:
            display_prs(main_lift_performances, other_lift_performances, date_range_str, show_other=show_other)
            
            prompt_parts = ["[n]ew date range", "[w]ilks score", "[q]uit"]
            if other_lift_performances:
                prompt_parts.insert(-1, "[m]ore lifts" if not show_other else "[h]ide other lifts")
            
            print("\n" + "-"*50)
            print(' | '.join(prompt_parts))
            action = input("> ").lower()
            
            if action == 'n':
                break
            elif action == 'q':
                return
            elif action == 'm' and other_lift_performances:
                show_other = True
            elif action == 'h' and other_lift_performances:
                show_other = False
            elif action == 'w':
                squat_pr = main_lift_performances.get("squat", {}).get("e1rm", 0)
                bench_pr = main_lift_performances.get("bench press", {}).get("e1rm", 0)
                deadlift_pr = main_lift_performances.get("deadlift", {}).get("e1rm", 0)
    
                if not all([squat_pr, bench_pr, deadlift_pr]):
                    console.print("\n[bold red]Cannot calculate Wilks. Missing performance for Squat, Bench, or Deadlift in this period.[/bold red]")
                    console.input("Press Enter to continue...")
                    continue

                if not client_gender:
                    while True:
                        gender_input = console.input("Enter client gender (m/f): ").lower()
                        if gender_input in ['m', 'f']:
                            client_gender = 'male' if gender_input == 'm' else 'female'
                            break
                        console.print("[red]Invalid input. Please enter 'm' or 'f'.[/red]")

                try:
                    bw_input = console.input(f"Enter bodyweight for Wilks Score (e.g., 180 lbs or 82 kg): ").lower()
                    
                    if 'kg' in bw_input:
                        bw_value = float(bw_input.replace('kg', '').strip())
                        bodyweight_kg = bw_value
                        bodyweight_lbs = bw_value * 2.20462
                    else:
                        bw_value = float(bw_input.replace('lbs', '').strip())
                        bodyweight_lbs = bw_value
                        bodyweight_kg = bw_value * 0.453592
                
                except (ValueError, IndexError):
                    console.print(f"\n[bold red]Invalid input. Please enter a number, optionally followed by 'lbs' or 'kg'.[/bold red]")
                    console.input("Press Enter to continue...")
                    continue
                
                total_lbs = squat_pr + bench_pr + deadlift_pr
                total_kg = total_lbs * 0.453592
                score = calculate_wilks(total_kg, bodyweight_kg, client_gender)

                console.print("\n--- [bold]Estimated Wilks Score[/bold] ---")
                console.print(f"Bodyweight:      {bodyweight_lbs:.1f} lbs ({bodyweight_kg:.1f} kg)")
                console.print(f"e1RM Total:      {total_lbs:.1f} lbs ({total_kg:.1f} kg)")
                console.print(f"Client Gender:   {client_gender.title()}")
                console.print(f"Estimated Wilks: [bold green]{score:.2f}[/bold green]")
                console.input("\nPress Enter to continue...")

            else:
                input("Invalid choice. Press Enter to continue...")
