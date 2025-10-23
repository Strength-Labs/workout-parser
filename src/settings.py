# settings.py (complete updated version)
import json
import os
import platform
from datetime import datetime
from rich.console import Console
from cryptography.fernet import Fernet
import base64
import getpass  # Added for secure password input
from src.encoding_utils import safe_open, safe_json_dump, safe_json_load

console = Console()

SETTINGS_FILE = os.path.expanduser("~/.turnkey_coach_settings.json")

# Workspace management functions
def get_workspace_settings():
    """Load workspace-based settings structure."""
    settings = safe_json_load(SETTINGS_FILE)
    if not settings:
        return create_initial_workspace_structure()
    
    # Migrate old format to workspace format if needed
    if 'workspaces' not in settings:
        settings = migrate_to_workspace_format(settings)
        safe_json_dump(settings, SETTINGS_FILE)
    
    return settings

def create_initial_workspace_structure():
    """Create initial workspace settings structure."""
    os_name = platform.system().lower()
    defaults = {
        'windows': ['notepad.exe'],
        'darwin': ['open', '-e'],
        'linux': ['nvim']
    }
    default_cmd = defaults.get(os_name, ['nvim'])
    
    return {
        'version': '2.0',
        'default_editor': default_cmd,
        'workspaces': {},
        'current_workspace': None,
        'encryption_key': base64.urlsafe_b64encode(Fernet.generate_key()).decode('utf-8')
    }

def migrate_to_workspace_format(old_settings):
    """Migrate old settings format to workspace-based format."""
    console.print("[yellow]Migrating settings to workspace format...[/yellow]")
    
    new_settings = {
        'version': '2.0',
        'default_editor': old_settings.get('default_editor', ['nvim']),
        'workspaces': {},
        'current_workspace': None,
        'encryption_key': old_settings.get('encryption_key', base64.urlsafe_b64encode(Fernet.generate_key()).decode('utf-8'))
    }
    
    # Migrate old credentials to a "default" workspace
    if old_settings.get('email') or old_settings.get('encrypted_password'):
        new_settings['workspaces']['default'] = {
            'name': 'Default Workspace',
            'email': old_settings.get('email'),
            'encrypted_password': old_settings.get('encrypted_password'),
            'company_name': None,
            'last_login': None,
            'llm_provider': old_settings.get('llm_provider'),
            'llm_encrypted_key': old_settings.get('llm_encrypted_key')
        }
        new_settings['current_workspace'] = 'default'
    
    return new_settings

def save_workspace_settings(settings):
    """Save workspace settings to file."""
    safe_json_dump(settings, SETTINGS_FILE)

def get_current_workspace():
    """Get the currently active workspace settings."""
    settings = get_workspace_settings()
    current_workspace_key = settings.get('current_workspace')
    if not current_workspace_key or current_workspace_key not in settings.get('workspaces', {}):
        return None

    # Return workspace data with the key included
    workspace_data = settings['workspaces'][current_workspace_key].copy()
    workspace_data['key'] = current_workspace_key
    return workspace_data

def create_workspace(workspace_key, name, email, password, company_name=None, llm_provider=None, llm_api_key=None):
    """Create a new workspace with encrypted credentials."""
    settings = get_workspace_settings()
    
    # Encrypt credentials
    key = base64.urlsafe_b64decode(settings['encryption_key'].encode('utf-8'))
    fernet = Fernet(key)
    
    encrypted_password = fernet.encrypt(password.encode()).decode('utf-8') if password else None
    encrypted_llm_key = fernet.encrypt(llm_api_key.encode()).decode('utf-8') if llm_api_key else None
    
    settings['workspaces'][workspace_key] = {
        'name': name,
        'email': email,
        'encrypted_password': encrypted_password,
        'company_name': company_name,
        'last_login': None,
        'llm_provider': llm_provider,
        'llm_encrypted_key': encrypted_llm_key
    }
    
    save_workspace_settings(settings)

def switch_workspace(workspace_key):
    """Switch to a different workspace."""
    settings = get_workspace_settings()
    if workspace_key in settings.get('workspaces', {}):
        settings['current_workspace'] = workspace_key
        # Update last login timestamp
        settings['workspaces'][workspace_key]['last_login'] = datetime.now().isoformat()
        save_workspace_settings(settings)
        return True
    return False

