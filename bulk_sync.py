#!/usr/bin/env python3
"""
Overnight Bulk Sync Tool - Downloads all client data in background
Syncs workouts and unified feed data for all clients
"""
import os
import sys
import time
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.table import Table
from rich.text import Text

# Import your existing efficient sync functions
from api_client import get_access_token, get_clients, get_workout_history
from feed_tool import fetch_and_aggregate_data
from directory_migration import get_client_dir

console = Console()

class BulkSyncManager:
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()
        self.start_time = None
        self.total_clients = 0
        self.completed_clients = 0
        
    def sync_single_client(self, token, user_id, client):
        """Sync workout data and feed data for a single client"""
        client_id = client['id']
        client_name = client['full_name']
        
        result = {
            'client_id': client_id,
            'client_name': client_name,
            'status': 'starting',
            'workouts_synced': 0,
            'workouts_new': 0,
            'feed_events': 0,
            'error': None,
            'start_time': time.time(),
            'end_time': None
        }
        
        try:
            # Verbose logging - always show what we're doing
            console.print(f"🔄 [cyan]Starting sync for {client_name}[/cyan]")
            
            # Update status
            result['status'] = 'syncing_workouts'
            self._update_result(client_id, result)
            console.print(f"  💪 [yellow]Syncing workouts for {client_name}...[/yellow]")
            
            # Sync workouts using your existing efficient system
            workouts = get_workout_history(token, client, force_refresh=False)
            result['workouts_synced'] = len(workouts) if workouts else 0
            console.print(f"  ✅ [green]{client_name}: {result['workouts_synced']} workouts synced[/green]")
            
            # Update status
            result['status'] = 'syncing_feed'
            self._update_result(client_id, result)
            console.print(f"  📡 [yellow]Syncing feed data for {client_name}...[/yellow]")
            
            # Sync feed data (this includes incremental workout updates and messages)
            feed_data_lock = threading.Lock()
            feed_data = {"events": [], "is_refreshing": True}
            
            # Use your existing feed aggregation
            fetch_and_aggregate_data(token, client, feed_data_lock, feed_data)
            
            with feed_data_lock:
                result['feed_events'] = len(feed_data.get('events', []))
            
            console.print(f"  📊 [green]{client_name}: {result['feed_events']} feed events synced[/green]")
            console.print(f"🎉 [bold green]{client_name} sync completed![/bold green]")
            
            result['status'] = 'completed'
            result['end_time'] = time.time()
            
        except Exception as e:
            console.print(f"❌ [bold red]ERROR syncing {client_name}: {str(e)}[/bold red]")
            result['status'] = 'error'
            result['error'] = str(e)
            result['end_time'] = time.time()
        
        self._update_result(client_id, result)
        return result
    
    def _update_result(self, client_id, result):
        """Thread-safe result updating"""
        with self.lock:
            self.results[client_id] = result.copy()
            if result['status'] in ['completed', 'error']:
                self.completed_clients += 1

def create_progress_display(sync_manager):
    """Create a rich display for progress monitoring"""
    def make_progress_table():
        table = Table(title="🌙 Overnight Bulk Sync Progress")
        table.add_column("Client", style="cyan", width=25)
        table.add_column("Status", style="yellow", width=15)
        table.add_column("Workouts", style="green", width=10)
        table.add_column("Feed Events", style="blue", width=12)
        table.add_column("Time", style="magenta", width=10)
        table.add_column("Error", style="red", width=30)
        
        with sync_manager.lock:
            results = sync_manager.results.copy()
        
        for client_id, result in results.items():
            client_name = result['client_name'][:23] + "..." if len(result['client_name']) > 25 else result['client_name']
            
            # Status with emoji
            status_map = {
                'starting': '🔄 Starting',
                'syncing_workouts': '💪 Workouts',
                'syncing_feed': '📡 Feed',
                'completed': '✅ Done',
                'error': '❌ Error'
            }
            status = status_map.get(result['status'], result['status'])
            
            # Time calculation
            if result['start_time']:
                if result['end_time']:
                    duration = result['end_time'] - result['start_time']
                    time_str = f"{duration:.1f}s"
                else:
                    duration = time.time() - result['start_time']
                    time_str = f"{duration:.1f}s"
            else:
                time_str = "-"
            
            # Workouts and events
            workouts_str = str(result['workouts_synced']) if result['workouts_synced'] > 0 else "-"
            events_str = str(result['feed_events']) if result['feed_events'] > 0 else "-"
            
            # Error (truncated)
            error_str = result['error'][:28] + "..." if result['error'] and len(result['error']) > 30 else (result['error'] or "-")
            
            table.add_row(
                client_name,
                status,
                workouts_str,
                events_str,
                time_str,
                error_str
            )
        
        return table
    
    return make_progress_table

