# settings.py (complete updated version)
import json
import os
import platform
from rich.console import Console
from cryptography.fernet import Fernet
import base64
import getpass  # Added for secure password input

console = Console()

SETTINGS_FILE = os.path.expanduser("~/.turnkey_coach_settings.json")

def load_or_init_settings():
    """Load settings or prompt for editor prefs and credentials like a nosy therapist."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    
    # First-time setup: Editor configuration (original code, unchanged)
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
    
    # New: Prompt for email and password (added HERE, after editor setup)
    console.print("\n[bold]Enter your Turnkey Coach credentials (stored securely for auto-login):[/bold]")
    email = console.input("Email: ").strip()
    password = getpass.getpass("Password: ")  # Secure input, no echo
    
    # Generate encryption key for password
    key = Fernet.generate_key()
    encoded_key = base64.urlsafe_b64encode(key).decode('utf-8')  # Store as string
    
    # Encrypt password
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode()).decode('utf-8')
    
    # Save editor and credentials together
    settings = {
        'default_editor': default_cmd,
        'email': email,
        'encrypted_password': encrypted_password,
        'encryption_key': encoded_key  # Store key (tradeoff for simplicity)
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    console.print(f"[green]Settings saved to {SETTINGS_FILE}. You're welcome.[/green]")
    return settings

# Original get_default_editor function (unchanged, was at line 39)
def get_default_editor():
    """Grab the editor command from settings. Returns a list for subprocess.run."""
    settings = load_or_init_settings()
    return settings.get('default_editor', ['nvim'])  # Ultimate fallback

# New: Helper to retrieve and decrypt credentials
def get_stored_credentials():
    """Retrieve and decrypt stored email/password."""
    settings = load_or_init_settings()
    email = settings.get('email')
    encrypted_password = settings.get('encrypted_password')
    encryption_key = settings.get('encryption_key')
    
    if not all([email, encrypted_password, encryption_key]):
        return None, None
    
    try:
        key = base64.urlsafe_b64decode(encryption_key.encode('utf-8'))
        fernet = Fernet(key)
        password = fernet.decrypt(encrypted_password.encode()).decode('utf-8')
        return email, password
    except Exception as e:
        console.print(f"[red]Error decrypting credentials: {e}. Please re-enter in settings.[/red]")
        return None, None

# New: Helper to clear credentials (for logout)
def clear_stored_credentials():
    """Clear stored credentials for logout."""
    settings = load_or_init_settings()
    settings.pop('email', None)
    settings.pop('encrypted_password', None)
    settings.pop('encryption_key', None)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
    console.print("[green]Credentials cleared. You'll need to re-enter on next login.[/green]")

# New: Helper to retrieve and decrypt LLM credentials
def get_llm_credentials():
    """Retrieve and decrypt stored LLM provider and API key."""
    settings = load_or_init_settings()
    provider = settings.get('llm_provider')
    encrypted_key = settings.get('llm_encrypted_key')
    encryption_key = settings.get('encryption_key')
    
    if not all([provider, encrypted_key, encryption_key]):
        return None, None
    
    try:
        key = base64.urlsafe_b64decode(encryption_key.encode('utf-8'))
        fernet = Fernet(key)
        api_key = fernet.decrypt(encrypted_key.encode()).decode('utf-8')
        return provider, api_key
    except Exception as e:
        console.print(f"[red]Error decrypting LLM key: {e}. Please re-enter.[/red]")
        return None, None
