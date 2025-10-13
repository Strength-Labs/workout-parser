#!/usr/bin/env python3
"""
Workspace Management Module for Turnkey Coach Tools

Handles workspace selection, creation, and switching at startup.
Each workspace represents a separate business/company environment.
"""

import os
import getpass
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from settings import (
    get_workspace_settings, save_workspace_settings, 
    create_workspace, switch_workspace, list_workspaces, 
    delete_workspace, get_current_workspace
)
from api_client import get_user_profile, sanitize_workspace_name
from directory_migration import get_workspace_base_dir, migrate_to_workspace_directory

console = Console()

def format_last_login(last_login_str):
    """Format last login timestamp for display."""
    if not last_login_str:
        return "Never"
    
    try:
        last_login = datetime.fromisoformat(last_login_str)
        now = datetime.now()
        diff = now - last_login
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes} min ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return last_login.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Unknown"

def display_workspace_table(workspaces, current_workspace_key):
    """Display available workspaces in a nice table."""
    if not workspaces:
        console.print("[yellow]No workspaces configured yet.[/yellow]")
        return
    
    table = Table(title="Available Workspaces", border_style="green")
    table.add_column("Key", style="bold", width=8)
    table.add_column("Workspace", style="cyan", min_width=20)
    table.add_column("Email", style="dim", min_width=25)
    table.add_column("Company", style="blue", min_width=15)
    table.add_column("AI Provider", style="magenta", width=12)
    table.add_column("Last Login", style="dim", width=15)
    table.add_column("Status", width=10)
    
    for workspace in workspaces:
        key = workspace['key']
        name = workspace['name'] or key
        email = workspace['email'] or "Not set"
        company = workspace['company_name'] or "Unknown"
        llm_provider = workspace['llm_provider'] or "Not set"
        last_login = format_last_login(workspace['last_login'])
        
        # Current workspace indicator
        status = "[bold green]CURRENT[/bold green]" if key == current_workspace_key else ""
        
        table.add_row(key, name, email, company, llm_provider, last_login, status)
    
    console.print(table)