def run_bulk_sync(max_workers=4, force_refresh=False):
    """Run the bulk sync operation"""
    console.print(Panel.fit("🌙 [bold blue]Overnight Bulk Sync Starting[/bold blue] 🌙", border_style="blue"))
    
    # Get authentication
    console.print("🔐 [bold yellow]Authenticating...[/bold yellow]")
    token, user_id = get_access_token()
    if not token or not user_id:
        console.print("❌ [red]Authentication failed. Exiting.[/red]")
        return False
    console.print("✅ [green]Authentication successful![/green]")
    
    # Get all clients
    console.print("👥 [bold yellow]Fetching client list...[/bold yellow]")
    clients = get_clients(token, user_id)
    if not clients:
        console.print("❌ [red]No clients found. Exiting.[/red]")
        return False
    
    console.print(f"📋 [bold green]Found {len(clients)} clients to sync:[/bold green]")
    for i, client in enumerate(clients, 1):
        console.print(f"  {i:2d}. {client['full_name']}")
    
    # Initialize sync manager
    sync_manager = BulkSyncManager()
    sync_manager.total_clients = len(clients)
    sync_manager.start_time = time.time()
    
    # Initialize results
    for client in clients:
        sync_manager.results[client['id']] = {
            'client_id': client['id'],
            'client_name': client['full_name'],
            'status': 'queued',
            'workouts_synced': 0,
            'workouts_new': 0,
            'feed_events': 0,
            'error': None,
            'start_time': None,
            'end_time': None
        }
    
    console.print(f"🚀 [bold blue]Starting sync with {max_workers} parallel workers...[/bold blue]")
    console.print("📊 [dim]Live progress table will update below...[/dim]\n")
    
    # Create progress display
    progress_table_fn = create_progress_display(sync_manager)
    
    # Run sync with live progress display
    with Live(progress_table_fn(), refresh_per_second=2) as live:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all sync tasks
            future_to_client = {
                executor.submit(sync_manager.sync_single_client, token, user_id, client): client
                for client in clients
            }
            
            # Wait for completion
            for future in as_completed(future_to_client):
                client = future_to_client[future]
                try:
                    result = future.result()
                    # Result already stored by sync_single_client
                    # Show completion message
                    duration = result['end_time'] - result['start_time'] if result['end_time'] else 0
                    if result['status'] == 'completed':
                        console.print(f"✨ [bold green]{client['full_name']} completed in {duration:.1f}s[/bold green]")
                except Exception as e:
                    console.print(f"❌ [red]Unexpected error for {client['full_name']}: {e}[/red]")
                
                # Update display
                live.update(progress_table_fn())
    
    # Final summary
    end_time = time.time()
    total_duration = end_time - sync_manager.start_time
    
    with sync_manager.lock:
        results = sync_manager.results.copy()
    
    # Calculate statistics
    completed = sum(1 for r in results.values() if r['status'] == 'completed')
    errored = sum(1 for r in results.values() if r['status'] == 'error')
    total_workouts = sum(r['workouts_synced'] for r in results.values())
    total_events = sum(r['feed_events'] for r in results.values())
    
    # Print final summary
    console.print("\n" + "="*60)
    console.print(Panel.fit(f"""
[bold green]🎉 Bulk Sync Complete! 🎉[/bold green]

📊 [bold]Summary:[/bold]
  • Total Clients: {len(clients)}
  • ✅ Successful: {completed}
  • ❌ Errors: {errored}
  • 💪 Total Workouts Synced: {total_workouts:,}
  • 📡 Total Feed Events: {total_events:,}
  • ⏱️ Total Time: {total_duration/60:.1f} minutes

🏠 All data saved to: ~/Turnkey/
""", border_style="green"))
    
    # Show errors if any
    if errored > 0:
        console.print("\n❌ [bold red]Clients with errors:[/bold red]")
        for result in results.values():
            if result['status'] == 'error':
                console.print(f"  • {result['client_name']}: {result['error']}")
    
    return completed > 0

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Overnight bulk sync for all client data")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of concurrent workers (default: 4)")
    parser.add_argument("--force", "-f", action="store_true", help="Force refresh all data (ignore cache)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced without actually syncing")
    
    args = parser.parse_args()
    
    if args.dry_run:
        console.print("🔍 [yellow]Dry run mode - checking clients...[/yellow]")
        token, user_id = get_access_token()
        if token:
            clients = get_clients(token, user_id)
            console.print(f"📋 Would sync {len(clients)} clients:")
            for i, client in enumerate(clients, 1):
                console.print(f"  {i:2d}. {client['full_name']}")
        return
    
    # Show current time for reference
    console.print(f"🕐 [dim]Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    
    # Confirm before starting
    console.print("\n🌙 [bold yellow]About to start overnight bulk sync...[/bold yellow]")
    console.print("This will sync workout data and feed data for ALL clients.")
    console.print("The process may take a while depending on the amount of data.")
    console.print("[bold]Progress will be shown continuously during the sync.[/bold]")
    
    if input("\n🚀 Ready to start? [y/N]: ").lower() != 'y':
        console.print("❌ Sync cancelled.")
        return
    
    console.print("\n🎬 [bold green]Starting sync...[/bold green]")
    start_time = datetime.now()
    console.print(f"🕐 [dim]Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")
    
    # Run the sync
    success = run_bulk_sync(max_workers=args.workers, force_refresh=args.force)
    
    end_time = datetime.now()
    console.print(f"\n🕐 [dim]Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    
    if success:
        console.print("\n✨ [bold green]Sweet dreams! Your data is now up to date.[/bold green] ✨")
        console.print(f"🏠 [dim]All data saved to: {os.path.expanduser('~/Turnkey/')}[/dim]")
    else:
        console.print("\n😴 [yellow]Sync completed with some issues. Check the errors above.[/yellow]")

if __name__ == "__main__":
    main()