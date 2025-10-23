#!/usr/bin/env python3
"""
Display utilities for handling differences between source and bundled app environments.
Provides dual-mode progress displays that work in both terminal and bundled contexts.
"""
import sys
import time
from rich.console import Console
from rich.live import Live

console = Console()


def is_bundled():
    """
    Detect if running as a PyInstaller bundle.

    Returns:
        bool: True if running as bundled app, False if running from source
    """
    return getattr(sys, 'frozen', False)


def safe_input(prompt=""):
    """
    Safe input that works in both source and bundled modes.

    Args:
        prompt (str): Input prompt to display

    Returns:
        str: User input
    """
    try:
        # Try Rich console input first (works in proper terminals)
        return console.input(prompt)
    except (EOFError, KeyboardInterrupt, OSError):
        # Fallback to basic input for bundled apps with limited terminal support
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""


class BulkSyncProgressTracker:
    """Base class for bulk sync progress tracking."""

    def __init__(self, sync_manager):
        self.sync_manager = sync_manager

    def run(self, executor, clients, token, user_id):
        """Run the sync with progress tracking. To be implemented by subclasses."""
        raise NotImplementedError


class LiveBulkProgress(BulkSyncProgressTracker):
    """
    Rich.Live-based progress tracker for source code execution.
    Beautiful real-time table updates with colors and emojis.
    """

    def create_progress_table(self):
        """Create a rich table for progress monitoring."""
        from rich.table import Table

        table = Table(title="🌙 Overnight Bulk Sync Progress")
        table.add_column("Client", style="cyan", width=25)
        table.add_column("Status", style="yellow", width=15)
        table.add_column("Workouts", style="green", width=10)
        table.add_column("Feed Events", style="blue", width=12)
        table.add_column("Time", style="magenta", width=10)
        table.add_column("Error", style="red", width=30)

        with self.sync_manager.lock:
            results = self.sync_manager.results.copy()

        for client_id, result in results.items():
            client_name = result['client_name'][:23] + "..." if len(result['client_name']) > 25 else result['client_name']

            # Status with emoji
            status_map = {
                'queued': '⏳ Queued',
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

    def run(self, executor, clients, token, user_id):
        """Run sync with Rich.Live display."""
        from concurrent.futures import as_completed

        # Run sync with live progress display
        with Live(self.create_progress_table(), refresh_per_second=2) as live:
            # Submit all sync tasks
            future_to_client = {
                executor.submit(self.sync_manager.sync_single_client, token, user_id, client): client
                for client in clients
            }

            # Wait for completion
            for future in as_completed(future_to_client):
                client = future_to_client[future]
                try:
                    result = future.result()
                    # Result already stored by sync_single_client
                except Exception as e:
                    # Store error in results instead of printing
                    self.sync_manager.results[client['id']]['status'] = 'error'
                    self.sync_manager.results[client['id']]['error'] = f"Unexpected error: {e}"

                # Update display
                live.update(self.create_progress_table())


class SimpleBulkProgress(BulkSyncProgressTracker):
    """
    Simple print-based progress tracker for bundled apps.
    No Rich.Live, just sequential console output.
    """

    def run(self, executor, clients, token, user_id):
        """Run sync with simple print-based progress."""
        from concurrent.futures import as_completed

        console.print("\n📊 [bold]Progress:[/bold]")
        console.print("[dim]Syncing clients in parallel...[/dim]\n")

        # Submit all sync tasks
        future_to_client = {
            executor.submit(self.sync_manager.sync_single_client, token, user_id, client): client
            for client in clients
        }

        # Wait for completion and print updates
        completed = 0
        for future in as_completed(future_to_client):
            client = future_to_client[future]
            completed += 1

            try:
                result = future.result()

                if result['status'] == 'completed':
                    console.print(
                        f"✅ [{completed}/{len(clients)}] {result['client_name'][:40]} - "
                        f"Completed ({result['workouts_synced']} workouts, {result['feed_events']} events)"
                    )
                elif result['status'] == 'error':
                    error_msg = result['error'][:50] + "..." if len(result['error']) > 50 else result['error']
                    console.print(
                        f"❌ [{completed}/{len(clients)}] {result['client_name'][:40]} - "
                        f"Error: {error_msg}"
                    )

            except Exception as e:
                # Store error and print
                self.sync_manager.results[client['id']]['status'] = 'error'
                self.sync_manager.results[client['id']]['error'] = f"Unexpected error: {e}"
                console.print(
                    f"❌ [{completed}/{len(clients)}] {client['full_name'][:40]} - "
                    f"Unexpected error: {e}"
                )


def create_progress_tracker(sync_manager):
    """
    Factory function to create appropriate progress tracker based on environment.

    Args:
        sync_manager: BulkSyncManager instance

    Returns:
        BulkSyncProgressTracker: Appropriate tracker for the environment
    """
    if is_bundled():
        console.print("[dim]Running in bundled mode - using simple progress display[/dim]")
        return SimpleBulkProgress(sync_manager)
    else:
        return LiveBulkProgress(sync_manager)