def setup_new_workspace():
    """Interactive setup for a new workspace."""
    console.print("\n[bold]Create New Workspace[/bold]")
    console.print("[dim]Each workspace represents a separate business/company environment.[/dim]\n")
    
    # Get workspace name
    workspace_name = console.input("Workspace name (e.g., 'Barbell Logic', 'Soulsteading'): ").strip()
    if not workspace_name:
        console.print("[red]Workspace name cannot be empty.[/red]")
        return False
    
    # Generate workspace key
    workspace_key = sanitize_workspace_name(workspace_name)
    
    # Check if key already exists
    workspaces = list_workspaces()
    if any(w['key'] == workspace_key for w in workspaces):
        console.print(f"[red]Workspace '{workspace_key}' already exists.[/red]")
        return False
    
    # Get credentials
    console.print(f"\n[bold]Credentials for '{workspace_name}' workspace:[/bold]")
    email = console.input("Email: ").strip()
    password = getpass.getpass("Password: ")
    
    if not email or not password:
        console.print("[red]Email and password are required.[/red]")
        return False
    
    # Try to get company name from API
    console.print("\n[dim]Detecting company information...[/dim]")
    try:
        # Test login to get company info
        from api_client import get_access_token, get_user_profile
        
        # Temporarily create a basic workspace to test login
        temp_key = sanitize_workspace_name(workspace_name)
        create_workspace(
            workspace_key=temp_key,
            name=workspace_name,
            email=email,
            password=password
        )
        switch_workspace(temp_key)
        
        # Now try to get company info
        token, user_id = get_access_token()
        if token and user_id:
            profile = get_user_profile(token, user_id)
            detected_company = profile.get('company_name')
            
            if detected_company:
                console.print(f"[green]✅ Detected company: {detected_company}[/green]")
                company_name = detected_company
            else:
                console.print("[yellow]Could not detect company from API[/yellow]")
                company_name = console.input("Company name (for directory naming): ").strip() or workspace_name
        else:
            console.print("[yellow]Could not authenticate to detect company[/yellow]")
            company_name = console.input("Company name (for directory naming): ").strip() or workspace_name
            
    except Exception as e:
        console.print(f"[red]Error detecting company: {e}[/red]")
        company_name = console.input("Company name (for directory naming): ").strip() or workspace_name
    
    # Get AI provider preferences
    console.print(f"\n[bold]AI Settings for '{workspace_name}' (optional):[/bold]")
    console.print("1. OpenAI (ChatGPT)")
    console.print("2. xAI (Grok)")
    console.print("3. Skip AI setup")
    
    llm_provider = None
    llm_api_key = None
    
    ai_choice = console.input("Choose AI provider (1/2/3): ").strip()
    if ai_choice == "1":
        llm_provider = "openai"
        llm_api_key = getpass.getpass("OpenAI API Key: ")
    elif ai_choice == "2":
        llm_provider = "xai"
        llm_api_key = getpass.getpass("xAI API Key: ")
    
    # Update workspace with company info and AI settings
    try:
        # We already created a temp workspace above, now update it with full info
        settings = get_workspace_settings()
        workspace_key = sanitize_workspace_name(workspace_name)
        
        if workspace_key in settings['workspaces']:
            # Update the existing workspace with company name and AI settings
            workspace_data = settings['workspaces'][workspace_key]
            workspace_data['company_name'] = company_name
            workspace_data['llm_provider'] = llm_provider
            
            if llm_api_key:
                # Encrypt the API key
                key = base64.urlsafe_b64decode(settings['encryption_key'].encode('utf-8'))
                fernet = Fernet(key)
                workspace_data['llm_encrypted_key'] = fernet.encrypt(llm_api_key.encode()).decode('utf-8')
            
            save_workspace_settings(settings)
            console.print(f"[green]✅ Workspace '{workspace_name}' created successfully![/green]")
            return workspace_key
        else:
            # Fallback: create from scratch if temp workspace wasn't created
            create_workspace(
                workspace_key=workspace_key,
                name=workspace_name,
                email=email,
                password=password,
                company_name=company_name,
                llm_provider=llm_provider,
                llm_api_key=llm_api_key
            )
            console.print(f"[green]✅ Workspace '{workspace_name}' created successfully![/green]")
            return workspace_key
            
    except Exception as e:
        console.print(f"[red]Failed to create workspace: {e}[/red]")
        return False

def auto_migrate_for_existing_users():
    """Automatically migrate existing Barbell Logic users to workspace structure."""
    from directory_migration import needs_workspace_migration, migrate_to_workspace_directory
    
    # Check if this looks like an existing Barbell Logic user
    settings = get_workspace_settings()
    has_workspaces = bool(settings.get('workspaces'))
    needs_migration = needs_workspace_migration()
    
    if not has_workspaces and needs_migration:
        console.print("[yellow]🔄 Detected existing Turnkey Coach installation![/yellow]")
        console.print("[dim]Upgrading to v1.5.0 workspace structure...[/dim]")
        
        # Create default Barbell Logic workspace from old settings
        old_settings = settings  # These are the migrated old settings
        
        # Create Barbell Logic workspace if we have credentials
        if 'workspaces' in old_settings and 'default' in old_settings['workspaces']:
            # Rename 'default' workspace to 'barbell-logic'
            default_workspace = old_settings['workspaces']['default']
            default_workspace['name'] = 'Barbell Logic'
            default_workspace['company_name'] = 'Barbell Logic'
            
            # Move it to barbell-logic key
            old_settings['workspaces']['barbell-logic'] = default_workspace
            del old_settings['workspaces']['default']
            old_settings['current_workspace'] = 'barbell-logic'
            
            save_workspace_settings(old_settings)
            console.print("[green]✅ Created Barbell Logic workspace from existing settings[/green]")
        
        # Migrate the directories
        console.print("[blue]Migrating your client data...[/blue]")
        if migrate_to_workspace_directory('barbell-logic', force=True):
            console.print("[bold green]🎉 Migration successful! Your data is now organized in workspaces.[/bold green]")
            console.print("[dim]Press Enter to continue...[/dim]")
            input()
            return 'barbell-logic'
        else:
            console.print("[red]Migration failed. You may need to manually organize your directories.[/red]")
            console.input("Press Enter to continue...")
    
    return None