def list_workspaces():
    """Get list of all available workspaces."""
    settings = get_workspace_settings()
    workspaces = []
    for key, workspace in settings.get('workspaces', {}).items():
        workspaces.append({
            'key': key,
            'name': workspace.get('name', key),
            'email': workspace.get('email'),
            'company_name': workspace.get('company_name'),
            'last_login': workspace.get('last_login'),
            'llm_provider': workspace.get('llm_provider')
        })
    return workspaces

def delete_workspace(workspace_key):
    """Delete a workspace."""
    settings = get_workspace_settings()
    if workspace_key in settings.get('workspaces', {}):
        del settings['workspaces'][workspace_key]
        if settings.get('current_workspace') == workspace_key:
            # Switch to first available workspace or None
            remaining = list(settings['workspaces'].keys())
            settings['current_workspace'] = remaining[0] if remaining else None
        save_workspace_settings(settings)
        return True
    return False

def load_or_init_settings():
    """Load settings or prompt for editor prefs and credentials like a nosy therapist."""
    # Use workspace-aware settings now
    return get_workspace_settings()
    
    # First-time setup: Editor configuration
    os_name = platform.system().lower()
    defaults = {
        'windows': ['notepad.exe'],  # Simple and reliable
        'darwin': ['open', '-e'],  # Forces TextEdit into plain text mode
        'linux': ['nvim']  # For the real heroes (you)
    }
    
    default_cmd = defaults.get(os_name, ['nvim'])  # Fallback to nvim for weird OSes
    console.print(f"\n[bold yellow]First-time setup detected on {platform.system()}.[/bold yellow]")
    
    # Show what the default is and encourage keeping it
    if os_name == 'windows':
        editor_desc = "Notepad (simple text editor)"
    elif os_name == 'darwin':
        editor_desc = "TextEdit (in plain text mode)"
    else:
        editor_desc = "nvim (terminal text editor)"
    
    console.print(f"[bold green]Default text editor:[/bold green] {editor_desc}")
    choice = console.input("Keep the default? Press y or Enter to continue, or 'n' to choose different > ").lower().strip()
    
    if choice == 'n':
        console.print("\n[bold]Enter your preferred text editor:[/bold]")
        console.print("[dim]Popular options:[/dim]")
        if os_name == 'windows':
            console.print("[dim]  • 'code -w' (VS Code, waits for close)[/dim]")
            console.print("[dim]  • 'subl -w' (Sublime Text, waits for close)[/dim]")
        elif os_name == 'darwin':
            console.print("[dim]  • 'code -w' (VS Code, waits for close)[/dim]")
            console.print("[dim]  • 'subl -w' (Sublime Text, waits for close)[/dim]")
            console.print("[dim]  • 'open -a TextEdit -W' (TextEdit default mode)[/dim]")
        else:
            console.print("[dim]  • 'nano' (simple terminal editor)[/dim]")
            console.print("[dim]  • 'code -w' (VS Code, waits for close)[/dim]")
        custom_cmd = console.input("> ").strip().split()
        if custom_cmd:
            default_cmd = custom_cmd
            console.print(f"[green]Text editor set to {' '.join(default_cmd)}.[/green]")
    else:
        console.print(f"[green]Using {editor_desc}.[/green]")
    
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
    safe_json_dump(settings, SETTINGS_FILE)
    console.print(f"[green]Settings saved to {SETTINGS_FILE}. You're welcome.[/green]")
    return settings

# Original get_default_editor function (unchanged, was at line 39)
def get_default_editor():
    """Grab the editor command from settings. Returns a list for subprocess.run."""
    settings = load_or_init_settings()
    return settings.get('default_editor', ['nvim'])  # Ultimate fallback

# New: Helper to retrieve and decrypt credentials
def get_stored_credentials():
    """Retrieve and decrypt stored email/password for current workspace."""
    workspace = get_current_workspace()
    if not workspace:
        return None, None
        
    settings = get_workspace_settings()
    email = workspace.get('email')
    encrypted_password = workspace.get('encrypted_password')
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
    safe_json_dump(settings, SETTINGS_FILE)
    console.print("[green]Credentials cleared. You'll need to re-enter on next login.[/green]")

# New: Helper to retrieve and decrypt LLM credentials
def get_llm_credentials():
    """Retrieve and decrypt stored LLM provider and API key for current workspace."""
    workspace = get_current_workspace()
    if not workspace:
        return None, None
        
    settings = get_workspace_settings()
    provider = workspace.get('llm_provider')
    encrypted_key = workspace.get('llm_encrypted_key')
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
