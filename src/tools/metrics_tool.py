"""
Metrics Tool for Turnkey Coach

Allows coaches to program and upload client metrics (weight, body fat %, measurements, etc.)
to the Turnkey Coach platform via API.
"""

import math
import os
from datetime import datetime, date, timedelta
from typing import Any, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.api_client import API_BASE_URL
from src.directory_migration import get_client_dir
from src.encoding_utils import safe_json_dump, safe_json_load
import requests

console = Console()

# Common metric types that coaches track
METRIC_TYPES = {
    "weight": {"name": "Body Weight", "unit": "lbs", "alt_unit": "kg", "api_metric_type": "decimal"},
    "body_fat": {"name": "Body Fat %", "unit": "%", "alt_unit": None, "api_metric_type": "decimal"},
    "waist": {"name": "Waist", "unit": "inches", "alt_unit": "cm", "api_metric_type": "decimal"},
    "chest": {"name": "Chest", "unit": "inches", "alt_unit": "cm", "api_metric_type": "decimal"},
    "arms": {"name": "Arms", "unit": "inches", "alt_unit": "cm", "api_metric_type": "decimal"},
    "thighs": {"name": "Thighs", "unit": "inches", "alt_unit": "cm", "api_metric_type": "decimal"},
    "sleep": {"name": "Sleep Hours", "unit": "hours", "alt_unit": None, "api_metric_type": "decimal"},
    "stress": {"name": "Stress Level", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "recovery": {"name": "Recovery Score", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "energy": {"name": "Energy Level", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "fatigue": {"name": "Fatigue", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "difficulty": {"name": "Difficulty", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "enjoyment": {"name": "Enjoyment", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "motivation": {"name": "Motivation", "unit": "1-10", "alt_unit": None, "api_metric_type": "scale", "scale_start": 1, "scale_end": 10},
    "duration": {"name": "Duration", "unit": "minutes", "alt_unit": None, "api_metric_type": "decimal"},
}

NUMERIC_UNITS = {
    "lbs",
    "lb",
    "kg",
    "kgs",
    "kilograms",
    "grams",
    "g",
    "%",
    "percent",
    "in",
    "inch",
    "inches",
    "cm",
    "centimeters",
    "mm",
    "hours",
    "mins",
    "minutes",
    "min",
    "seconds",
    "secs",
    "s",
    "bpm",
    "ms",
    "km",
    "miles",
    "steps",
}


def _normalise_metric_key(metric_key: str) -> str:
    """Return a lower-case metric key for internal lookups."""
    return (metric_key or "").strip().lower()


def _metric_display_name(metric_key: str) -> str:
    """Return a human-friendly name for the metric."""
    meta = METRIC_TYPES.get(metric_key)
    if meta and meta.get("name"):
        return meta["name"]
    return metric_key.replace("_", " ").title()


def _determine_api_metric_type(metric_key: str, value, unit: str, notes: str) -> str:
    """Determine the correct API metric_type (integer/decimal/short_text/long_text/scale)."""
    meta = METRIC_TYPES.get(metric_key, {})
    if meta.get("api_metric_type"):
        return meta["api_metric_type"]

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            if math.isfinite(float(value)) and float(value).is_integer():
                return "integer"
        except (OverflowError, ValueError, TypeError):
            pass
        return "decimal"

    if unit and unit.lower() in NUMERIC_UNITS:
        return "decimal"

    # Fall back to short_text for placeholders or textual notes
    return "short_text"


def build_metric_payload(metric_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map internal metric data to the payload expected by the API."""
    metric_key = _normalise_metric_key(metric_data.get("metric_type"))
    value = metric_data.get("value")
    unit = metric_data.get("unit") or ""
    notes = metric_data.get("notes") or ""

    payload: Dict[str, Any] = {
        "user_id": metric_data["user_id"],
        "metric_date": metric_data["metric_date"],
        "name": _metric_display_name(metric_key),
        "metric_type": _determine_api_metric_type(metric_key, value, unit, notes),
    }

    meta = METRIC_TYPES.get(metric_key, {})

    if payload["metric_type"] == "scale":
        payload["scale_start"] = meta.get("scale_start", 1)
        payload["scale_end"] = meta.get("scale_end", 10)

    # Decide unit: use explicit first, then default numeric ones (skip 1-10 scale units)
    unit_lower = unit.lower()
    if unit and unit_lower not in ["", "n/a"]:
        payload["unit"] = unit
    else:
        default_unit = meta.get("unit")
        if default_unit and payload["metric_type"] not in ("scale", "short_text", "long_text"):
            payload["unit"] = default_unit

    if notes:
        payload["notes"] = notes

    value_to_send = value
    if isinstance(value_to_send, str) and not value_to_send.strip():
        value_to_send = None

    if isinstance(value_to_send, (int, float)) and not isinstance(value_to_send, bool):
        try:
            if not math.isfinite(float(value_to_send)):
                value_to_send = None
        except (OverflowError, ValueError, TypeError):
            value_to_send = None

    if value_to_send is not None:
        if payload["metric_type"] in ("integer", "scale"):
            try:
                payload["value"] = int(round(float(value_to_send)))
            except (ValueError, TypeError):
                payload["value"] = value_to_send
        elif payload["metric_type"] == "decimal":
            try:
                payload["value"] = float(value_to_send)
            except (ValueError, TypeError):
                payload["value"] = value_to_send
        else:
            payload["value"] = value_to_send

    return payload


def get_client_metrics(token, client_id, start_date=None, end_date=None):
    """Fetch metrics for a client from the API.

    Args:
        token (str): Authentication token
        client_id (int): Client ID
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format

    Returns:
        list: List of metric dictionaries from API
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/api/v1/metrics"
    params = {"user_id": client_id}

    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    with console.status("[bold green]Fetching metrics from API...[/bold green]"):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            console.print(f"\n[bold red]Could not fetch metrics:[/bold red] {err}")
            return []


def upload_metric(token, metric_data):
    """Upload a single metric to the API.

    Args:
        token (str): Authentication token
        metric_data (dict): Metric data to upload
            Required fields: user_id, metric_date, metric_type
            Optional fields: value, notes, unit

    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{API_BASE_URL}/api/v1/metrics"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = build_metric_payload(metric_data)

    # Remove any blank optional fields that may slip through
    for optional_key in ("unit", "notes"):
        if payload.get(optional_key) in ("", None):
            payload.pop(optional_key, None)

    if payload.get("value") is None:
        payload.pop("value", None)

    placeholder = "value" not in payload

    try:
        action_word = "placeholder metric" if placeholder else "metric"
        metric_key = metric_data.get("metric_type") or payload.get("name")
        data_type = payload.get("metric_type")
        console.print(
            f"Uploading {action_word}: [cyan]{metric_key}[/cyan] "
            f"for [cyan]{metric_data.get('metric_date')}[/cyan] "
            f"(type: {data_type})..."
        )
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        if placeholder:
            console.print(f"✅ [bold green]Successfully uploaded placeholder metric![/bold green]")
        else:
            console.print(f"✅ [bold green]Successfully uploaded metric![/bold green]")
        return True
    except requests.exceptions.HTTPError as e:
        console.print(f"❌ [bold red]Upload failed.[/bold red] HTTP Error: {e.response.status_code}")
        console.print(f"[dim]API Response: {e.response.text}[/dim]")
        return False


def display_metrics(metrics, metric_type=None):
    """Display metrics in a formatted table.

    Args:
        metrics (list): List of metric dictionaries
        metric_type (str, optional): Filter by metric type
    """
    if metric_type:
        metrics = [m for m in metrics if m.get('metric_type') == metric_type]

    if not metrics:
        console.print("[yellow]No metrics found.[/yellow]")
        return

    # Sort by date
    metrics = sorted(metrics, key=lambda m: m.get('metric_date', ''), reverse=True)

    table = Table(title="Client Metrics", border_style="cyan")
    table.add_column("Date", style="dim", width=12)
    table.add_column("Metric", style="bold", width=20)
    table.add_column("Value", style="green", width=15)
    table.add_column("Notes", width=40)

    for metric in metrics[:20]:  # Show last 20 metrics
        metric_date = metric.get('metric_date', 'N/A')
        metric_name = METRIC_TYPES.get(metric.get('metric_type'), {}).get('name', metric.get('metric_type', 'Unknown'))
        raw_value = metric.get('value')
        value = "Pending" if raw_value in [None, ''] else raw_value
        unit = metric.get('unit', '')
        notes = metric.get('notes', '')

        table.add_row(
            metric_date,
            metric_name,
            f"{value} {unit}".strip(),
            notes[:40] if notes else ""
        )

    console.print(table)
    console.print(f"\n[dim]Showing {min(20, len(metrics))} of {len(metrics)} total metrics[/dim]")


def program_single_metric(token, client):
    """Interactive UI to program a single metric entry.

    Args:
        token (str): Authentication token
        client (dict): Client dictionary with 'id' and 'full_name'
    """
    console.print("\n[bold]Program Single Metric[/bold]\n")

    # Display metric types
    console.print("[bold]Available Metric Types:[/bold]")
    metric_list = list(METRIC_TYPES.keys())
    for i, metric_key in enumerate(metric_list, 1):
        info = METRIC_TYPES[metric_key]
        console.print(f"  [[bold]{i}[/bold]] {info['name']} ({info['unit']})")
    console.print("  [[bold]c[/bold]] Custom metric type")
    console.print("  [[bold]q[/bold]] Cancel")

    # Select metric type
    choice = console.input("\nSelect metric type > ").strip().lower()
    if choice == 'q':
        return

    if choice == 'c':
        metric_type = console.input("Enter custom metric type (e.g., 'resting_hr'): ").strip().lower()
        metric_name = console.input("Enter display name (e.g., 'Resting Heart Rate'): ").strip()
        unit = console.input("Enter unit (e.g., 'bpm'): ").strip()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(metric_list):
                metric_type = metric_list[idx]
                metric_info = METRIC_TYPES[metric_type]
                metric_name = metric_info['name']
                unit = metric_info['unit']
            else:
                console.print("[red]Invalid selection.[/red]")
                return
        except ValueError:
            console.print("[red]Invalid input.[/red]")
            return

    # Get date
    date_input = console.input(f"\nEnter date (YYYY-MM-DD) or press Enter for today: ").strip()
    if not date_input:
        metric_date = date.today().isoformat()
    else:
        try:
            # Validate date format
            datetime.strptime(date_input, "%Y-%m-%d")
            metric_date = date_input
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
            return

    # Get value
    value_input = console.input(f"Enter value ({unit}): ").strip()
    try:
        value = float(value_input)
    except ValueError:
        console.print("[red]Invalid value. Must be a number.[/red]")
        return

    # Get optional notes
    notes = console.input("Enter notes (optional): ").strip()

    # Confirm
    console.print(f"\n[bold]Confirm Metric Entry:[/bold]")
    console.print(f"  Client: {client['full_name']}")
    console.print(f"  Date: {metric_date}")
    console.print(f"  Metric: {metric_name}")
    console.print(f"  Value: {value} {unit}")
    if notes:
        console.print(f"  Notes: {notes}")

    confirm = console.input("\nUpload this metric? (y/n) > ").lower()
    if confirm != 'y':
        console.print("[yellow]Upload cancelled.[/yellow]")
        return

    # Build metric data
    metric_data = {
        "user_id": client['id'],
        "metric_date": metric_date,
        "metric_type": metric_type,
        "value": value,
        "unit": unit
    }
    if notes:
        metric_data["notes"] = notes

    # Upload
    success = upload_metric(token, metric_data)
    if success:
        console.input("\nPress Enter to continue.")


def program_bulk_metrics(token, client):
    """Interactive UI to program multiple metrics from a file or manual entry.

    Args:
        token (str): Authentication token
        client (dict): Client dictionary with 'id' and 'full_name'
    """
    console.print("\n[bold]Program Bulk Metrics[/bold]\n")
    console.print("You can enter multiple metrics in the following format:")
    console.print("[dim]YYYY-MM-DD, metric_type, value, unit, notes (optional)[/dim]\n")
    console.print("Example:")
    console.print("[dim]2025-10-01, weight, 180, lbs, feeling good[/dim]")
    console.print("[dim]2025-10-01, body_fat, 15.5, %, post-workout[/dim]\n")

    console.print("Enter metrics (one per line). Type 'done' when finished:\n")

    metrics_to_upload = []
    line_num = 1

    while True:
        line = console.input(f"[{line_num}] > ").strip()

        if line.lower() == 'done':
            break

        if not line:
            continue

        # Parse line: date, metric_type, value, unit, notes
        parts = [p.strip() for p in line.split(',')]

        if len(parts) < 4:
            console.print(f"[red]Error on line {line_num}: Need at least date, metric_type, value, unit[/red]")
            continue

        metric_date = parts[0]
        metric_type = parts[1]
        try:
            value = float(parts[2])
        except ValueError:
            console.print(f"[red]Error on line {line_num}: Value must be a number[/red]")
            continue

        unit = parts[3]
        notes = parts[4] if len(parts) > 4 else ""

        # Validate date
        try:
            datetime.strptime(metric_date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Error on line {line_num}: Invalid date format. Use YYYY-MM-DD[/red]")
            continue

        metric_data = {
            "user_id": client['id'],
            "metric_date": metric_date,
            "metric_type": metric_type,
            "value": value,
            "unit": unit
        }
        if notes:
            metric_data["notes"] = notes

        metrics_to_upload.append(metric_data)
        console.print(f"[green]✓ Added {metric_type}: {value} {unit} on {metric_date}[/green]")
        line_num += 1

    if not metrics_to_upload:
        console.print("[yellow]No metrics to upload.[/yellow]")
        console.input("Press Enter to continue.")
        return

    # Confirm
    console.print(f"\n[bold]Ready to upload {len(metrics_to_upload)} metrics:[/bold]")
    for m in metrics_to_upload:
        value = m.get('value')
        unit = m.get('unit') or ''
        if value in [None, '']:
            summary_value = "Pending"
        else:
            summary_value = value
        display = f"{summary_value} {unit}".strip()
        console.print(f"  {m['metric_date']}: {m['metric_type']} = {display}")

    confirm = console.input("\nUpload these metrics? (y/n) > ").lower()
    if confirm != 'y':
        console.print("[yellow]Upload cancelled.[/yellow]")
        console.input("Press Enter to continue.")
        return

    # Upload all
    success_count = 0
    for metric_data in metrics_to_upload:
        if upload_metric(token, metric_data):
            success_count += 1

    console.print(f"\n[bold green]Uploaded {success_count} of {len(metrics_to_upload)} metrics successfully.[/bold green]")
    console.input("Press Enter to continue.")


def view_metrics(token, client):
    """View existing metrics for a client.

    Args:
        token (str): Authentication token
        client (dict): Client dictionary with 'id' and 'full_name'
    """
    console.print("\n[bold]View Client Metrics[/bold]\n")
    console.print("[bold]Date Range:[/bold]")
    console.print("  [bold]1.[/bold] Last 30 Days")
    console.print("  [bold]2.[/bold] Last 90 Days")
    console.print("  [bold]3.[/bold] Last Year")
    console.print("  [bold]4.[/bold] All Time")
    console.print("  [bold]5.[/bold] Custom Range")
    console.print("  [bold]q.[/bold] Back")

    choice = console.input("\n> ").strip().lower()

    if choice == 'q':
        return

    start_date, end_date = None, None
    today = date.today()

    if choice == '1':
        start_date = (today - timedelta(days=30)).isoformat()
    elif choice == '2':
        start_date = (today - timedelta(days=90)).isoformat()
    elif choice == '3':
        start_date = (today - timedelta(days=365)).isoformat()
    elif choice == '4':
        pass  # All time - no date filter
    elif choice == '5':
        try:
            start_date = console.input("Enter start date (YYYY-MM-DD): ").strip()
            end_date = console.input("Enter end date (YYYY-MM-DD): ").strip()
            # Validate
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date format.[/red]")
            console.input("Press Enter to continue.")
            return
    else:
        console.print("[red]Invalid choice.[/red]")
        console.input("Press Enter to continue.")
        return

    # Fetch and display
    metrics = get_client_metrics(token, client['id'], start_date, end_date)

    if not metrics:
        console.print("[yellow]No metrics found for this date range.[/yellow]")
        console.input("Press Enter to continue.")
        return

    display_metrics(metrics)

    # Option to filter by type
    console.print("\n[bold]Filter Options:[/bold]")
    console.print("  [bold]f.[/bold] Filter by metric type")
    console.print("  [bold]Enter.[/bold] Back to menu")

    filter_choice = console.input("\n> ").strip().lower()

    if filter_choice == 'f':
        console.print("\n[bold]Select metric type to filter:[/bold]")
        metric_list = list(set(m.get('metric_type') for m in metrics))
        for i, mt in enumerate(metric_list, 1):
            console.print(f"  [[bold]{i}[/bold]] {mt}")

        type_choice = console.input("\n> ").strip()
        try:
            idx = int(type_choice) - 1
            if 0 <= idx < len(metric_list):
                filtered_type = metric_list[idx]
                display_metrics(metrics, metric_type=filtered_type)
        except ValueError:
            pass

    console.input("\nPress Enter to continue.")


def run_metrics_tool(token, client):
    """Main entry point for the metrics tool.

    Args:
        token (str): Authentication token
        client (dict): Client dictionary with 'id' and 'full_name'
    """
    while True:
        from src.api_client import clear_screen
        clear_screen()
        console.print(Panel(f"[bold]Metrics Tool[/bold] - {client['full_name']}", expand=False))

        console.print("\n[bold]Options:[/bold]")
        console.print("  [bold]1.[/bold] Program Single Metric")
        console.print("  [bold]2.[/bold] Program Bulk Metrics")
        console.print("  [bold]3.[/bold] View Client Metrics")
        console.print("  [bold]q.[/bold] Back to Tool Menu")

        choice = console.input("\n> ").strip().lower()

        if choice == '1':
            program_single_metric(token, client)
        elif choice == '2':
            program_bulk_metrics(token, client)
        elif choice == '3':
            view_metrics(token, client)
        elif choice == 'q':
            break
        else:
            console.print("[red]Invalid choice.[/red]")
            console.input("Press Enter to continue.")