def workspace_selector():
    """
    Main workspace selection interface.
    Returns the selected workspace key or None to exit.
    Automatically logs into single workspace for better UX.
    """
    # Check for automatic migration first
    auto_migrated = auto_migrate_for_existing_users()
    if auto_migrated:
        return auto_migrated
    
    settings = get_workspace_settings()
    current_workspace_key = settings.get('current_workspace')
    workspaces = list_workspaces()
    
    # AUTO-LOGIN: If user only has one workspace, log them in directly
    if len(workspaces) == 1:
        workspace = workspaces[0]
        workspace_key = workspace['key']
        
        # Show brief message about auto-login
        console.clear()
        console.print(Panel("[bold blue]Turnkey Coach Tools[/bold blue]", expand=False))
        console.print(f"[dim]🔄 Logging into {workspace['name']}...[/dim]")
        
        if switch_workspace(workspace_key):
            console.print(f"[green]✅ Welcome to {workspace['name']}![/green]")
            return workspace_key
        else:
            console.print(f"[red]❌ Failed to access {workspace['name']}[/red]")
            console.input("Press Enter to continue to workspace selector...")
    
    # MULTI-WORKSPACE: Show selector interface for users with multiple workspaces
    while True:
        console.clear()
        console.print(Panel("[bold blue]Turnkey Coach Tools - Workspace Selector[/bold blue]", expand=False))
        
        if workspaces:
            console.print()
            display_workspace_table(workspaces, current_workspace_key)
            console.print()
        
        console.print("[bold]Options:[/bold]")
        
        # Show quick-select options for existing workspaces
        if workspaces:
            for i, workspace in enumerate(workspaces[:9], 1):  # Show first 9 workspaces with number keys
                key = workspace['key']
                name = workspace['name']
                console.print(f"  [bold]{i}[/bold] - Switch to {name}")
        
        console.print("  [bold]n[/bold] - Create new workspace")
        if workspaces:
            console.print("  [bold]d[/bold] - Delete workspace")
        console.print("  [bold]q[/bold] - Quit")
        
        choice = console.input("\n> ").strip().lower()
        
        if choice == 'q':
            return None
        elif choice == 'n':
            new_workspace_key = setup_new_workspace()
            if new_workspace_key:
                switch_workspace(new_workspace_key)
                return new_workspace_key
            console.input("Press Enter to continue...")
        elif choice == 'd' and workspaces:
            console.print("\n[bold]Delete Workspace[/bold]")
            console.print("Available workspaces:")
            for i, workspace in enumerate(workspaces, 1):
                console.print(f"  {i} - {workspace['name']} ({workspace['key']})")
            
            delete_choice = console.input("\nEnter number or workspace key to delete: ").strip()
            
            # Handle both number and key input
            workspace_to_delete = None
            if delete_choice.isdigit() and 1 <= int(delete_choice) <= len(workspaces):
                # User entered a number
                workspace_index = int(delete_choice) - 1
                workspace_to_delete = workspaces[workspace_index]
            elif delete_choice in [w['key'] for w in workspaces]:
                # User entered a workspace key
                workspace_to_delete = next(w for w in workspaces if w['key'] == delete_choice)
            
            if workspace_to_delete:
                workspace_key = workspace_to_delete['key']
                workspace_name = workspace_to_delete['name']
                confirm = console.input(f"Are you sure you want to delete '{workspace_name}' ({workspace_key})? (y/N): ").strip().lower()
                if confirm == 'y':
                    if delete_workspace(workspace_key):
                        console.print(f"[green]Workspace '{workspace_name}' deleted.[/green]")
                        # Update current workspace if it was deleted
                        settings = get_workspace_settings()
                        current_workspace_key = settings.get('current_workspace')
                    else:
                        console.print(f"[red]Failed to delete workspace '{workspace_name}'.[/red]")
                else:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
            else:
                console.print("[red]Invalid selection.[/red]")
            console.input("Press Enter to continue...")
        elif choice.isdigit() and 1 <= int(choice) <= len(workspaces):
            # Handle numeric selection
            workspace_index = int(choice) - 1
            workspace = workspaces[workspace_index]
            target_key = workspace['key']
            
            if switch_workspace(target_key):
                console.print(f"[green]✅ Switched to workspace '{workspace['name']}'[/green]")
                return target_key
            else:
                console.print(f"[red]Failed to switch to workspace '{workspace['name']}'[/red]")
                console.input("Press Enter to continue...")
        else:
            console.print(f"[red]Invalid choice: {choice}[/red]")
            console.input("Press Enter to continue...")

