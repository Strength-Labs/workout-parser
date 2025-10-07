import json
import os
import platform
from rich.console import Console

console = Console()

SETTINGS_FILE = os.path.expanduser("~/.turnkey_coach_settings.json")

def load_or_init_settings():
    """Load settings or prompt for editor prefs like a nosy therapist."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    
    # First-time setup: Be annoyingly helpful
    os_name = platform.system().lower()
    defaults = {
        'windows': ['notepad.exe'],  # Boring but reliable
        'darwin': ['open', '-a', 'TextEdit', '-W'],  # Mac's guilty pleasure
        'linux': ['nvim']  # For the real heroes (you)
    }
    
    default_cmd = defaults.get(os_name, ['nvim'])  # Fallback to nvim for weird OSes
    console.print(f"\n[bold yellow]First-time setup detected on {platform.system()}.[/bold yellow]")
    console.print(f"[dim]Default editor for you: {' '.join(default_cmd)}[/dim]")
    choice = console.input("Want to change it? (y/n) > ").lower().strip()
    
    if choice == 'y':
        console.print("\n[bold]Enter your preferred editor command (e.g., 'code -w' for VS Code, or 'nvim' for masochists):[/bold]")
        custom_cmd = console.input("> ").strip().split()  # Split on spaces for multi-arg commands
        if custom_cmd:
            default_cmd = custom_cmd
            console.print(f"[green]Got it—editor set to {' '.join(default_cmd)}.[/green]")
    
    settings = {'default_editor': default_cmd}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    console.print(f"[green]Settings saved to {SETTINGS_FILE}. You're welcome.[/green]")
    return settings

def get_default_editor():
    """Grab the editor command from settings. Returns a list for subprocess.run."""
    settings = load_or_init_settings()
    return settings.get('default_editor', ['nvim'])  # Ultimate fallback
