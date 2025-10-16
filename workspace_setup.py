#!/usr/bin/env python3
"""
Simple workspace setup that asks user for their company/workspace name
"""

import getpass
from rich.console import Console
from settings import create_workspace, switch_workspace, list_workspaces, get_workspace_settings
from api_client import get_access_token, sanitize_workspace_name

console = Console()

def setup_new_workspace():
    """Set up a new workspace by prompting user for details"""
    
    console.print("\n[bold yellow]🚀 Setting up a new TurnKey Coach workspace[/bold yellow]\n")
    
    # Get credentials
    console.print("[bold]Enter your TurnKey Coach credentials:[/bold]")
    email = console.input("📧 Email: ").strip()
    if not email:
        console.print("[red]❌ Email is required[/red]")
        return False
    
    password = getpass.getpass("🔒 Password: ")
    if not password:
        console.print("[red]❌ Password is required[/red]")
        return False
    
    # Test authentication
    console.print("\n[dim]Testing authentication...[/dim]")
    try:
        # Clear any cached token first to force fresh login
        import os
        from api_client import get_token_cache_file
        token_cache = get_token_cache_file()
        if os.path.exists(token_cache):
            os.remove(token_cache)
        
        # Temporarily store credentials for authentication test
        from settings import create_workspace as temp_create
        temp_create('temp-test', 'Temp', email, password)
        from settings import switch_workspace
        switch_workspace('temp-test')
        
        # Test login
        token, user_id = get_access_token()
        if not token or not user_id:
            console.print("[red]❌ Authentication failed. Please check your credentials.[/red]")
            return False
            
        console.print(f"[green]✅ Authentication successful! User ID: {user_id}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Authentication failed: {e}[/red]")
        return False
    
    # Get workspace/company name
    console.print("\n[bold]What would you like to call this workspace?[/bold]")
    console.print("[dim]Examples: 'Soulsteading', 'McGuffinStrength', 'Barbell Logic', 'My Gym'[/dim]")
    
    while True:
        workspace_name = console.input("🏢 Workspace name: ").strip()
        if workspace_name:
            break
        console.print("[yellow]Please enter a name for your workspace[/yellow]")
    
    # Generate workspace key
    workspace_key = sanitize_workspace_name(workspace_name)
    
    # Check if workspace already exists
    existing_workspaces = list_workspaces()
    if any(ws['key'] == workspace_key for ws in existing_workspaces):
        console.print(f"[yellow]⚠️ Workspace '{workspace_key}' already exists[/yellow]")
        return False
    
    # Ask for LLM provider (optional)
    console.print(f"\n[bold]Optional: AI Assistant Setup[/bold]")
    console.print("[dim]You can configure an AI provider for workout programming help[/dim]")
    
    llm_choice = console.input("Configure AI now? (y/N): ").lower().strip()
    llm_provider = None
    llm_api_key = None
    
    if llm_choice in ['y', 'yes']:
        console.print("\n[bold]Choose AI provider:[/bold]")
        console.print("1. OpenAI (GPT-4)")
        console.print("2. xAI (Grok)")
        console.print("3. Skip for now")
        
        provider_choice = console.input("Choice (1-3): ").strip()
        if provider_choice == '1':
            llm_provider = 'openai'
            llm_api_key = getpass.getpass("OpenAI API Key: ").strip()
        elif provider_choice == '2':
            llm_provider = 'xai'
            llm_api_key = getpass.getpass("xAI API Key: ").strip()
    
    # Create the workspace
    try:
        create_workspace(
            workspace_key=workspace_key,
            name=workspace_name,
            email=email,
            password=password,
            company_name=workspace_name,  # Use the workspace name as company name
            llm_provider=llm_provider,
            llm_api_key=llm_api_key
        )
        
        # Switch to the new workspace
        switch_workspace(workspace_key)
        
        console.print(f"\n[green]✅ Workspace '{workspace_name}' created successfully![/green]")
        console.print(f"[dim]📁 Directory: ~/Turnkey-{workspace_key}[/dim]")
        
        # Clean up temp workspace
        settings = get_workspace_settings()
        if 'temp-test' in settings.get('workspaces', {}):
            del settings['workspaces']['temp-test']
            from settings import save_workspace_settings
            save_workspace_settings(settings)
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create workspace: {e}[/red]")
        return False

def list_existing_workspaces():
    """Show existing workspaces"""
    
    workspaces = list_workspaces()
    if not workspaces:
        console.print("[yellow]No workspaces found.[/yellow]")
        return
    
    console.print(f"\n[bold]📋 Existing Workspaces ({len(workspaces)}):[/bold]")
    for i, ws in enumerate(workspaces, 1):
        status = "✅ Current" if ws.get('last_login') else "💤 Inactive"
        console.print(f"  {i}. [bold]{ws['name']}[/bold] ({ws['key']}) - {ws['email']} - {status}")

def main():
    """Main workspace setup interface"""
    
    console.print("[bold blue]🔧 TurnKey Coach Workspace Manager[/bold blue]")
    
    # Show existing workspaces
    list_existing_workspaces()
    
    console.print("\n[bold]What would you like to do?[/bold]")
    console.print("1. Create new workspace")
    console.print("2. Switch workspace") 
    console.print("3. Exit")
    
    choice = console.input("\nChoice (1-3): ").strip()
    
    if choice == '1':
        setup_new_workspace()
    elif choice == '2':
        workspaces = list_workspaces()
        if workspaces:
            console.print("\n[bold]Select workspace:[/bold]")
            for i, ws in enumerate(workspaces, 1):
                console.print(f"  {i}. {ws['name']} ({ws['email']})")
            
            try:
                selection = int(console.input("Choice: ")) - 1
                if 0 <= selection < len(workspaces):
                    workspace_key = workspaces[selection]['key']
                    if switch_workspace(workspace_key):
                        console.print(f"[green]✅ Switched to {workspaces[selection]['name']}[/green]")
                    else:
                        console.print("[red]❌ Failed to switch workspace[/red]")
                else:
                    console.print("[red]❌ Invalid selection[/red]")
            except (ValueError, IndexError):
                console.print("[red]❌ Invalid selection[/red]")
        else:
            console.print("[yellow]No workspaces available to switch to[/yellow]")
    elif choice == '3':
        console.print("👋 Goodbye!")
    else:
        console.print("[red]❌ Invalid choice[/red]")

if __name__ == "__main__":
    main()