def ensure_workspace_directories():
    """Ensure the current workspace directories exist."""
    try:
        from directory_migration import get_new_paths
        paths = get_new_paths()
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        console.print(f"[red]Error creating workspace directories: {e}[/red]")
        return False

def get_workspace_info():
    """Get current workspace information for display."""
    workspace = get_current_workspace()
    if not workspace:
        return "No workspace selected"
    
    name = workspace.get('name', 'Unknown')
    company = workspace.get('company_name', 'Unknown company')
    llm = workspace.get('llm_provider', 'No AI provider')
    
    return f"{name} ({company}) - AI: {llm}"

def quick_workspace_switcher():
    """Quick workspace switcher for multi-workspace users."""
    workspaces = list_workspaces()
    current_workspace_key = get_workspace_settings().get('current_workspace')
    
    if len(workspaces) <= 1:
        console.print("[yellow]No other workspaces available.[/yellow]")
        return None
    
    console.print("\n[bold]Switch Workspace[/bold]")
    console.print("Available workspaces:")
    
    available_workspaces = []
    for i, workspace in enumerate(workspaces, 1):
        status = "(current)" if workspace['key'] == current_workspace_key else ""
        console.print(f"  {i} - {workspace['name']} {status}")
        if workspace['key'] != current_workspace_key:  # Don't include current workspace
            available_workspaces.append(workspace)
    
    if not available_workspaces:
        console.print("[yellow]No other workspaces to switch to.[/yellow]")
        return None
    
    choice = console.input("\nEnter number to switch to (or Enter to cancel): ").strip()
    
    if not choice:
        return None
    
    try:
        # Handle numeric selection from all workspaces
        if choice.isdigit():
            workspace_index = int(choice) - 1
            if 0 <= workspace_index < len(workspaces):
                target_workspace = workspaces[workspace_index]
                if target_workspace['key'] == current_workspace_key:
                    console.print("[yellow]That's your current workspace.[/yellow]")
                    return None
                
                if switch_workspace(target_workspace['key']):
                    return target_workspace['name']
                else:
                    console.print(f"[red]Failed to switch to {target_workspace['name']}[/red]")
                    return None
        
        console.print("[red]Invalid selection.[/red]")
        return None
        
    except (ValueError, IndexError):
        console.print("[red]Invalid input.[/red]")
        return None

def logout_current_workspace():
    """Logout from current workspace by clearing auth cache."""
    try:
        from api_client import get_token_cache_file
        token_cache_file = get_token_cache_file()
        if os.path.exists(token_cache_file):
            os.remove(token_cache_file)
        console.print("[green]Logged out successfully.[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Error during logout: {e}[/red]")
        return False
